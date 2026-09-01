"""Application service for reference comparison."""

import logging
from datetime import UTC, datetime
from pathlib import PurePath
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.application.processors.base import ProcessorContext
from backend.app.application.processors.inspection import FileInspectionProcessor
from backend.app.application.services.artifact_service import ArtifactService
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.comparison.engine import ENGINE_VERSION, ComparisonEngine
from backend.app.comparison.exceptions import ComparisonError
from backend.app.comparison.localization import regions_to_responses
from backend.app.comparison.models import (
    ComparisonContext,
    ComparisonRunStatus,
    DifferenceItem,
    RegionBox,
)
from backend.app.comparison.repository import ComparisonRepository
from backend.app.comparison.schemas import (
    ComparisonRunListResponse,
    ComparisonRunResponse,
    ComparisonSummaryResponse,
    DifferenceListResponse,
    DifferenceResponse,
    ReferenceEvidenceCreateRequest,
    ReferenceEvidenceListResponse,
    ReferenceEvidenceResponse,
)
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
from backend.app.infrastructure.database.repositories.custody import CustodyRepository
from backend.app.infrastructure.database.repositories.extraction import (
    ExtractionRepository,
)
from backend.app.infrastructure.database.repositories.processing import (
    ArtifactRepository,
    ProcessingJobRepository,
)
from backend.app.models.comparison import (
    ComparisonRun,
    Difference,
    DifferenceRegion,
    ReferenceEvidence,
)
from backend.app.models.custody import ChainOfCustodyEvent
from backend.app.models.evidence import Evidence
from backend.app.models.processing import Artifact, ProcessingJob

logger = logging.getLogger(__name__)


