"""Application service for multimodal fusion and AI jury."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    ConflictError,
    ProcessingError,
    ResourceNotFoundError,
)
from backend.app.domain.evidence import EvidenceStatus
from backend.app.domain.processing import ProcessingJobStatus, ProcessingJobType
from backend.app.fusion.engine import FusionEngine
from backend.app.fusion.exceptions import FusionAnalysisError
from backend.app.fusion.models import FusionRunStatus, Modality, ModalityAvailability
from backend.app.fusion.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.fusion.repository import FusionRepository
from backend.app.fusion.schemas import (
    AgreementMetricsResponse,
    FusionAnalysisDetailResponse,
    FusionAnalysisRunListResponse,
    FusionAnalysisRunResponse,
    FusionConflictResponse,
    FusionSignalsResponse,
    JuryAssessmentResponse,
    ModalityStatusResponse,
    NormalizedFindingResponse,
)
from backend.app.infrastructure.database.repositories.processing import (
    ProcessingJobRepository,
)
from backend.app.models.evidence import Evidence
from backend.app.models.fusion import (
    FusionAnalysisRun,
    FusionConflictRecord,
    JuryAssessmentRecord,
)
from backend.app.models.processing import ProcessingJob

logger = logging.getLogger(__name__)


class FusionService:
    """Queue and execute multimodal evidence fusion."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: FusionEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or FusionEngine()
        self.job_repository = ProcessingJobRepository(session)
        self.repository = FusionRepository(session)

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
                "Process and extract the evidence before multimodal fusion.",
            )
        active = await self.job_repository.get_active(
            evidence_id,
            ProcessingJobType.MULTIMODAL_FUSION,
        )
        if active is not None:
            raise ConflictError("An active multimodal fusion job already exists.")
        job = ProcessingJob(
            id=uuid4(),
            evidence_id=evidence_id,
            job_type=ProcessingJobType.MULTIMODAL_FUSION,
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
                "An active multimodal fusion job already exists.",
            ) from exc
        return self._job_response(job)

    async def run(self, job_id: UUID) -> None:
        job = await self.job_repository.get(job_id)
        if (
            job is None
            or job.status != ProcessingJobStatus.QUEUED
            or job.job_type != ProcessingJobType.MULTIMODAL_FUSION
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
        analysis_run = FusionAnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            processing_job_id=job.id,
            status=FusionRunStatus.RUNNING,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
            findings_count=0,
            conflicts_count=0,
            started_at=datetime.now(UTC),
            metadata_json={"source_sha256": evidence.sha256_hash},
            provenance_json={"source_sha256": evidence.sha256_hash},
            modality_status_json=[],
        )
        try:
            await self.repository.add_run(analysis_run)
            await self.session.commit()
            result = await self.engine.analyze(self.session, evidence)
            assessment = result.assessment
            if result.status != FusionRunStatus.SUCCEEDED or assessment is None:
                raise FusionAnalysisError(
                    result.error_code or "FUSION_FAILED",
                    result.error_message_safe or "Multimodal fusion failed.",
                )
            for jury_item in assessment.jury_assessments:
                await self.repository.add_jury_assessment(
                    JuryAssessmentRecord(
                        id=uuid4(),
                        analysis_run_id=analysis_run.id,
                        role=jury_item.role,
                        member_name=jury_item.member_name,
                        verdict=jury_item.verdict,
                        confidence=jury_item.confidence,
                        availability=jury_item.availability,
                        supporting_finding_ids=list(
                            jury_item.supporting_finding_ids
                        ),
                        contradictory_finding_ids=list(
                            jury_item.contradictory_finding_ids
                        ),
                        explanation=jury_item.explanation,
                        limitations=jury_item.limitations,
                        model_name=jury_item.model_name,
                        model_version=jury_item.model_version,
                    )
                )
            for conflict in assessment.conflicts:
                await self.repository.add_conflict(
                    FusionConflictRecord(
                        id=uuid4(),
                        analysis_run_id=analysis_run.id,
                        conflict_id=conflict.conflict_id,
                        conflict_type=conflict.conflict_type,
                        severity=conflict.severity,
                        involved_finding_ids=list(conflict.involved_finding_ids),
                        involved_modalities=[
                            modality.value for modality in conflict.involved_modalities
                        ],
                        explanation=conflict.explanation,
                        resolution_status=conflict.resolution_status,
                    )
                )
            analysis_run.status = FusionRunStatus.SUCCEEDED
            analysis_run.verdict = assessment.verdict
            analysis_run.risk_score = assessment.risk_score
            analysis_run.confidence = assessment.confidence
            analysis_run.findings_count = len(result.normalized_findings)
            analysis_run.conflicts_count = len(assessment.conflicts)
            analysis_run.completed_at = datetime.now(UTC)
            analysis_run.provenance_json = assessment.provenance
            analysis_run.modality_status_json = [
                {
                    "modality": status.modality.value,
                    "availability": status.availability.value,
                    "findings_count": status.findings_count,
                    "reason": status.reason,
                }
                for status in result.modality_statuses
            ]
            analysis_run.metadata_json = {
                **analysis_run.metadata_json,
                **result.metadata,
                "explanation": assessment.explanation,
                "limitations": assessment.limitations,
                "supporting_finding_ids": list(assessment.supporting_finding_ids),
                "contradictory_finding_ids": list(
                    assessment.contradictory_finding_ids
                ),
                "participating_modalities": [
                    modality.value for modality in assessment.participating_modalities
                ],
                "unavailable_modalities": [
                    modality.value for modality in assessment.unavailable_modalities
                ],
                "agreement": {
                    "modality_agreement_ratio": (
                        assessment.agreement.modality_agreement_ratio
                    ),
                    "jury_agreement_ratio": assessment.agreement.jury_agreement_ratio,
                    "supporting_modalities": assessment.agreement.supporting_modalities,
                    "contradictory_modalities": (
                        assessment.agreement.contradictory_modalities
                    ),
                    "unavailable_modalities": (
                        assessment.agreement.unavailable_modalities
                    ),
                    "inconclusive_modalities": (
                        assessment.agreement.inconclusive_modalities
                    ),
                    "confidence_spread": assessment.agreement.confidence_spread,
                    "jury_votes_available": assessment.agreement.jury_votes_available,
                    "jury_votes_total": assessment.agreement.jury_votes_total,
                },
            }
            evidence.metadata_json = {
                **evidence.metadata_json,
                "multimodal_fusion": {
                    "status": result.status.value,
                    "verdict": assessment.verdict.value,
                    "risk_score": assessment.risk_score,
                    "confidence": assessment.confidence,
                    "findings_count": len(result.normalized_findings),
                },
            }
            job.status = ProcessingJobStatus.SUCCEEDED
            job.completed_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "fusion_analysis_run_id": str(analysis_run.id),
                "verdict": assessment.verdict.value,
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if isinstance(exc, FusionAnalysisError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "FUSION_FAILED"
                safe_message = "The multimodal fusion pipeline failed."
            await self._fail_job(job_id, analysis_run.id, error_code, safe_message)
            logger.exception(
                "Multimodal fusion job failed",
                extra={"job_id": str(job_id), "evidence_id": str(evidence.id)},
            )

    async def list_runs(
        self,
        evidence_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> FusionAnalysisRunListResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        runs, total = await self.repository.list_runs_for_evidence(
            evidence_id,
            limit=limit,
            offset=offset,
        )
        return FusionAnalysisRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, evidence_id: UUID) -> FusionAnalysisDetailResponse:
        if await self.session.get(Evidence, evidence_id) is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        run = await self.repository.get_latest_for_evidence(evidence_id)
        if run is None:
            raise ResourceNotFoundError(
                "No multimodal fusion analysis exists for this evidence.",
            )
        return self._detail_response(run)

    async def get_run(self, analysis_id: UUID) -> FusionAnalysisDetailResponse:
        run = await self.repository.get_run_with_details(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested fusion analysis run was not found.",
            )
        return self._detail_response(run)

    async def list_jury(self, evidence_id: UUID) -> list[JuryAssessmentResponse]:
        run = await self.repository.get_latest_for_evidence(evidence_id)
        if run is None:
            raise ResourceNotFoundError(
                "No multimodal fusion analysis exists for this evidence.",
            )
        return [self._jury_response(item) for item in run.jury_assessments]

    async def list_conflicts(
        self,
        evidence_id: UUID,
    ) -> list[FusionConflictResponse]:
        run = await self.repository.get_latest_for_evidence(evidence_id)
        if run is None:
            raise ResourceNotFoundError(
                "No multimodal fusion analysis exists for this evidence.",
            )
        return [self._conflict_response(item) for item in run.conflicts]

    async def get_signals(self, evidence_id: UUID) -> FusionSignalsResponse:
        evidence = await self.session.get(Evidence, evidence_id)
        if evidence is None:
            raise ResourceNotFoundError("The requested evidence was not found.")
        result = await self.engine.analyze(self.session, evidence)
        return FusionSignalsResponse(
            evidence_id=evidence_id,
            findings=[
                NormalizedFindingResponse(
                    finding_id=item.finding_id,
                    evidence_id=item.evidence_id,
                    modality=item.modality,
                    analyzer=item.analyzer,
                    category=item.category,
                    finding_type=item.finding_type,
                    verdict=item.verdict.value,
                    confidence=item.confidence,
                    severity=item.severity,
                    description=item.description,
                    explanation=item.explanation,
                    source_reference=item.source_reference,
                    availability=item.availability,
                    model_name=item.model_name,
                    model_version=item.model_version,
                    temporal=item.temporal,
                    metadata=item.metadata,
                )
                for item in result.normalized_findings
            ],
            modality_status=[
                ModalityStatusResponse(
                    modality=status.modality,
                    availability=status.availability,
                    findings_count=status.findings_count,
                    reason=status.reason,
                )
                for status in result.modality_statuses
            ],
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
                run.status = FusionRunStatus.FAILED
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
    def _run_response(run: FusionAnalysisRun) -> FusionAnalysisRunResponse:
        return FusionAnalysisRunResponse(
            id=run.id,
            evidence_id=run.evidence_id,
            status=run.status,
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            verdict=run.verdict,
            risk_score=run.risk_score,
            confidence=run.confidence,
            findings_count=run.findings_count,
            conflicts_count=run.conflicts_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
            provenance=run.provenance_json,
        )

    def _detail_response(self, run: FusionAnalysisRun) -> FusionAnalysisDetailResponse:
        base = self._run_response(run)
        agreement_raw = run.metadata_json.get("agreement")
        agreement = None
        if isinstance(agreement_raw, dict):
            agreement = AgreementMetricsResponse(**agreement_raw)

        def _modality(value: str) -> Modality:
            return Modality(value)

        def _availability(value: str) -> ModalityAvailability:
            return ModalityAvailability(value)

        return FusionAnalysisDetailResponse(
            **base.model_dump(),
            modality_status=[
                ModalityStatusResponse(
                    modality=_modality(str(item["modality"])),
                    availability=_availability(str(item["availability"])),
                    findings_count=int(item.get("findings_count", 0)),
                    reason=item.get("reason"),
                )
                for item in run.modality_status_json
                if isinstance(item, dict)
            ],
            jury_assessments=[
                self._jury_response(item) for item in run.jury_assessments
            ],
            conflicts=[self._conflict_response(item) for item in run.conflicts],
            agreement=agreement,
            explanation=run.metadata_json.get("explanation"),
            limitations=run.metadata_json.get("limitations"),
            supporting_finding_ids=list(
                run.metadata_json.get("supporting_finding_ids", [])
            ),
            contradictory_finding_ids=list(
                run.metadata_json.get("contradictory_finding_ids", [])
            ),
            participating_modalities=[
                _modality(str(value))
                for value in run.metadata_json.get("participating_modalities", [])
            ],
            unavailable_modalities=[
                _modality(str(value))
                for value in run.metadata_json.get("unavailable_modalities", [])
            ],
        )

    @staticmethod
    def _jury_response(record: JuryAssessmentRecord) -> JuryAssessmentResponse:
        return JuryAssessmentResponse(
            id=record.id,
            role=record.role,
            member_name=record.member_name,
            verdict=record.verdict,
            confidence=record.confidence,
            availability=record.availability,
            supporting_finding_ids=list(record.supporting_finding_ids),
            contradictory_finding_ids=list(record.contradictory_finding_ids),
            explanation=record.explanation,
            limitations=record.limitations,
            model_name=record.model_name,
            model_version=record.model_version,
        )

    @staticmethod
    def _conflict_response(record: FusionConflictRecord) -> FusionConflictResponse:
        return FusionConflictResponse(
            id=record.id,
            conflict_id=record.conflict_id,
            conflict_type=record.conflict_type,
            severity=record.severity,
            involved_finding_ids=list(record.involved_finding_ids),
            involved_modalities=list(record.involved_modalities),
            explanation=record.explanation,
            resolution_status=record.resolution_status,
        )
