"""Application service for provenance-preserving evidence extraction."""

import logging
from datetime import UTC, datetime
from pathlib import PurePath
from typing import cast
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.processing import (
    ArtifactListResponse,
    ArtifactResponse,
    ProcessingJobResponse,
)
from backend.app.application.processors.base import ProcessorContext
from backend.app.application.processors.inspection import FileInspectionProcessor
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
from backend.app.domain.processing import (
    ArtifactType,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.extraction.audio.extractor import AudioExtractor
from backend.app.extraction.base import EvidenceExtractor
from backend.app.extraction.document.extractor import DocumentExtractor
from backend.app.extraction.exceptions import ExtractionError
from backend.app.extraction.image.extractor import ImageExtractor
from backend.app.extraction.models import (
    ExtractionContext,
    ExtractionItem,
    ExtractionResult,
    ExtractionStatus,
    ExtractionType,
)
from backend.app.extraction.ocr import TesseractOCRProvider
from backend.app.extraction.schemas import (
    BoundingBoxResponse,
    ExtractionListResponse,
    ExtractionResponse,
    NormalizedBoundingBoxResponse,
)
from backend.app.extraction.video.extractor import VideoExtractor
from backend.app.infrastructure.database.repositories.custody import CustodyRepository
from backend.app.infrastructure.database.repositories.extraction import (
    ExtractionRepository,
)
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
    ProcessingJobRepository,
)
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)
EXTRACTION_VERSION = "1.0"