class ComparisonService:
    """Queue and execute replaceable reference comparison matchers."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: ComparisonEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or ComparisonEngine()
        self.job_repository = ProcessingJobRepository(session)
        self.repository = ComparisonRepository(session)
        self.extraction_repository = ExtractionRepository(session)
        self.artifact_repository = ArtifactRepository(session)
        self.custody_repository = CustodyRepository(session)
        self.artifact_service = ArtifactService(
            session,
            storage,
            hash_service,
            settings,
        )

    async def register_reference(
        self,
        case_id: UUID,
        payload: ReferenceEvidenceCreateRequest,
    ) -> ReferenceEvidenceResponse:
        """Register processed evidence as immutable trusted reference."""

        evidence = await self.session.get(Evidence, payload.evidence_id)
        if evidence is None or evidence.case_id != case_id:
            raise ResourceNotFoundError("The requested evidence was not found.")
        if evidence.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process and extract the evidence before registering a reference.",
            )
        extraction_job = await self.job_repository.latest_for_evidence(
            evidence.id,
            ProcessingJobType.EXTRACTION,
        )
        if (
            extraction_job is None
            or extraction_job.status != ProcessingJobStatus.SUCCEEDED
        ):
            raise ProcessingError(
                "EXTRACTION_REQUIRED",
                "Run extraction before registering reference evidence.",
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
        reference = ReferenceEvidence(
            id=uuid4(),
            case_id=case_id,
            evidence_id=evidence.id,
            label=payload.label,
            description=payload.description,
            reference_hash=evidence.sha256_hash,
            metadata_json={
                "original_filename": evidence.original_filename,
                "mime_type": evidence.mime_type,
                "file_size": evidence.file_size,
                **evidence.metadata_json,
            },
        )
        await self.repository.add_reference(reference)
        await self._record_event_in_transaction(
            evidence.id,
            CustodyEventType.REFERENCE_REGISTERED,
            f"Evidence registered as trusted reference '{payload.label}'.",
            evidence.sha256_hash,
            {"reference_id": str(reference.id), "label": payload.label},
        )
        await self.session.commit()
        await self.session.refresh(reference)
        return self._reference_response(reference, evidence)

    async def list_references(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ReferenceEvidenceListResponse:
        """Return trusted references for one case."""

        references, total = await self.repository.list_references_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        items: list[ReferenceEvidenceResponse] = []
        for reference in references:
            evidence = await self.session.get(Evidence, reference.evidence_id)
            if evidence is None:
                continue
            items.append(self._reference_response(reference, evidence))
        return ReferenceEvidenceListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def create_job(
        self,
        evidence_id: UUID,
        reference_record_id: UUID,
    ) -> ProcessingJobResponse:
        """Create a comparison job after integrity verification."""

        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        reference = await self.repository.get_reference(reference_record_id)
        if reference is None or reference.case_id != evidence.case_id:
            raise ResourceNotFoundError("The requested reference was not found.")
        if evidence.id == reference.evidence_id:
            raise ProcessingError(
                "SAME_EVIDENCE",
                "Questioned evidence cannot be compared against itself.",
            )
        if evidence.status not in {
            EvidenceStatus.READY_FOR_ANALYSIS,
            EvidenceStatus.ANALYZED,
        }:
            raise ProcessingError(
                "EVIDENCE_NOT_READY",
                "Process and extract the evidence before comparison.",
            )
        ref_evidence = await self.session.get(Evidence, reference.evidence_id)
        if ref_evidence is None:
            raise ResourceNotFoundError("Reference evidence record is unavailable.")
        if ref_evidence.sha256_hash != reference.reference_hash:
            raise ProcessingError(
                "REFERENCE_INTEGRITY_FAILED",
                "Reference hash no longer matches the registered immutable hash.",
            )
        for item in (evidence, ref_evidence):
            await FileInspectionProcessor(
                self.storage,
                self.hash_service,
            ).process(
                ProcessorContext(
                    evidence=item,
                    extension=PurePath(item.original_filename)
                    .suffix.lower()
                    .lstrip("."),
                )
            )
        active = await self.job_repository.get_active(
            evidence_id,
            ProcessingJobType.COMPARISON,
        )
        if active is not None:
            raise ConflictError("An active comparison job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.COMPARISON,
            status=ProcessingJobStatus.QUEUED,
            priority=0,
            attempt=0,
            max_attempts=1,
            metadata_json={
                "runner": "local",
                "reference_record_id": str(reference_record_id),
                "reference_evidence_id": str(reference.evidence_id),
                "questioned_sha256": evidence.sha256_hash,
                "reference_sha256": reference.reference_hash,
                "engine_version": ENGINE_VERSION,
            },
        )
        try:
            await self.job_repository.add(job)
            await self.session.commit()
            await self.session.refresh(job)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError("An active comparison job already exists.") from exc
        logger.info(
            "Comparison job created",
            extra={
                "job_id": str(job.id),
                "evidence_id": str(evidence_id),
                "reference_record_id": str(reference_record_id),
            },
        )
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        """Execute exactly one queued comparison job."""

        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.COMPARISON
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
        reference_record_id = UUID(job.metadata_json["reference_record_id"])
        reference = await self.repository.get_reference(reference_record_id)
        if reference is None:
            await self._fail_job(
                job_id,
                None,
                "REFERENCE_NOT_FOUND",
                "The reference record is no longer available.",
            )
            return
        ref_evidence = await self.session.get(Evidence, reference.evidence_id)
        if ref_evidence is None:
            await self._fail_job(
                job_id,
                None,
                "REFERENCE_EVIDENCE_NOT_FOUND",
                "The reference evidence record is no longer available.",
            )
            return
        job.status = ProcessingJobStatus.RUNNING
        job.attempt += 1
        job.started_at = datetime.now(UTC)
        comparison_run = ComparisonRun(
            id=uuid4(),
            evidence_id=evidence.id,
            reference_record_id=reference.id,
            reference_evidence_id=ref_evidence.id,
            processing_job_id=job.id,
            status=ComparisonRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            differences_count=0,
            started_at=datetime.now(UTC),
            metadata_json={
                "questioned_sha256": evidence.sha256_hash,
                "reference_sha256": reference.reference_hash,
            },
        )
        created_artifacts: list[Artifact] = []
        try:
            await self.repository.add_run(comparison_run)
            await self.session.commit()
            await self._record_event(
                evidence.id,
                CustodyEventType.COMPARISON_STARTED,
                "Reference comparison started.",
                evidence.sha256_hash,
                {"reference_id": str(reference.id)},
            )
            context = await self._context(evidence, ref_evidence, reference)
            result = await self.engine.compare(context)
            differences_count = 0
            for payload in result.artifacts:
                artifact = await self.artifact_service.create(evidence, payload)
                created_artifacts.append(artifact)
                await self._record_event_in_transaction(
                    evidence.id,
                    CustodyEventType.COMPARISON_ARTIFACT_CREATED,
                    f"{payload.artifact_type.value} comparison artifact created.",
                    artifact.sha256_hash,
                    {
                        "artifact_id": str(artifact.id),
                        "matcher": payload.metadata.get("matcher"),
                    },
                )
            for item in result.differences:
                await self._persist_difference(comparison_run, evidence.id, item)
                differences_count += 1
            comparison_run.status = ComparisonRunStatus.SUCCEEDED
            comparison_run.differences_count = differences_count
            comparison_run.completed_at = datetime.now(UTC)
            comparison_run.metadata_json = {
                **comparison_run.metadata_json,
                **result.metadata,
            }
            evidence.metadata_json = {
                **evidence.metadata_json,
                "reference_comparison": {
                    "status": result.status.value,
                    "engine_version": ENGINE_VERSION,
                    "differences_count": differences_count,
                    "reference_id": str(reference.id),
                },
            }
            job.status = ProcessingJobStatus.SUCCEEDED
            job.completed_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "comparison_run_id": str(comparison_run.id),
                "differences_count": differences_count,
            }
            await self._record_event_in_transaction(
                evidence.id,
                CustodyEventType.COMPARISON_COMPLETED,
                "Reference comparison completed.",
                evidence.sha256_hash,
                {"differences_count": differences_count},
            )
            await self.session.commit()
            logger.info(
                "Comparison job completed",
                extra={
                    "job_id": str(job_id),
                    "evidence_id": str(evidence.id),
                    "differences_count": differences_count,
                },
            )
        except Exception as exc:
            await self.session.rollback()
            for artifact in created_artifacts:
                await self.artifact_service.cleanup(artifact)
            if isinstance(exc, ComparisonError):
                error_code = exc.code
                safe_message = exc.message
            elif isinstance(exc, ProcessingError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "COMPARISON_FAILED"
                safe_message = "The reference comparison pipeline failed."
            await self._fail_job(
                job_id,
                comparison_run.id,
                error_code,
                safe_message,
            )
            logger.exception(
                "Comparison job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_comparisons(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> ComparisonRunListResponse:
        """Return comparison history for one evidence item."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return ComparisonRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_comparison(self, comparison_id: UUID) -> ComparisonRunResponse:
        """Return one comparison run."""

        run = await self.repository.get_run(comparison_id)
        if run is None:
            raise ResourceNotFoundError("The requested comparison run was not found.")
        return self._run_response(run)

    async def get_summary(self, evidence_id: UUID) -> ComparisonSummaryResponse:
        """Return the latest comparison summary."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        run = await self.repository.latest_run_for_evidence(evidence_id)
        if run is None:
            return ComparisonSummaryResponse(
                status=ComparisonRunStatus.QUEUED,
                comparison_run_id=None,
                differences_count=0,
                type_counts={},
                error_code="COMPARISON_NOT_RUN",
            )
        differences, _ = await self.repository.list_differences_for_evidence(
            evidence_id,
            limit=500,
            offset=0,
        )
        type_counts: dict[str, int] = {}
        for difference in differences:
            if difference.comparison_run_id != run.id:
                continue
            type_counts[difference.difference_type.value] = (
                type_counts.get(difference.difference_type.value, 0) + 1
            )
        return ComparisonSummaryResponse(
            status=run.status,
            comparison_run_id=run.id,
            differences_count=run.differences_count,
            type_counts=type_counts,
            error_code=run.error_code,
        )

    async def list_differences(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> DifferenceListResponse:
        """Return differences for one evidence item."""

        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        differences, total = await self.repository.list_differences_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return DifferenceListResponse(
            items=[self._difference_response(item) for item in differences],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def _context(
        self,
        questioned: Evidence,
        reference: Evidence,
        reference_record: ReferenceEvidence,
    ) -> ComparisonContext:
        questioned_extractions = await self._extractions(questioned.id)
        reference_extractions = await self._extractions(reference.id)
        return ComparisonContext(
            case_id=questioned.case_id,
            questioned_evidence_id=questioned.id,
            reference_evidence_id=reference.id,
            questioned_filename=questioned.original_filename,
            reference_filename=reference.original_filename,
            questioned_mime_type=questioned.mime_type,
            reference_mime_type=reference.mime_type,
            questioned_storage_key=questioned.storage_key,
            reference_storage_key=reference.storage_key,
            questioned_sha256=questioned.sha256_hash,
            reference_sha256=reference_record.reference_hash,
            questioned_classification=await self._classification(questioned),
            reference_classification=await self._classification(reference),
            storage=self.storage,
            settings=self.settings,
            questioned_extractions=questioned_extractions,
            reference_extractions=reference_extractions,
            questioned_metadata=questioned.metadata_json,
            reference_metadata={
                **reference.metadata_json,
                **reference_record.metadata_json,
            },
        )

    async def _extractions(self, evidence_id: UUID) -> tuple[dict[str, object], ...]:
        records, _ = await self.extraction_repository.list_for_evidence(
            evidence_id,
            extraction_type=None,
            limit=500,
            offset=0,
        )
        return tuple(
            {
                "id": str(record.id),
                "extraction_type": record.extraction_type.value,
                "content": record.content,
                "page_number": record.page_number,
                "metadata": record.metadata_json,
            }
            for record in records
        )

    async def _classification(self, evidence: Evidence) -> EvidenceClassification:
        classification = EvidenceClassification.UNKNOWN
        raw_classification = evidence.metadata_json.get("classification")
        if isinstance(raw_classification, str):
            try:
                classification = EvidenceClassification(raw_classification)
            except ValueError:
                classification = EvidenceClassification.UNKNOWN
        if classification == EvidenceClassification.UNKNOWN:
            artifacts, _ = await self.artifact_repository.list_for_evidence(
                evidence.id,
                artifact_types=(ArtifactType.CLASSIFICATION,),
                limit=1,
                offset=0,
            )
            if artifacts:
                meta = artifacts[0].metadata_json
                raw = meta.get("classification")
                if isinstance(raw, str):
                    try:
                        classification = EvidenceClassification(raw)
                    except ValueError:
                        classification = EvidenceClassification.UNKNOWN
        return classification

    async def _persist_difference(
        self,
        comparison_run: ComparisonRun,
        evidence_id: UUID,
        item: DifferenceItem,
    ) -> Difference:
        difference = Difference(
            id=uuid4(),
            comparison_run_id=comparison_run.id,
            evidence_id=evidence_id,
            matcher=item.matcher,
            difference_type=item.difference_type,
            severity=item.severity,
            confidence=item.confidence,
            description=item.description,
            explanation=item.explanation,
            original_value=item.original_value,
            submitted_value=item.submitted_value,
            metadata_json=item.metadata,
        )
        await self.repository.add_difference(difference)
        for region in item.regions:
            await self.repository.add_region(
                DifferenceRegion(
                    id=uuid4(),
                    difference_id=difference.id,
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
        return difference

    async def _fail_job(
        self,
        job_id: UUID,
        comparison_run_id: UUID | None,
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
        if comparison_run_id is not None:
            run = await self.repository.get_run(comparison_run_id)
            if run is not None:
                run.status = ComparisonRunStatus.FAILED
                run.completed_at = datetime.now(UTC)
                run.error_code = error_code
                run.error_message = safe_message
        await self._record_event_in_transaction(
            evidence.id,
            CustodyEventType.COMPARISON_FAILED,
            "Reference comparison failed; original evidence preserved.",
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

    def _reference_response(
        self,
        reference: ReferenceEvidence,
        evidence: Evidence,
    ) -> ReferenceEvidenceResponse:
        return ReferenceEvidenceResponse(
            id=reference.id,
            case_id=reference.case_id,
            evidence_id=reference.evidence_id,
            label=reference.label,
            description=reference.description,
            reference_hash=reference.reference_hash,
            original_filename=evidence.original_filename,
            mime_type=evidence.mime_type,
            metadata=reference.metadata_json,
            created_at=reference.created_at,
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

    def _run_response(self, run: ComparisonRun) -> ComparisonRunResponse:
        return ComparisonRunResponse(
            id=run.id,
            evidence_id=run.evidence_id,
            reference_evidence_id=run.reference_evidence_id,
            reference_record_id=run.reference_record_id,
            status=run.status,
            engine_version=run.engine_version,
            differences_count=run.differences_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
        )

    def _difference_response(self, difference: Difference) -> DifferenceResponse:
        return DifferenceResponse(
            id=difference.id,
            comparison_run_id=difference.comparison_run_id,
            matcher=difference.matcher,
            difference_type=difference.difference_type,
            severity=difference.severity,
            confidence=difference.confidence,
            description=difference.description,
            explanation=difference.explanation,
            original_value=difference.original_value,
            submitted_value=difference.submitted_value,
            regions=regions_to_responses(
                tuple(self._region_box(region) for region in difference.regions)
            ),
            metadata=difference.metadata_json,
            created_at=difference.created_at,
        )

    @staticmethod
    def _region_box(region: DifferenceRegion) -> RegionBox:
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
