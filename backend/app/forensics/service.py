"""Application service for deterministic forensic analysis."""

import logging
from datetime import UTC, datetime
from pathlib import PurePath
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
    EvidenceClassification,
    ProcessingJobStatus,
    ProcessingJobType,
)
from backend.app.forensics.engine import ENGINE_VERSION, ForensicAnalysisEngine
from backend.app.forensics.exceptions import ForensicAnalysisError
from backend.app.forensics.localization import regions_to_responses
from backend.app.forensics.models import (
    AnalysisContext,
    AnalysisRunStatus,
    FindingItem,
    RegionBox,
)
from backend.app.forensics.repository import ForensicRepository
from backend.app.forensics.schemas import (
    AnalysisRunListResponse,
    AnalysisRunResponse,
    AnalysisSummaryResponse,
    FindingListResponse,
    FindingResponse,
)
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
from backend.app.models.forensics import AnalysisRun, Finding, FindingRegion
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)


class ForensicAnalysisService:
    """Queue and execute replaceable forensic detector plugins."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: ForensicAnalysisEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or ForensicAnalysisEngine()
        self.job_repository = ProcessingJobRepository(session)
        self.repository = ForensicRepository(session)
        self.extraction_repository = ExtractionRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.custody_repository = CustodyRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )

    async def create_job(self, evidence_id: UUID) -> ProcessingJobResponse:
        """Create a forensic analysis job after integrity verification."""

        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if evidence.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process and extract the evidence before starting analysis.",
            )
        extraction_job = await self.job_repository.latest_for_evidence(
            evidence_id,
            ProcessingJobType.EXTRACTION,
        )
        if (
            extraction_job is None
            or extraction_job.status != ProcessingJobStatus.SUCCEEDED
        ):
            raise ProcessingError(
                "EXTRACTION_REQUIRED",
                "Run extraction before starting forensic analysis.",
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
        latest = await self.job_repository.latest_for_evidence(
            evidence_id,
            ProcessingJobType.ANALYSIS,
        )
        if (
            latest is not None
            and latest.status == ProcessingJobStatus.SUCCEEDED
            and latest.metadata_json.get("source_sha256") == evidence.sha256_hash
            and latest.metadata_json.get("engine_version") == ENGINE_VERSION
        ):
            return self._job_response(latest)
        active = await self.job_repository.get_active(
            evidence_id,
            ProcessingJobType.ANALYSIS,
        )
        if active is not None:
            raise ConflictError("An active analysis job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.ANALYSIS,
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
            raise ConflictError("An active analysis job already exists.") from exc
        logger.info(
            "Analysis job created",
            extra={"job_id": str(job.id), "evidence_id": str(evidence_id)},
        )
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        """Execute exactly one queued forensic analysis job."""

        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.ANALYSIS
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
        analysis_run = AnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            processing_job_id=job.id,
            status=AnalysisRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            findings_count=0,
            started_at=datetime.now(UTC),
            metadata_json={"source_sha256": evidence.sha256_hash},
        )
        created_artifacts: list[Artifact] = []
        try:
            await self.repository.add_run(analysis_run)
            evidence.status = EvidenceStatus.ANALYZING
            await self.session.commit()
            await self._record_event(
                evidence.id,
                CustodyEventType.ANALYSIS_STARTED,
                "Forensic analysis started.",
                evidence.sha256_hash,
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
            context = await self._context(evidence)
            result = await self.engine.analyze(context)
            findings_count = 0
            for payload in result.artifacts:
                artifact = await self.artifact_service.create(evidence, payload)
                created_artifacts.append(artifact)
                await self._record_event_in_transaction(
                    evidence.id,
                    CustodyEventType.ANALYSIS_ARTIFACT_CREATED,
                    f"{payload.artifact_type.value} forensic artifact created.",
                    artifact.sha256_hash,
                    {
                        "artifact_id": str(artifact.id),
                        "detector": payload.metadata.get("detector"),
                    },
                )
            for item in result.findings:
                await self._persist_finding(analysis_run, evidence.id, item)
                findings_count += 1
            analysis_run.status = AnalysisRunStatus.SUCCEEDED
            analysis_run.findings_count = findings_count
            analysis_run.completed_at = datetime.now(UTC)
            analysis_run.metadata_json = {
                **analysis_run.metadata_json,
                **result.metadata,
            }
            evidence.status = EvidenceStatus.ANALYZED
            evidence.metadata_json = {
                **evidence.metadata_json,
                "forensic_analysis": {
                    "status": result.status.value,
                    "engine_version": ENGINE_VERSION,
                    "findings_count": findings_count,
                },
            }
            job.status = ProcessingJobStatus.SUCCEEDED
            job.completed_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "analysis_run_id": str(analysis_run.id),
                "findings_count": findings_count,
            }
            await self._record_event_in_transaction(
                evidence.id,
                CustodyEventType.ANALYSIS_COMPLETED,
                "Forensic analysis completed.",
                evidence.sha256_hash,
                {"findings_count": findings_count},
            )
            await self.session.commit()
            logger.info(
                "Analysis job completed",
                extra={
                    "job_id": str(job_id),
                    "evidence_id": str(evidence.id),
                    "findings_count": findings_count,
                },
            )
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, ForensicAnalysisError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "ANALYSIS_FAILED"
                safe_message = "The forensic analysis pipeline failed."
            await self._fail_job(job_id, analysis_run.id, error_code, safe_message)
            logger.exception(
                "Analysis job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_analysis_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> AnalysisRunListResponse:
        """Return analysis history for one evidence item."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return AnalysisRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_analysis_run(self, analysis_run_id: UUID) -> AnalysisRunResponse:
        """Return one analysis run."""

        run = await self.repository.get_run(analysis_run_id)
        if run is None:
            raise ResourceNotFoundError("The requested analysis run was not found.")
        return self._run_response(run)

    async def get_summary(self, evidence_id: UUID) -> AnalysisSummaryResponse:
        """Return the latest analysis summary."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        run = await self.repository.latest_run_for_evidence(evidence_id)
        if run is None:
            return AnalysisSummaryResponse(
                status=AnalysisRunStatus.QUEUED,
                analysis_run_id=None,
                findings_count=0,
                severity_counts={},
                error_code="ANALYSIS_NOT_RUN",
            )
        findings, _ = await self.repository.list_findings_for_evidence(
            evidence_id,
            limit=500,
            offset=0,
        )
        severity_counts: dict[str, int] = {}
        for finding in findings:
            if finding.analysis_run_id != run.id:
                continue
            severity_counts[finding.severity.value] = (
                severity_counts.get(finding.severity.value, 0) + 1
            )
        return AnalysisSummaryResponse(
            status=run.status,
            analysis_run_id=run.id,
            findings_count=run.findings_count,
            severity_counts=severity_counts,
            error_code=run.error_code,
        )

    async def list_findings(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> FindingListResponse:
        """Return findings for one evidence item."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        findings, total = await self.repository.list_findings_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return FindingListResponse(
            items=[self._finding_response(item) for item in findings],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_heatmaps(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ArtifactListResponse:
        """Return forensic visualization artifacts."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        artifacts, total = await self.repository.list_heatmap_artifacts(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return ArtifactListResponse(
            items=[self._artifact_response(item) for item in artifacts],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _context(self, evidence: Evidence) -> AnalysisContext:
        records, _ = await self.extraction_repository.list_for_evidence(
            evidence.id,
            extraction_type=None,
            limit=500,
            offset=0,
        )
        extraction_records = tuple(
            {
                "id": str(record.id),
                "extraction_type": record.extraction_type.value,
                "content": record.content,
                "page_number": record.page_number,
                "metadata": record.metadata_json,
            }
            for record in records
        )
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
        classification = EvidenceClassification.UNKNOWN
        raw_classification = evidence.metadata_json.get("classification")
        if isinstance(raw_classification, str):
            try:
                classification = EvidenceClassification(raw_classification)
            except ValueError:
                classification = EvidenceClassification.UNKNOWN
        if classification == EvidenceClassification.UNKNOWN:
            (
                classification_artifacts,
                _,
            ) = await self.artifact_repository.list_for_evidence(
                evidence.id,
                artifact_types=(ArtifactType.CLASSIFICATION,),
                limit=1,
                offset=0,
            )
            if classification_artifacts:
                meta = classification_artifacts[0].metadata_json
                raw = meta.get("classification")
                if isinstance(raw, str):
                    try:
                        classification = EvidenceClassification(raw)
                    except ValueError:
                        classification = EvidenceClassification.UNKNOWN
        image_width = evidence.metadata_json.get("image_width")
        image_height = evidence.metadata_json.get("image_height")
        return AnalysisContext(
            evidence_id=evidence.id,
            case_id=evidence.case_id,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            storage_key=evidence.storage_key,
            classification=classification,
            source_sha256=evidence.sha256_hash,
            storage=self.storage,
            settings=self.settings,
            extraction_records=extraction_records,
            extraction_artifacts=tuple(
                {
                    "id": str(item.id),
                    "artifact_type": item.artifact_type.value,
                    "metadata": item.metadata_json,
                }
                for item in extraction_artifact_items
            ),
            image_width=int(image_width) if isinstance(image_width, int) else None,
            image_height=int(image_height) if isinstance(image_height, int) else None,
        )

    async def _persist_finding(
        self,
        analysis_run: AnalysisRun,
        evidence_id: UUID,
        item: FindingItem,
    ) -> Finding:
        finding = Finding(
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
            metadata_json=item.metadata,
        )
        await self.repository.add_finding(finding)
        for region in item.regions:
            await self.repository.add_region(
                FindingRegion(
                    id=uuid4(),
                    finding_id=finding.id,
                    x=region.x,
                    y=region.y,
                    width=region.width,
                    height=region.height,
                    page_number=region.page_number,
                    frame_number=region.frame_number,
                    polygon_json=(
                        [[point[0], point[1]] for point in region.polygon]
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
        return finding

    async def _fail_job(
        self,
        job_id: UUID,
        analysis_run_id: UUID | None,
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
        if analysis_run_id is not None:
            run = await self.repository.get_run(analysis_run_id)
            if run is not None:
                run.status = AnalysisRunStatus.FAILED
                run.completed_at = datetime.now(UTC)
                run.error_code = error_code
                run.error_message = safe_message
        if evidence.status == EvidenceStatus.ANALYZING:
            evidence.status = EvidenceStatus.READY_FOR_ANALYSIS
        await self._record_event_in_transaction(
            evidence.id,
            CustodyEventType.ANALYSIS_FAILED,
            "Forensic analysis failed; original evidence preserved.",
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

    def _job_response(self, job: ProcessingJob) -> ProcessingJobResponse:
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

    def _run_response(self, run: AnalysisRun) -> AnalysisRunResponse:
        return AnalysisRunResponse(
            id=run.id,
            evidence_id=run.evidence_id,
            status=run.status,
            engine_version=run.engine_version,
            findings_count=run.findings_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
        )

    def _finding_response(self, finding: Finding) -> FindingResponse:
        return FindingResponse(
            id=finding.id,
            analysis_run_id=finding.analysis_run_id,
            detector=finding.detector,
            category=finding.category,
            severity=finding.severity,
            confidence=finding.confidence,
            description=finding.description,
            explanation=finding.explanation,
            recommendation=finding.recommendation,
            regions=regions_to_responses(
                tuple(self._region_box(region) for region in finding.regions)
            ),
            metadata=finding.metadata_json,
            created_at=finding.created_at,
        )

    @staticmethod
    def _region_box(region: FindingRegion) -> RegionBox:
        return RegionBox(
            x=region.x,
            y=region.y,
            width=region.width,
            height=region.height,
            page_number=region.page_number,
            frame_number=region.frame_number,
            polygon=(
                tuple((point[0], point[1]) for point in region.polygon_json)
                if region.polygon_json
                else None
            ),
            normalized=(
                RegionBox(
                    x=region.normalized_x,
                    y=region.normalized_y,
                    width=region.normalized_width,
                    height=region.normalized_height,
                    page_number=region.page_number,
                    frame_number=region.frame_number,
                )
                if region.normalized_x is not None
                and region.normalized_y is not None
                and region.normalized_width is not None
                and region.normalized_height is not None
                else None
            ),
        )

    def _artifact_response(self, artifact: Artifact) -> ArtifactResponse:
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
