"""Application service for Siamese signature verification."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.document.signature.config import SignatureAISettings
from backend.app.ai.document.signature.inference import SignatureInferenceEngine
from backend.app.ai.document.signature.schemas import (
    SignatureRegionResponse,
    SignatureVerdict,
    SignatureVerificationListResponse,
    SignatureVerificationResponse,
)
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.application.services.artifact_service import ArtifactService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.comparison.utils import load_bytes_from_storage
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    ConflictError,
    ProcessingError,
    ResourceNotFoundError,
)
from backend.app.domain.evidence import EvidenceStatus
from backend.app.domain.processing import (
    ArtifactType,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.infrastructure.database.repositories.processing import (
    ProcessingJobRepository,
)
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact, ProcessingJob
from backend.app.models.signature_ai import SignatureVerificationRun

logger = logging.getLogger(__name__)

MAX_SIGNATURE_BYTES = 16 * 1024 * 1024


class SignatureVerificationService:
    """Verify questioned signatures against trusted reference signatures."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: SignatureInferenceEngine | None = None,
        signature_settings: SignatureAISettings | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.signature_settings = signature_settings or SignatureAISettings()
        self.engine = engine or SignatureInferenceEngine(
            settings=self.signature_settings
        )
        self.job_repository = ProcessingJobRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )

    async def verify(
        self,
        *,
        reference_evidence_id: UUID | None = None,
        questioned_evidence_id: UUID | None = None,
        reference_bytes: bytes | None = None,
        questioned_bytes: bytes | None = None,
    ) -> SignatureVerificationResponse:
        """Run signature verification from evidence IDs or uploaded bytes."""

        (
            reference_data,
            reference_hash,
            reference_id,
        ) = await self._resolve_signature_input(
            evidence_id=reference_evidence_id,
            raw_bytes=reference_bytes,
            label="reference",
        )
        (
            questioned_data,
            questioned_hash,
            questioned_id,
        ) = await self._resolve_signature_input(
            evidence_id=questioned_evidence_id,
            raw_bytes=questioned_bytes,
            label="questioned",
        )
        artifact_evidence = None
        if questioned_id is not None:
            artifact_evidence = await self.session.get(Evidence, questioned_id)
        return await self._execute_verification(
            reference_bytes=reference_data,
            questioned_bytes=questioned_data,
            reference_hash=reference_hash,
            questioned_hash=questioned_hash,
            reference_evidence_id=reference_id,
            questioned_evidence_id=questioned_id,
            processing_job_id=None,
            artifact_evidence=artifact_evidence,
        )

    async def create_job(
        self,
        questioned_evidence_id: UUID,
        reference_evidence_id: UUID,
    ) -> ProcessingJobResponse:
        questioned = await self.session.get(Evidence, questioned_evidence_id)
        if questioned is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        reference = await self.session.get(Evidence, reference_evidence_id)
        if reference is None:
            raise ResourceNotFoundError(
                "The requested reference evidence was not found.",
            )
        if questioned.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                (
                    "Process and extract the questioned evidence before "
                    "signature analysis."
                ),
            )
        active = await self.job_repository.get_active(
            questioned_evidence_id,
            ProcessingJobType.SIGNATURE_VERIFICATION,
        )
        if active is not None:
            raise ConflictError("An active signature verification job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=questioned_evidence_id,
            job_type=ProcessingJobType.SIGNATURE_VERIFICATION,
            status=ProcessingJobStatus.QUEUED,
            priority=0,
            attempt=0,
            max_attempts=1,
            metadata_json={
                "runner": "local",
                "reference_evidence_id": str(reference_evidence_id),
                "questioned_sha256": questioned.sha256_hash,
                "reference_sha256": reference.sha256_hash,
            },
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active signature verification job already exists.",
            ) from exc
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.SIGNATURE_VERIFICATION
        ):
            return
        reference_id_raw = job.metadata_json.get("reference_evidence_id")
        if not isinstance(reference_id_raw, str):
            await self._fail_job(
                job_id,
                "INVALID_JOB",
                "Signature verification job is missing reference evidence.",
            )
            return
        reference_evidence_id = UUID(reference_id_raw)
        questioned = await self.session.get(Evidence, job.evidence_id)
        reference = await self.session.get(Evidence, reference_evidence_id)
        if questioned is None or reference is None:
            await self._fail_job(
                job_id,
                "EVIDENCE_NOT_FOUND",
                "The evidence records are no longer available.",
            )
            return
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = datetime.now(UTC)
        created_artifact: Artifact | None = None
        try:
            reference_bytes = await load_bytes_from_storage(
                self.storage,
                reference.storage_key,
                max_bytes=MAX_SIGNATURE_BYTES,
            )
            questioned_bytes = await load_bytes_from_storage(
                self.storage,
                questioned.storage_key,
                max_bytes=MAX_SIGNATURE_BYTES,
            )
            response = await self._execute_verification(
                reference_bytes=reference_bytes,
                questioned_bytes=questioned_bytes,
                reference_hash=reference.sha256_hash,
                questioned_hash=questioned.sha256_hash,
                reference_evidence_id=reference.id,
                questioned_evidence_id=questioned.id,
                processing_job_id=job.id,
                artifact_evidence=questioned,
            )
            job.status = ProcessingJobStatus.SUCCEEDED
            job.completed_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "signature_verification_run_id": str(response.id),
                "verdict": response.verdict.value,
                "similarity": response.similarity,
            }
            questioned.metadata_json = {
                **questioned.metadata_json,
                "signature_verification": {
                    "verdict": response.verdict.value,
                    "similarity": response.similarity,
                    "reference_evidence_id": str(reference.id),
                    "run_id": str(response.id),
                },
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if created_artifact is not None:
                await self.artifact_service.cleanup(created_artifact)
            if isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "SIGNATURE_VERIFICATION_FAILED"
                safe_message = "Signature verification failed."
            await self._fail_job(job_id, error_code, safe_message)
            logger.exception(
                "Signature verification job failed",
                extra={"job_id": str(job_id), "evidence_id": str(job.evidence_id)},
            )

    async def get_run(self, verification_id: UUID) -> SignatureVerificationResponse:
        run = await self.session.get(SignatureVerificationRun, verification_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested signature verification run was not found.",
            )
        return self._run_response(run)

    async def list_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> SignatureVerificationListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        filters = [SignatureVerificationRun.questioned_evidence_id == evidence_id]
        total = await self.session.scalar(
            select(func.count()).select_from(SignatureVerificationRun).where(*filters)
        )
        result = await self.session.scalars(
            select(SignatureVerificationRun)
            .where(*filters)
            .order_by(SignatureVerificationRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        runs = list(result)
        return SignatureVerificationListResponse(
            items=[self._run_response(run) for run in runs],
            total=int(total or 0),
            limit=limit,
            offset=offset,
        )

    async def _execute_verification(
        self,
        *,
        reference_bytes: bytes,
        questioned_bytes: bytes,
        reference_hash: str,
        questioned_hash: str,
        reference_evidence_id: UUID | None,
        questioned_evidence_id: UUID | None,
        processing_job_id: UUID | None,
        artifact_evidence: Evidence | None = None,
    ) -> SignatureVerificationResponse:
        device = self.signature_settings.default_device
        started = time.perf_counter()
        prediction = await self.engine.verify_pair(
            reference_bytes,
            questioned_bytes,
            device=device,
        )
        verdict = SignatureVerdict(str(prediction.get("verdict", "UNAVAILABLE")))
        similarity_raw = prediction.get("similarity")
        similarity = (
            float(similarity_raw)
            if verdict != SignatureVerdict.UNAVAILABLE and similarity_raw is not None
            else None
        )
        threshold = float(
            prediction.get("threshold", self.signature_settings.threshold),
        )
        processing_time_ms = prediction.get("processing_time_ms")
        if processing_time_ms is None:
            processing_time_ms = round((time.perf_counter() - started) * 1000.0, 3)
        run = SignatureVerificationRun(
            id=uuid4(),
            reference_evidence_id=reference_evidence_id,
            questioned_evidence_id=questioned_evidence_id,
            processing_job_id=processing_job_id,
            reference_hash=reference_hash,
            questioned_hash=questioned_hash,
            model_name=str(prediction.get("model", "siamese-signature")),
            model_version=str(
                prediction.get("model_version", self.signature_settings.model_version),
            ),
            similarity=similarity,
            threshold=threshold,
            verdict=verdict,
            device=str(prediction.get("device", device)),
            processing_time_ms=float(processing_time_ms),
            metadata_json={
                "status": str(prediction.get("status", "ok")),
                "reason": prediction.get("reason"),
                "backbone": prediction.get("backbone"),
                "model_hash": prediction.get("model_hash"),
            },
        )
        artifact_id: UUID | None = None
        if artifact_evidence is not None:
            artifact_payload = DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_SIGNATURE_PREDICTION,
                mime_type="application/json",
                content=json.dumps(
                    {
                        "verdict": verdict.value,
                        "similarity": similarity,
                        "threshold": threshold,
                        "reference_hash": reference_hash,
                        "questioned_hash": questioned_hash,
                        "model": run.model_name,
                        "model_version": run.model_version,
                        "metadata": run.metadata_json,
                    },
                    sort_keys=True,
                ).encode("utf-8"),
                metadata={
                    "verdict": verdict.value,
                    "reference_evidence_id": (
                        str(reference_evidence_id) if reference_evidence_id else None
                    ),
                    "questioned_evidence_id": (
                        str(questioned_evidence_id) if questioned_evidence_id else None
                    ),
                },
            )
            artifact = await self.artifact_service.create(
                artifact_evidence,
                artifact_payload,
            )
            artifact_id = artifact.id
            run.artifact_id = artifact_id
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return self._run_response(run)

    async def _resolve_signature_input(
        self,
        *,
        evidence_id: UUID | None,
        raw_bytes: bytes | None,
        label: str,
    ) -> tuple[bytes, str, UUID | None]:
        if raw_bytes is not None:
            if len(raw_bytes) > MAX_SIGNATURE_BYTES:
                raise ProcessingError(
                    "SIGNATURE_TOO_LARGE",
                    f"The {label} signature exceeds the configured size limit.",
                )
            return raw_bytes, hashlib.sha256(raw_bytes).hexdigest(), evidence_id
        if evidence_id is None:
            raise ProcessingError(
                "SIGNATURE_INPUT_REQUIRED",
                f"Provide {label} evidence or upload {label} signature bytes.",
            )
        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError(
                f"The requested {label} evidence was not found.",
            )
        data = await load_bytes_from_storage(
            self.storage,
            evidence.storage_key,
            max_bytes=MAX_SIGNATURE_BYTES,
        )
        return data, evidence.sha256_hash, evidence.id

    async def _fail_job(
        self,
        job_id: UUID,
        error_code: str,
        message: str,
    ) -> None:
        job = await self.job_repository.get(job_id)
        if job is not None:
            job.status = ProcessingJobStatus.FAILED
            job.error_code = error_code
            job.error_message_safe = message
            job.completed_at = datetime.now(UTC)
        await self.session.commit()

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
    def _run_response(run: SignatureVerificationRun) -> SignatureVerificationResponse:
        localization = None
        if run.localization_json is not None:
            localization = SignatureRegionResponse(
                x=float(run.localization_json.get("x", 0)),
                y=float(run.localization_json.get("y", 0)),
                width=float(run.localization_json.get("width", 0)),
                height=float(run.localization_json.get("height", 0)),
                page_number=run.localization_json.get("page_number"),
                confidence=run.localization_json.get("confidence"),
            )
        return SignatureVerificationResponse(
            id=run.id,
            reference_hash=run.reference_hash,
            questioned_hash=run.questioned_hash,
            model=run.model_name,
            model_version=run.model_version,
            similarity=run.similarity,
            threshold=run.threshold,
            verdict=run.verdict,
            device=run.device,
            processing_time_ms=run.processing_time_ms,
            reference_evidence_id=run.reference_evidence_id,
            questioned_evidence_id=run.questioned_evidence_id,
            localization=localization,
            artifact_id=run.artifact_id,
            metadata=run.metadata_json,
            created_at=run.created_at,
        )
