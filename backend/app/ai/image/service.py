"""Application service for AI image forensic analysis."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.image.bootstrap import build_image_analysis_stack
from backend.app.ai.image.config import ImageAISettings
from backend.app.ai.image.engine import ENGINE_VERSION, ImageAnalysisEngine
from backend.app.ai.image.exceptions import ImageAnalysisError
from backend.app.ai.image.models import ImageAnalysisContext, ImageAnalysisRunStatus
from backend.app.ai.image.repository import ImageAnalysisRepository
from backend.app.ai.image.schemas import (
    ImageAIFindingListResponse,
    ImageAIFindingResponse,
    ImageAnalysisRunListResponse,
    ImageAnalysisRunResponse,
    ImageFindingRegionResponse,
)
from backend.app.api.schemas.processing import ProcessingJobResponse
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
from backend.app.domain.evidence import EvidenceStatus
from backend.app.domain.processing import (
    ArtifactType,
    EvidenceClassification,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.forensics.utils import load_image_from_storage
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
    ProcessingJobRepository,
)
from backend.app.models.evidence import Evidence
from backend.app.models.image_ai import (
    ImageAIFinding,
    ImageAIFindingRegion,
    ImageAnalysisRun,
)
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)


class ImageAnalysisService:
    """Queue and execute pluggable AI image forensic detectors."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: ImageAnalysisEngine | None = None,
        image_settings: ImageAISettings | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.image_settings = image_settings or ImageAISettings()
        if engine is None:
            _, _, engine = build_image_analysis_stack(self.image_settings)
        self.engine = engine
        self.job_repository = ProcessingJobRepository(session)
        self.repository = ImageAnalysisRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )

    async def create_job(self, evidence_id: UUID) -> ProcessingJobResponse:
        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if evidence.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process and extract the evidence before AI image analysis.",
            )
        classification = await self._classification(evidence)
        if classification != EvidenceClassification.IMAGE:
            raise ProcessingError(
                "UNSUPPORTED_EVIDENCE",
                "AI image analysis requires image evidence.",
            )
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
        active = await self.job_repository.get_active(
            evidence_id,
            ProcessingJobType.IMAGE_AI_ANALYSIS,
        )
        if active is not None:
            raise ConflictError("An active AI image analysis job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.IMAGE_AI_ANALYSIS,
            status=ProcessingJobStatus.QUEUED,
            priority=0,
            attempt=0,
            max_attempts=1,
            metadata_json={
                "runner": "local",
                "source_sha256": evidence.sha256_hash,
                "engine_version": ENGINE_VERSION,
            },
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active AI image analysis job already exists.",
            ) from exc
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.IMAGE_AI_ANALYSIS
        ):
            return
        evidence = await self.session.get(Evidence, job.evidence_id)
        if evidence is None:
            await self._fail_job(
                job_id,
                None,
                "EVIDENCE_NOT_FOUND",
                "The evidence record is no longer available.",
            )
            return
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = datetime.now(UTC)
        analysis_run = ImageAnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            processing_job_id=job.id,
            status=ImageAnalysisRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            device=self.image_settings.default_device,
            findings_count=0,
            started_at=datetime.now(UTC),
            metadata_json={"source_sha256": evidence.sha256_hash},
        )
        created_artifacts: list[Artifact] = []
        try:
            await self.repository.add_run(analysis_run)
            await self.session.commit()
            context = await self._context(evidence)
            result = await self.engine.analyze(context)
            if result.status != ImageAnalysisRunStatus.SUCCEEDED:
                raise ImageAnalysisError(
                    result.error_code or "ANALYSIS_FAILED",
                    result.error_message_safe or "AI image analysis failed.",
                )
            artifact_by_detector: dict[str, dict[str, UUID]] = {}
            for payload in result.artifacts:
                artifact = await self.artifact_service.create(evidence, payload)
                created_artifacts.append(artifact)
                detector = str(payload.metadata.get("detector", "unknown"))
                bucket = artifact_by_detector.setdefault(detector, {})
                if payload.artifact_type == ArtifactType.AI_IMAGE_HEATMAP:
                    bucket["heatmap"] = artifact.id
                elif payload.artifact_type == ArtifactType.AI_IMAGE_MASK:
                    bucket["mask"] = artifact.id
            findings_count = 0
            for item in result.findings:
                detector_artifacts = artifact_by_detector.get(item.detector, {})
                await self._persist_finding(
                    analysis_run,
                    evidence.id,
                    item,
                    heatmap_artifact_id=detector_artifacts.get("heatmap"),
                    mask_artifact_id=detector_artifacts.get("mask"),
                )
                findings_count += 1
            analysis_run.status = ImageAnalysisRunStatus.SUCCEEDED
            analysis_run.findings_count = findings_count
            analysis_run.latency_ms = result.latency_ms
            analysis_run.device = result.device
            analysis_run.completed_at = datetime.now(UTC)
            analysis_run.metadata_json = {
                **analysis_run.metadata_json,
                **result.metadata,
            }
            evidence.metadata_json = {
                **evidence.metadata_json,
                "ai_image_analysis": {
                    "status": result.status.value,
                    "engine_version": ENGINE_VERSION,
                    "findings_count": findings_count,
                    "latency_ms": result.latency_ms,
                    "device": result.device,
                },
            }
            job.status = ProcessingJobStatus.SUCCEEDED
            job.completed_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "image_analysis_run_id": str(analysis_run.id),
                "findings_count": findings_count,
                "latency_ms": result.latency_ms,
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, ImageAnalysisError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "IMAGE_ANALYSIS_FAILED"
                safe_message = "The AI image analysis pipeline failed."
            await self._fail_job(job_id, analysis_run.id, error_code, safe_message)
            logger.exception(
                "AI image analysis job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ImageAnalysisRunListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return ImageAnalysisRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_run(self, analysis_id: UUID) -> ImageAnalysisRunResponse:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested image analysis run was not found.",
            )
        return self._run_response(run)

    async def list_findings(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
        detector: str | None = None,
    ) -> ImageAIFindingListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        findings, total = await self.repository.list_findings_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        )
        return ImageAIFindingListResponse(
            items=[self._finding_response(item) for item in findings],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _context(self, evidence: Evidence) -> ImageAnalysisContext:
        classification = await self._classification(evidence)
        max_bytes = self.image_settings.max_image_bytes
        rgb, width, height = await load_image_from_storage(
            self.storage,
            evidence.storage_key,
            max_bytes=max_bytes,
        )
        return ImageAnalysisContext(
            evidence_id=evidence.id,
            case_id=evidence.case_id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            storage_key=evidence.storage_key,
            classification=classification,
            source_sha256=evidence.sha256_hash,
            storage=self.storage,
            settings=self.settings,
            image_array=rgb,
            width=width,
            height=height,
        )

    async def _classification(self, evidence: Evidence) -> EvidenceClassification:
        raw = evidence.metadata_json.get("classification")
        if isinstance(raw, str):
            try:
                return EvidenceClassification(raw)
            except ValueError:
                pass
        artifacts, _ = await self.artifact_repository.list_for_evidence(
            evidence.id,
            artifact_types=(ArtifactType.CLASSIFICATION,),
            limit=1,
            offset=0,
        )
        if artifacts:
            meta = artifacts[0].metadata_json
            raw_value = meta.get("classification")
            if isinstance(raw_value, str):
                try:
                    return EvidenceClassification(raw_value)
                except ValueError:
                    pass
        return EvidenceClassification.UNKNOWN

    async def _persist_finding(
        self,
        analysis_run: ImageAnalysisRun,
        evidence_id: UUID,
        item: object,
        *,
        heatmap_artifact_id: UUID | None,
        mask_artifact_id: UUID | None,
    ) -> None:
        from backend.app.ai.image.models import ImageAIFindingItem

        assert isinstance(item, ImageAIFindingItem)
        finding = ImageAIFinding(
            id=uuid4(),
            analysis_run_id=analysis_run.id,
            evidence_id=evidence_id,
            detector=item.detector,
            category=item.category,
            severity=item.severity,
            confidence=item.confidence,
            description=item.description,
            explanation=item.explanation,
            recommendation=item.recommendation,
            model_name=item.model_name,
            model_version=item.model_version,
            model_framework=item.model_framework,
            heatmap_artifact_id=heatmap_artifact_id,
            mask_artifact_id=mask_artifact_id,
            metadata_json=item.metadata,
        )
        await self.repository.add_finding(finding)
        for region in item.regions:
            await self.repository.add_region(
                ImageAIFindingRegion(
                    id=uuid4(),
                    finding_id=finding.id,
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    page_number=region.page_number,
                    frame_number=region.frame_number,
                    polygon_json=(
                        [list(point) for point in region.polygon]
                        if region.polygon
                        else None
                    ),
                    normalized_x=region.normalized.x if region.normalized else None,
                    normalized_y=region.normalized.y if region.normalized else None,
                    normalized_width=(
                        region.normalized.width if region.normalized else None
                    ),
                    normalized_height=(
                        region.normalized.height if region.normalized else None
                    ),
                )
            )

    async def _fail_job(
        self,
        job_id: UUID,
        analysis_run_id: UUID | None,
        error_code: str,
        message: str,
    ) -> None:
        job = await self.job_repository.get(job_id)
        if job is not None:
            job.status = ProcessingJobStatus.FAILED
            job.error_code = error_code
            job.error_message_safe = message
            job.completed_at = datetime.now(UTC)
        if analysis_run_id is not None:
            run = await self.repository.get_run(analysis_run_id)
            if run is not None:
                run.status = ImageAnalysisRunStatus.FAILED
                run.error_code = error_code
                run.error_message = message
                run.completed_at = datetime.now(UTC)
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
    def _run_response(run: ImageAnalysisRun) -> ImageAnalysisRunResponse:
        return ImageAnalysisRunResponse(
            id=run.id,
            evidence_id=run.evidence_id,
            status=run.status,
            engine_version=run.engine_version,
            device=run.device,
            latency_ms=run.latency_ms,
            findings_count=run.findings_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
        )

    @staticmethod
    def _region_responses(
        regions: list[ImageAIFindingRegion],
    ) -> list[ImageFindingRegionResponse]:
        responses: list[ImageFindingRegionResponse] = []
        for region in regions:
            responses.append(
                ImageFindingRegionResponse(
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    page_number=region.page_number,
                    frame_number=region.frame_number,
                    polygon=(
                        [
                            (float(point[0]), float(point[1]))
                            for point in region.polygon_json
                        ]
                        if region.polygon_json
                        else None
                    ),
                    normalized_location=(
                        {
                            "x": region.normalized_x,
                            "y": region.normalized_y,
                            "width": region.normalized_width,
                            "height": region.normalized_height,
                        }
                        if region.normalized_x is not None
                        and region.normalized_y is not None
                        and region.normalized_width is not None
                        and region.normalized_height is not None
                        else None
                    ),
                )
            )
        return responses

    @staticmethod
    def _finding_response(finding: ImageAIFinding) -> ImageAIFindingResponse:
        return ImageAIFindingResponse(
            id=finding.id,
            analysis_run_id=finding.analysis_run_id,
            detector=finding.detector,
            category=finding.category,
            severity=finding.severity,
            confidence=finding.confidence,
            description=finding.description,
            explanation=finding.explanation,
            recommendation=finding.recommendation,
            model_name=finding.model_name,
            model_version=finding.model_version,
            model_framework=finding.model_framework,
            heatmap_artifact_id=finding.heatmap_artifact_id,
            mask_artifact_id=finding.mask_artifact_id,
            regions=ImageAnalysisService._region_responses(finding.regions),
            metadata=finding.metadata_json,
            created_at=finding.created_at,
        )
