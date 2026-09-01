"""Application service for AI document forensic analysis."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.document.bootstrap import build_document_analysis_stack
from backend.app.ai.document.config import DocumentAISettings
from backend.app.ai.document.engine import ENGINE_VERSION, DocumentAnalysisEngine
from backend.app.ai.document.exceptions import DocumentAnalysisError
from backend.app.ai.document.models.base import DocumentAnalysisRunStatus
from backend.app.ai.document.models.context import DocumentAnalysisContext
from backend.app.ai.document.preprocessing.regions import extraction_record_dict
from backend.app.ai.document.reference.comparator import ReferenceDocumentComparator
from backend.app.ai.document.repository import DocumentAnalysisRepository
from backend.app.ai.document.schemas import (
    DocumentAIFindingListResponse,
    DocumentAIFindingResponse,
    DocumentAnalysisRunListResponse,
    DocumentAnalysisRunResponse,
    DocumentFindingRegionResponse,
)
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.application.processors.base import ProcessorContext
from backend.app.application.processors.inspection import FileInspectionProcessor
from backend.app.application.services.artifact_service import ArtifactService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.comparison.repository import ComparisonRepository
from backend.app.comparison.utils import extract_text_content
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
from backend.app.infrastructure.database.repositories.extraction import (
    ExtractionRepository,
)
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
    ProcessingJobRepository,
)
from backend.app.models.document_ai import (
    DocumentAIFinding,
    DocumentAIFindingRegion,
    DocumentAnalysisRun,
)
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)


class DocumentAnalysisService:
    """Queue and execute pluggable AI document forensic detectors."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: DocumentAnalysisEngine | None = None,
        document_settings: DocumentAISettings | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.document_settings = document_settings or DocumentAISettings()
        if engine is None:
            _, _, engine = build_document_analysis_stack(self.document_settings)
        self.engine = engine
        self.job_repository = ProcessingJobRepository(session)
        self.repository = DocumentAnalysisRepository(session)
        self.extraction_repository = ExtractionRepository(session)
        self.comparison_repository = ComparisonRepository(session)
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
                "Process and extract the evidence before AI document analysis.",
            )
        classification = await self._classification(evidence)
        if classification not in {
            EvidenceClassification.DOCUMENT,
            EvidenceClassification.IMAGE,
        }:
            raise ProcessingError(
                "UNSUPPORTED_EVIDENCE",
                "AI document analysis requires document or page image evidence.",
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
            ProcessingJobType.DOCUMENT_AI_ANALYSIS,
        )
        if active is not None:
            raise ConflictError("An active AI document analysis job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.DOCUMENT_AI_ANALYSIS,
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
                "An active AI document analysis job already exists.",
            ) from exc
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.DOCUMENT_AI_ANALYSIS
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
        analysis_run = DocumentAnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            processing_job_id=job.id,
            status=DocumentAnalysisRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            device=self.document_settings.default_device,
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
            if result.status != DocumentAnalysisRunStatus.SUCCEEDED:
                raise DocumentAnalysisError(
                    result.error_code or "ANALYSIS_FAILED",
                    result.error_message_safe or "AI document analysis failed.",
                )
            artifact_by_detector: dict[str, dict[str, UUID]] = {}
            for payload in result.artifacts:
                artifact = await self.artifact_service.create(evidence, payload)
                created_artifacts.append(artifact)
                detector = str(payload.metadata.get("detector", "unknown"))
                bucket = artifact_by_detector.setdefault(detector, {})
                if payload.artifact_type == ArtifactType.AI_DOCUMENT_HEATMAP:
                    bucket["heatmap"] = artifact.id
                elif payload.artifact_type == ArtifactType.AI_DOCUMENT_MASK:
                    bucket["mask"] = artifact.id
                elif payload.artifact_type == ArtifactType.AI_DOCUMENT_OVERLAY:
                    bucket["overlay"] = artifact.id
                elif payload.artifact_type == ArtifactType.AI_DOCUMENT_PREDICTION:
                    bucket["prediction"] = artifact.id
            findings_count = 0
            for item in result.findings:
                detector_artifacts = artifact_by_detector.get(item.detector, {})
                artifact_id = (
                    detector_artifacts.get("prediction")
                    or detector_artifacts.get("heatmap")
                    or detector_artifacts.get("overlay")
                    or detector_artifacts.get("mask")
                )
                await self._persist_finding(
                    analysis_run,
                    evidence.id,
                    item,
                    artifact_id=artifact_id,
                )
                findings_count += 1
            analysis_run.status = DocumentAnalysisRunStatus.SUCCEEDED
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
                "ai_document_analysis": {
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
                "document_analysis_run_id": str(analysis_run.id),
                "findings_count": findings_count,
                "latency_ms": result.latency_ms,
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, DocumentAnalysisError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "DOCUMENT_ANALYSIS_FAILED"
                safe_message = "The AI document analysis pipeline failed."
            await self._fail_job(job_id, analysis_run.id, error_code, safe_message)
            logger.exception(
                "AI document analysis job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> DocumentAnalysisRunListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return DocumentAnalysisRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_run(self, analysis_id: UUID) -> DocumentAnalysisRunResponse:
        run = await self.repository.get_run(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested document analysis run was not found.",
            )
        return self._run_response(run)

    async def list_findings(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
        detector: str | None = None,
    ) -> DocumentAIFindingListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        findings, total = await self.repository.list_findings_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
            detector=detector,
        )
        return DocumentAIFindingListResponse(
            items=[self._finding_response(item) for item in findings],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _context(self, evidence: Evidence) -> DocumentAnalysisContext:
        classification = await self._classification(evidence)
        records, _ = await self.extraction_repository.list_for_evidence(
            evidence.id,
            extraction_type=None,
            limit=500,
            offset=0,
        )
        extraction_records = tuple(extraction_record_dict(record) for record in records)
        extraction_artifact_items, _ = await self.artifact_repository.list_for_evidence(
            evidence.id,
            artifact_types=(
                ArtifactType.OCR_RESULT,
                ArtifactType.DOCUMENT_STRUCTURE,
                ArtifactType.IMAGE_REGIONS,
                ArtifactType.TEXT_RESULT,
            ),
            limit=100,
            offset=0,
        )
        forensic_artifact_items, _ = await self.artifact_repository.list_for_evidence(
            evidence.id,
            artifact_types=(
                ArtifactType.FORENSIC_HEATMAP,
                ArtifactType.FORENSIC_OVERLAY,
            ),
            limit=100,
            offset=0,
        )
        differences, _ = await self.comparison_repository.list_differences_for_evidence(
            evidence.id,
            limit=500,
            offset=0,
        )
        comparison_differences = ReferenceDocumentComparator.differences_to_records(
            differences,
        )
        document_text = extract_text_content(extraction_records)
        return DocumentAnalysisContext(
            evidence_id=evidence.id,
            case_id=evidence.case_id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            storage_key=evidence.storage_key,
            classification=classification,
            source_sha256=evidence.sha256_hash,
            storage=self.storage,
            settings=self.settings,
            device=self.document_settings.default_device,
            extraction_records=extraction_records,
            extraction_artifacts=tuple(
                {
                    "id": str(item.id),
                    "artifact_type": item.artifact_type.value,
                    "metadata": item.metadata_json,
                }
                for item in extraction_artifact_items
            ),
            forensic_artifacts=tuple(
                {
                    "id": str(item.id),
                    "artifact_type": item.artifact_type.value,
                    "metadata": item.metadata_json,
                }
                for item in forensic_artifact_items
            ),
            comparison_differences=comparison_differences,
            document_text=document_text,
            metadata_json=evidence.metadata_json,
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
        analysis_run: DocumentAnalysisRun,
        evidence_id: UUID,
        item: object,
        *,
        artifact_id: UUID | None,
    ) -> None:
        from backend.app.ai.document.models.base import DocumentAIFindingItem

        assert isinstance(item, DocumentAIFindingItem)
        finding = DocumentAIFinding(
            id=uuid4(),
            analysis_run_id=analysis_run.id,
            evidence_id=evidence_id,
            detector=item.detector,
            category=item.category,
            severity=item.severity,
            method=item.method,
            confidence=item.confidence,
            description=item.description,
            explanation=item.explanation,
            recommendation=item.recommendation,
            model_name=item.model_name,
            model_version=item.model_version,
            model_framework=item.model_framework,
            artifact_id=artifact_id,
            metadata_json=item.metadata,
        )
        await self.repository.add_finding(finding)
        for region in item.regions:
            await self.repository.add_region(
                DocumentAIFindingRegion(
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
                run.status = DocumentAnalysisRunStatus.FAILED
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
    def _run_response(run: DocumentAnalysisRun) -> DocumentAnalysisRunResponse:
        return DocumentAnalysisRunResponse(
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
        regions: list[DocumentAIFindingRegion],
    ) -> list[DocumentFindingRegionResponse]:
        responses: list[DocumentFindingRegionResponse] = []
        for region in regions:
            responses.append(
                DocumentFindingRegionResponse(
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
    def _finding_response(finding: DocumentAIFinding) -> DocumentAIFindingResponse:
        return DocumentAIFindingResponse(
            id=finding.id,
            analysis_run_id=finding.analysis_run_id,
            detector=finding.detector,
            category=finding.category,
            severity=finding.severity,
            method=finding.method,
            confidence=finding.confidence,
            description=finding.description,
            explanation=finding.explanation,
            recommendation=finding.recommendation,
            model_name=finding.model_name,
            model_version=finding.model_version,
            model_framework=finding.model_framework,
            artifact_id=finding.artifact_id,
            regions=DocumentAnalysisService._region_responses(finding.regions),
            metadata=finding.metadata_json,
            created_at=finding.created_at,
        )
