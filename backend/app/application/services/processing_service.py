"""Asynchronous-ready evidence processing orchestration."""

import logging
from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.processing import (
    ArtifactListResponse,
    ArtifactResponse,
    ProcessingJobListResponse,
    ProcessingJobResponse,
)
from backend.app.application.processors.base import (
    DerivedArtifactPayload,
    EvidenceProcessor,
    ProcessorContext,
)
from backend.app.application.processors.classification import (
    FileClassificationProcessor,
)
from backend.app.application.processors.inspection import FileInspectionProcessor
from backend.app.application.processors.metadata import MetadataProcessor
from backend.app.application.processors.preview import PreviewProcessor
from backend.app.application.services.artifact_service import ArtifactService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    ConflictError,
    ProcessingError,
    ResourceNotFoundError,
)
from backend.app.domain.custody import CustodyActorType, CustodyEventType
from backend.app.domain.evidence import EvidenceStatus
from backend.app.domain.processing import ProcessingJobStatus, ProcessingJobType
from backend.app.infrastructure.database.repositories.custody import (
    CustodyRepository,
)
from backend.app.infrastructure.database.repositories.evidence import (
    EvidenceRepository,
)
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
    ProcessingJobRepository,
)
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """Coordinate jobs and safe processors while preserving original evidence."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.evidence_repository = EvidenceRepository(session)
        self.job_repository = ProcessingJobRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.custody_repository = CustodyRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )
        self.processors: tuple[EvidenceProcessor, ...] = (
            FileInspectionProcessor(storage, hash_service),
            FileClassificationProcessor(settings),
            MetadataProcessor(),
            PreviewProcessor(),
        )

    async def create_job(
        self,
        evidence_id: UUID,
        *,
        job_type: ProcessingJobType = ProcessingJobType.PREPROCESSING,
        priority: int = 0,
    ) -> ProcessingJobResponse:
        """Create one queued job while preventing active duplicates."""

        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if not await self.storage.exists(evidence.storage_key):
            raise ProcessingError(
                "EVIDENCE_FILE_MISSING",
                "The registered evidence file is no longer available.",
            )
        active = await self.job_repository.get_active(evidence_id, job_type)
        if active is not None:
            raise ConflictError("An active processing job already exists.")

        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=job_type,
            status=ProcessingJobStatus.QUEUED,
            priority=priority,
            attempt=0,
            max_attempts=1,
            metadata_json={"runner": "local"},
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("An active processing job already exists.") from exc
        except Exception:
            await self.session.rollback()
            raise

        logger.info(
            "Processing job created",
            extra={
                "job_id": str(job.id),
                "evidence_id": str(evidence_id),
                "job_type": job.job_type.value,
            },
        )
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        """Run the local deterministic pipeline for a queued job."""

        job = await self.job_repository.get(job_id)
        if job is None or job.status != ProcessingJobStatus.QUEUED:
            return
        evidence = await self.session.get(Evidence, job.evidence_id)
        if evidence is None:
            await self._fail_job(
                job_id,
                "EVIDENCE_NOT_FOUND",
                "The evidence record is no longer available.",
            )
            return

        started_at = datetime.now(UTC)
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = started_at
        job.metadata_json = {"runner": "local"}
        created_artifacts: list[Artifact] = []
        try:
            await self.session.commit()
            await self._record_event(
                evidence_id=evidence.id,
                event_type=CustodyEventType.PROCESSING_STARTED,
                description="Evidence processing started.",
                sha256_hash=evidence.sha256_hash,
            )
            logger.info(
                "Processing job started",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

            context = ProcessorContext(
                evidence=evidence,
                extension=PurePath(evidence.original_filename)
                .suffix.lower()
                .lstrip("."),
            )
            artifact_payloads: list[DerivedArtifactPayload] = []
            for processor in self.processors:
                if not processor.can_process(context):
                    continue
                result = await processor.process(context)
                if result.inspection is not None:
                    context.inspection = result.inspection
                if result.classification is not None:
                    context.classification = result.classification
                if result.metadata is not None:
                    context.metadata.update(result.metadata)
                artifact_payloads.extend(result.artifacts)

            async with self.session.begin():
                for payload in artifact_payloads:
                    artifact = await self.artifact_service.create(evidence, payload)
                    created_artifacts.append(artifact)
                    await self._record_event_in_transaction(
                        evidence_id=evidence.id,
                        event_type=CustodyEventType.ARTIFACT_CREATED,
                        description=f"{payload.artifact_type.value} artifact created.",
                        sha256_hash=artifact.sha256_hash,
                        metadata={"artifact_id": str(artifact.id)},
                    )

                evidence.metadata_json = {
                    **evidence.metadata_json,
                    "classification": context.classification.value,
                    "processing": context.metadata,
                }
                evidence.status = EvidenceStatus.READY_FOR_ANALYSIS
                job.status = ProcessingJobStatus.SUCCEEDED
                job.completed_at = datetime.now(UTC)
                job.metadata_json = {
                    "runner": "local",
                    "classification": context.classification.value,
                    "artifacts_created": len(created_artifacts),
                }
                await self._record_event_in_transaction(
                    evidence_id=evidence.id,
                    event_type=CustodyEventType.PROCESSING_COMPLETED,
                    description="Evidence processing completed successfully.",
                    sha256_hash=evidence.sha256_hash,
                    metadata={"artifacts_created": len(created_artifacts)},
                )
            logger.info(
                "Processing job completed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            error_code = (
                exc.code if isinstance(exc, ProcessingError) else "PROCESSOR_FAILED"
            )
            safe_message = (
                exc.message
                if isinstance(exc, ProcessingError)
                else "The evidence processing pipeline failed."
            )
            await self._fail_job(
                job_id,
                error_code,
                safe_message,
            )
            logger.exception(
                "Processing job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def get_job(self, job_id: UUID) -> ProcessingJobResponse:
        """Return a processing job or a safe not-found error."""

        job = await self.job_repository.get(job_id)
        if job is None:
            raise ResourceNotFoundError("The requested processing job was not found.")
        return self._job_response(job)

    async def list_jobs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ProcessingJobListResponse:
        """Return bounded processing history for one evidence item."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        jobs, total = await self.job_repository.list_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return ProcessingJobListResponse(
            items=[self._job_response(job) for job in jobs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_artifacts(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ArtifactListResponse:
        """Return bounded derived-artifact metadata for one evidence item."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        artifacts, total = await self.artifact_repository.list_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return ArtifactListResponse(
            items=[self._artifact_response(artifact) for artifact in artifacts],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def cancel(self, job_id: UUID) -> ProcessingJobResponse:
        """Cancel a queued or running job without deleting evidence."""

        job = await self.job_repository.get(job_id)
        if job is None:
            raise ResourceNotFoundError("The requested processing job was not found.")
        if job.status not in {
            ProcessingJobStatus.QUEUED,
            ProcessingJobStatus.RUNNING,
        }:
            return self._job_response(job)
        job.status = ProcessingJobStatus.CANCELLED
        job.completed_at = datetime.now(UTC)
        await self.session.commit()
        return self._job_response(job)

    async def _fail_job(
        self,
        job_id: UUID,
        error_code: str,
        safe_message: str,
    ) -> None:
        """Persist a safe terminal failure state and custody event."""

        await self.session.rollback()
        job = await self.job_repository.get(job_id)
        if job is None:
            return
        evidence = await self.session.get(Evidence, job.evidence_id)
        if evidence is None:
            return
        job.status = ProcessingJobStatus.FAILED
        job.completed_at = datetime.now(UTC)
        job.error_code = error_code
        job.error_message_safe = safe_message
        evidence.status = EvidenceStatus.FAILED
        await self._record_event_in_transaction(
            evidence_id=evidence.id,
            event_type=CustodyEventType.PROCESSING_FAILED,
            description="Evidence processing failed; original evidence preserved.",
            sha256_hash=evidence.sha256_hash,
            metadata={"error_code": error_code, "severity": "high"},
        )
        await self.session.commit()
        logger.error(
            "Processing job failed safely",
            extra={"job_id": str(job_id), "error_code": error_code},
        )

    async def _record_event(
        self,
        *,
        evidence_id: UUID,
        event_type: CustodyEventType,
        description: str,
        sha256_hash: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        """Append and commit one operational custody event."""

        async with self.session.begin():
            await self._record_event_in_transaction(
                evidence_id=evidence_id,
                event_type=event_type,
                description=description,
                sha256_hash=sha256_hash,
                metadata=metadata,
            )

    async def _record_event_in_transaction(
        self,
        *,
        evidence_id: UUID,
        event_type: CustodyEventType,
        description: str,
        sha256_hash: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        """Append a custody event to the current transaction."""

        await self.custody_repository.add(
            ChainOfCustodyEvent(
                id=uuid4(),
                evidence_id=evidence_id,
                event_type=event_type,
                timestamp=datetime.now(UTC),
                actor_type=CustodyActorType.SYSTEM,
                actor_id=None,
                description=description,
                sha256_hash=sha256_hash,
                metadata_json=metadata or {},
            )
        )

    @staticmethod
    def _job_response(job: ProcessingJob) -> ProcessingJobResponse:
        """Map a job without exposing ORM implementation details."""

        return ProcessingJobResponse(
            id=job.id,
            evidence_id=job.evidence_id,
            job_type=job.job_type,
            status=job.status,
            priority=job.priority,
            attempt=job.attempt,
            max_attempts=job.max_attempts,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            updated_at=job.updated_at,
            error_code=job.error_code,
            error_message=job.error_message_safe,
            metadata=job.metadata_json,
        )

    @staticmethod
    def _artifact_response(artifact: Artifact) -> ArtifactResponse:
        """Map an artifact without exposing its storage key."""

        return ArtifactResponse(
            id=artifact.id,
            evidence_id=artifact.evidence_id,
            artifact_type=artifact.artifact_type,
            mime_type=artifact.mime_type,
            file_size=artifact.file_size,
            sha256_hash=artifact.sha256_hash,
            created_at=artifact.created_at,
            metadata=artifact.metadata_json,
        )