class ExtractionService:
    """Queue and execute replaceable extraction adapters."""

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
        self.job_repository = ProcessingJobRepository(session)
        self.repository = ExtractionRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.custody_repository = CustodyRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )
        self.extractors: tuple[EvidenceExtractor, ...] = (
            ImageExtractor(),
            DocumentExtractor(),
            VideoExtractor(),
            AudioExtractor(),
        )
        self.ocr_provider = TesseractOCRProvider(
            settings.ocr_enabled,
            settings.ocr_command,
        )

    async def create_job(self, evidence_id: UUID) -> ProcessingJobResponse:
        """Create a repeatable extraction job after integrity verification."""

        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if evidence.status != EvidenceStatus.READY_FOR_ANALYSIS:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process the evidence before starting extraction.",
            )
        context = self._context(evidence)
        await FileInspectionProcessor(
            self.storage,
            self.hash_service,
        ).process(
            ProcessorContext(
                evidence=evidence,
                extension=PurePath(evidence.original_filename)
                .suffix.lower()
                .lstrip("."),
            )
        )
        latest = await self.job_repository.latest_for_evidence(
            evidence_id,
            ProcessingJobType.EXTRACTION,
        )
        if (
            latest is not None
            and latest.status == ProcessingJobStatus.SUCCEEDED
            and latest.metadata_json.get("source_sha256") == evidence.sha256_hash
            and latest.metadata_json.get("extractor_version") == EXTRACTION_VERSION
        ):
            return self._job_response(latest)
        active = await self.job_repository.get_active(
            evidence_id,
            ProcessingJobType.EXTRACTION,
        )
        if active is not None:
            raise ConflictError("An active extraction job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.EXTRACTION,
            status=ProcessingJobStatus.QUEUED,
            priority=0,
            attempt=0,
            max_attempts=1,
            metadata_json={
                "runner": "local",
                "source_sha256": evidence.sha256_hash,
                "extractor_version": EXTRACTION_VERSION,
                "source_type": context.mime_type,
            },
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("An active extraction job already exists.") from exc
        logger.info(
            "Extraction job created",
            extra={"job_id": str(job.id), "evidence_id": str(evidence_id)},
        )
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        """Execute exactly one queued extraction job."""

        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.EXTRACTION
        ):
            return
        evidence = await self.session.get(Evidence, job.evidence_id)
        if evidence is None:
            await self._fail_job(
                job_id,
                "EVIDENCE_NOT_FOUND",
                "The evidence record is no longer available.",
            )
            return
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = datetime.now(UTC)
        created_artifacts: list[Artifact] = []
        try:
            await self.session.commit()
            await self._record_event(
                evidence.id,
                CustodyEventType.EXTRACTION_STARTED,
                "Evidence extraction started.",
                evidence.sha256_hash,
            )
            context = self._context(evidence)
            await FileInspectionProcessor(
                self.storage,
                self.hash_service,
            ).process(
                ProcessorContext(
                    evidence=evidence,
                    extension=PurePath(evidence.original_filename)
                    .suffix.lower()
                    .lstrip("."),
                )
            )
            extractor = next(
                (
                    candidate
                    for candidate in self.extractors
                    if candidate.can_extract(context)
                ),
                None,
            )
            result = (
                await extractor.extract(context)
                if extractor is not None
                else ExtractionResult(
                    status=ExtractionStatus.UNAVAILABLE,
                    metadata={"extraction_status": "UNAVAILABLE"},
                    error_code="EXTRACTOR_UNAVAILABLE",
                    error_message_safe="No safe extractor is available for this file.",
                )
            )
            async with self.session.begin():
                for payload in result.artifacts:
                    artifact = await self.artifact_service.create(evidence, payload)
                    created_artifacts.append(artifact)
                    await self._record_event_in_transaction(
                        evidence.id,
                        CustodyEventType.EXTRACTION_ARTIFACT_CREATED,
                        f"{payload.artifact_type.value} extraction artifact created.",
                        artifact.sha256_hash,
                        {"artifact_id": str(artifact.id)},
                    )
                for item in result.items:
                    await self.repository.add(self._record(item))
                evidence.metadata_json = {
                    **evidence.metadata_json,
                    "extraction": {
                        "status": result.status.value,
                        "method_version": EXTRACTION_VERSION,
                        **result.metadata,
                    },
                }
                job.status = ProcessingJobStatus.SUCCEEDED
                job.completed_at = datetime.now(UTC)
                job.metadata_json = {
                    **job.metadata_json,
                    "extraction_status": result.status.value,
                    "items_created": len(result.items),
                    "artifacts_created": len(created_artifacts),
                    "error_code": result.error_code,
                }
                await self._record_event_in_transaction(
                    evidence.id,
                    CustodyEventType.EXTRACTION_COMPLETED,
                    "Evidence extraction completed.",
                    evidence.sha256_hash,
                    {
                        "status": result.status.value,
                        "items_created": len(result.items),
                    },
                )
            logger.info(
                "Extraction job completed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, ExtractionError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "EXTRACTION_FAILED"
                safe_message = "The evidence extraction pipeline failed."
            await self._fail_job(job_id, error_code, safe_message)
            logger.exception(
                "Extraction job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_extractions(
        self,
        evidence_id: UUID,
        *,
        extraction_type: ExtractionType | tuple[ExtractionType, ...] | None,
        limit: int,
        offset: int,
    ) -> ExtractionListResponse:
        """Return records and the latest extraction capability status."""

        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        records, total = await self.repository.list_for_evidence(
            evidence_id,
            extraction_type=extraction_type,
            limit=limit,
            offset=offset,
        )
        job = await self.job_repository.latest_for_evidence(
            evidence_id,
            ProcessingJobType.EXTRACTION,
        )
        status = ExtractionStatus.UNAVAILABLE
        error_code: str | None = "EXTRACTION_NOT_RUN"
        if job is not None:
            if job.status in {
                ProcessingJobStatus.QUEUED,
                ProcessingJobStatus.RUNNING,
            }:
                error_code = "EXTRACTION_IN_PROGRESS"
            else:
                raw_status = job.metadata_json.get("extraction_status")
                try:
                    status = ExtractionStatus(str(raw_status))
                except (TypeError, ValueError):
                    status = (
                        ExtractionStatus.FAILED
                        if job.status == ProcessingJobStatus.FAILED
                        else ExtractionStatus.UNAVAILABLE
                    )
                raw_error_code = job.metadata_json.get("error_code")
                error_code = job.error_code or (
                    str(raw_error_code) if raw_error_code else None
                )
        return ExtractionListResponse(
            status=status,
            error_code=error_code,
            items=[self._response(record) for record in records],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_extraction(
        self,
        evidence_id: UUID,
        extraction_id: UUID,
    ) -> ExtractionResponse:
        """Return one extraction record within its evidence scope."""

        record = await self.repository.get(extraction_id)
        if record is None or record.evidence_id != evidence_id:
            raise ResourceNotFoundError("The requested extraction was not found.")
        return self._response(record)

    async def list_regions(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ExtractionListResponse:
        """Return only localized region records."""

        region_types = (
            ExtractionType.IMAGE_REGION,
            ExtractionType.FACE_REGION,
            ExtractionType.SIGNATURE_REGION,
            ExtractionType.LOGO_REGION,
            ExtractionType.STAMP_REGION,
            ExtractionType.QR_CODE,
            ExtractionType.BARCODE,
        )
        return await self.list_extractions(
            evidence_id,
            extraction_type=region_types,
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
        """Return only artifacts produced by extraction."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        extraction_types = (
            ArtifactType.OCR_RESULT,
            ArtifactType.DOCUMENT_STRUCTURE,
            ArtifactType.IMAGE_REGIONS,
            ArtifactType.VIDEO_FRAME_INDEX,
            ArtifactType.AUDIO_STREAM_INFO,
            ArtifactType.VIDEO_FRAME,
            ArtifactType.AUDIO_EXTRACT,
            ArtifactType.TEXT_RESULT,
        )
        artifacts, total = await self.artifact_repository.list_for_evidence(
            evidence_id,
            artifact_types=extraction_types,
            limit=limit,
            offset=offset,
        )
        return ArtifactListResponse(
            items=[self._artifact_response(item) for item in artifacts],
            total=total,
            limit=limit,
            offset=offset,
        )

    def _context(self, evidence: Evidence) -> ExtractionContext:
        return ExtractionContext(
            evidence_id=evidence.id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            storage_key=evidence.storage_key,
            storage=self.storage,
            settings=self.settings,
            ocr_provider=self.ocr_provider,
        )

    async def _fail_job(
        self,
        job_id: UUID,
        error_code: str,
        safe_message: str,
    ) -> None:
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
        await self._record_event_in_transaction(
            evidence.id,
            CustodyEventType.EXTRACTION_FAILED,
            "Evidence extraction failed; original evidence preserved.",
            evidence.sha256_hash,
            {"error_code": error_code},
        )
        await self.session.commit()

    async def _record_event(
        self,
        evidence_id: UUID,
        event_type: CustodyEventType,
        description: str,
        sha256_hash: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        await self.session.begin()
        await self._record_event_in_transaction(
            evidence_id,
            event_type,
            description,
            sha256_hash,
            metadata,
        )
        await self.session.commit()

    async def _record_event_in_transaction(
        self,
        evidence_id: UUID,
        event_type: CustodyEventType,
        description: str,
        sha256_hash: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
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
    def _record(item: ExtractionItem) -> ExtractionRecord:
        """Map an extraction contract into searchable persistence fields."""

        return ExtractionRecord(
            id=uuid4(),
            evidence_id=item.evidence_id,
            artifact_id=item.artifact_id,
            extraction_type=item.extraction_type,
            source_type=item.source_type,
            source_identifier=item.source_identifier,
            page_number=item.page_number,
            frame_number=item.frame_number,
            timestamp_ms=item.timestamp_ms,
            content=item.content,
            confidence=item.confidence,
            bbox_x=item.bbox.x if item.bbox else None,
            bbox_y=item.bbox.y if item.bbox else None,
            bbox_width=item.bbox.width if item.bbox else None,
            bbox_height=item.bbox.height if item.bbox else None,
            normalized_x=item.normalized_bbox.x if item.normalized_bbox else None,
            normalized_y=item.normalized_bbox.y if item.normalized_bbox else None,
            normalized_width=item.normalized_bbox.width
            if item.normalized_bbox
            else None,
            normalized_height=item.normalized_bbox.height
            if item.normalized_bbox
            else None,
            method=item.method,
            version=item.version,
            metadata_json=item.metadata,
        )

    @staticmethod
    def _job_response(job: ProcessingJob) -> ProcessingJobResponse:
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
    def _response(record: ExtractionRecord) -> ExtractionResponse:
        def box(
            x: float | None,
            y: float | None,
            width: float | None,
            height: float | None,
            *,
            normalized: bool = False,
        ) -> BoundingBoxResponse | NormalizedBoundingBoxResponse | None:
            if (
                x is None
                or y is None
                or width is None
                or height is None
            ):
                return None
            box_type = (
                NormalizedBoundingBoxResponse
                if normalized
                else BoundingBoxResponse
            )
            return box_type(
                x=x,
                y=y,
                width=width,
                height=height,
            )

        return ExtractionResponse(
            id=record.id,
            evidence_id=record.evidence_id,
            artifact_id=record.artifact_id,
            extraction_type=record.extraction_type,
            source_type=record.source_type,
            source_identifier=record.source_identifier,
            page_number=record.page_number,
            frame_number=record.frame_number,
            timestamp_ms=record.timestamp_ms,
            content=record.content,
            confidence=record.confidence,
            location=box(
                record.bbox_x,
                record.bbox_y,
                record.bbox_width,
                record.bbox_height,
            ),
            normalized_location=cast(
                NormalizedBoundingBoxResponse | None,
                box(
                    record.normalized_x,
                    record.normalized_y,
                    record.normalized_width,
                    record.normalized_height,
                    normalized=True,
                ),
            ),
            method=record.method,
            version=record.version,
            metadata=record.metadata_json,
            created_at=record.created_at,
        )

    @staticmethod
    def _artifact_response(artifact: Artifact) -> ArtifactResponse:
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
