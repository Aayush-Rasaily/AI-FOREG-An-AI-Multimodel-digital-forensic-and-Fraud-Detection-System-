"""Application service for case-level forensic intelligence."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.application.services.hashing import HashService
from backend.app.application.services.storage import StorageService
from backend.app.case_intelligence.engine import CaseIntelligenceEngine
from backend.app.case_intelligence.exceptions import CaseIntelligenceError
from backend.app.case_intelligence.models import (
    CaseIntelligenceRunStatus,
    EvidenceCoverageStatus,
)
from backend.app.case_intelligence.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.case_intelligence.repository import CaseIntelligenceRepository
from backend.app.case_intelligence.schemas import (
    CaseConflictResponse,
    CaseIntelligenceDetailResponse,
    CaseIntelligenceRunListResponse,
    CaseIntelligenceRunResponse,
    CaseRelationshipResponse,
    EvidenceCoverageResponse,
    EvidenceParticipationResponse,
    TimelineEventResponse,
)
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError, ResourceNotFoundError
from backend.app.models.case import Case
from backend.app.models.case_intelligence import (
    CaseConflictRecord,
    CaseEvidenceParticipationRecord,
    CaseIntelligenceRun,
    CaseRelationshipRecord,
    CaseTimelineEventRecord,
)

logger = logging.getLogger(__name__)


class CaseIntelligenceService:
    """Queue and execute case-level forensic synthesis."""

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageService,
        hash_service: HashService,
        settings: Settings,
        engine: CaseIntelligenceEngine | None = None,
    ) -> None:
        self.session = session
        self.storage = storage
        self.hash_service = hash_service
        self.settings = settings
        self.engine = engine or CaseIntelligenceEngine()
        self.repository = CaseIntelligenceRepository(session)

    async def create_analysis(self, case_id: UUID) -> CaseIntelligenceRunResponse:
        case = await self.session.get(Case, case_id)
        if case is None:
            raise ResourceNotFoundError("The requested case was not found.")
        active = await self.repository.get_active_for_case(case_id)
        if active is not None:
            raise ConflictError("An active case intelligence analysis already exists.")
        run = CaseIntelligenceRun(
            id=uuid4(),
            case_id=case_id,
            status=CaseIntelligenceRunStatus.QUEUED,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
            evidence_count=0,
            conflicts_count=0,
            relationships_count=0,
            metadata_json={"case_number": case.case_number},
            provenance_json={"case_id": str(case_id), "case_number": case.case_number},
            coverage_json={},
        )
        try:
            await self.repository.add_run(run)
            await self.session.commit()
            await self.session.refresh(run)
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                "An active case intelligence analysis already exists.",
            ) from exc
        return self._run_response(run)

    async def run(self, analysis_id: UUID) -> None:
        run = await self.repository.get_run(analysis_id)
        if (
            run is None
            or run.status != CaseIntelligenceRunStatus.QUEUED
        ):
            return
        case = await self.session.get(Case, run.case_id)
        if case is None:
            await self._fail_run(
                analysis_id,
                "CASE_NOT_FOUND",
                "The case record is no longer available.",
            )
            return
        run.status = CaseIntelligenceRunStatus.RUNNING
        run.started_at = datetime.now(UTC)
        try:
            await self.session.commit()
            result = await self.engine.analyze(self.session, case)
            assessment = result.assessment
            if (
                result.status != CaseIntelligenceRunStatus.SUCCEEDED
                or assessment is None
            ):
                raise CaseIntelligenceError(
                    result.error_code or "CASE_INTELLIGENCE_FAILED",
                    result.error_message_safe or "Case intelligence synthesis failed.",
                )
            for participation in assessment.participations:
                await self.repository.add_participation(
                    CaseEvidenceParticipationRecord(
                        id=uuid4(),
                        analysis_run_id=run.id,
                        evidence_id=participation.evidence_id,
                        evidence_number=participation.evidence_number,
                        evidence_type=participation.evidence_type,
                        evidence_hash=participation.evidence_hash,
                        evidence_status=participation.evidence_status,
                        coverage_status=participation.coverage_status.value,
                        fusion_run_id=participation.fusion_run_id,
                        fusion_verdict=participation.fusion_verdict,
                        risk_score=participation.risk_score,
                        confidence=participation.confidence,
                        supporting_finding_ids=list(
                            participation.supporting_finding_ids
                        ),
                        contradictory_finding_ids=list(
                            participation.contradictory_finding_ids
                        ),
                        conflicts_count=participation.conflicts_count,
                        participating_modalities=list(
                            participation.participating_modalities
                        ),
                        unavailable_modalities=list(
                            participation.unavailable_modalities
                        ),
                        fusion_engine_version=participation.fusion_engine_version,
                        fusion_policy_version=participation.fusion_policy_version,
                        fusion_completed_at=participation.fusion_completed_at,
                        reason=participation.reason,
                    )
                )
            for relationship in assessment.relationships:
                await self.repository.add_relationship(
                    CaseRelationshipRecord(
                        id=uuid4(),
                        analysis_run_id=run.id,
                        relationship_id=relationship.relationship_id,
                        evidence_a_id=relationship.evidence_a_id,
                        evidence_b_id=relationship.evidence_b_id,
                        relationship_type=relationship.relationship_type,
                        confidence=relationship.confidence,
                        supporting_reason=relationship.supporting_reason,
                        source_reference=relationship.source_reference,
                        status=relationship.status,
                    )
                )
            for conflict in assessment.conflicts:
                await self.repository.add_conflict(
                    CaseConflictRecord(
                        id=uuid4(),
                        analysis_run_id=run.id,
                        conflict_id=conflict.conflict_id,
                        conflict_type=conflict.conflict_type,
                        severity=conflict.severity,
                        involved_evidence_ids=[
                            str(value) for value in conflict.involved_evidence_ids
                        ],
                        involved_finding_ids=list(conflict.involved_finding_ids),
                        explanation=conflict.explanation,
                        resolution_status=conflict.resolution_status,
                    )
                )
            for event in assessment.timeline:
                await self.repository.add_timeline_event(
                    CaseTimelineEventRecord(
                        id=uuid4(),
                        analysis_run_id=run.id,
                        event_id=event.event_id,
                        event_type=event.event_type,
                        timestamp=event.timestamp,
                        timestamp_known=event.timestamp_known,
                        evidence_id=event.evidence_id,
                        source_reference=event.source_reference,
                        description=event.description,
                        metadata_json=event.metadata,
                    )
                )
            run.status = CaseIntelligenceRunStatus.SUCCEEDED
            run.verdict = assessment.verdict
            run.risk_score = assessment.risk_score
            run.confidence = assessment.confidence
            run.evidence_count = len(assessment.participations)
            run.conflicts_count = len(assessment.conflicts)
            run.relationships_count = len(assessment.relationships)
            run.completed_at = datetime.now(UTC)
            run.provenance_json = assessment.provenance
            run.coverage_json = {
                "total_evidence": assessment.coverage.total_evidence,
                "analyzed": assessment.coverage.analyzed,
                "not_analyzed": assessment.coverage.not_analyzed,
                "inconclusive": assessment.coverage.inconclusive,
                "insufficient_evidence": assessment.coverage.insufficient_evidence,
                "unavailable": assessment.coverage.unavailable,
                "failed": assessment.coverage.failed,
                "supporting_evidence": assessment.coverage.supporting_evidence,
                "contradictory_evidence": assessment.coverage.contradictory_evidence,
                "open_conflicts": assessment.coverage.open_conflicts,
                "supported_modalities": list(
                    assessment.coverage.supported_modalities
                ),
            }
            run.metadata_json = {
                **run.metadata_json,
                **result.metadata,
                "explanation": assessment.explanation,
                "limitations": assessment.limitations,
                "supporting_evidence_ids": [
                    str(value) for value in assessment.supporting_evidence_ids
                ],
                "contradictory_evidence_ids": [
                    str(value) for value in assessment.contradictory_evidence_ids
                ],
            }
            await self.session.commit()
        except Exception as exc:
            await self.session.rollback()
            if isinstance(exc, CaseIntelligenceError):
                error_code = exc.code
                safe_message = exc.message
            else:
                error_code = "CASE_INTELLIGENCE_FAILED"
                safe_message = "The case intelligence pipeline failed."
            await self._fail_run(analysis_id, error_code, safe_message)
            logger.exception(
                "Case intelligence run failed",
                extra={"analysis_id": str(analysis_id), "case_id": str(run.case_id)},
            )

    async def list_runs(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> CaseIntelligenceRunListResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        runs, total = await self.repository.list_runs_for_case(
            case_id,
            limit=limit,
            offset=offset,
        )
        return CaseIntelligenceRunListResponse(
            items=[self._run_response(run) for run in runs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, case_id: UUID) -> CaseIntelligenceDetailResponse:
        if await self.session.get(Case, case_id) is None:
            raise ResourceNotFoundError("The requested case was not found.")
        run = await self.repository.get_latest_for_case(case_id)
        if run is None:
            raise ResourceNotFoundError(
                "No case intelligence analysis exists for this case.",
            )
        return self._detail_response(run)

    async def get_run(self, analysis_id: UUID) -> CaseIntelligenceDetailResponse:
        run = await self.repository.get_run_with_details(analysis_id)
        if run is None:
            raise ResourceNotFoundError(
                "The requested case intelligence run was not found.",
            )
        return self._detail_response(run)

    async def list_relationships(
        self,
        case_id: UUID,
    ) -> list[CaseRelationshipResponse]:
        run = await self.repository.get_latest_for_case(case_id)
        if run is None:
            raise ResourceNotFoundError(
                "No case intelligence analysis exists for this case.",
            )
        return [self._relationship_response(item) for item in run.relationships]

    async def list_conflicts(self, case_id: UUID) -> list[CaseConflictResponse]:
        run = await self.repository.get_latest_for_case(case_id)
        if run is None:
            raise ResourceNotFoundError(
                "No case intelligence analysis exists for this case.",
            )
        return [self._conflict_response(item) for item in run.conflicts]

    async def list_timeline(self, case_id: UUID) -> list[TimelineEventResponse]:
        run = await self.repository.get_latest_for_case(case_id)
        if run is None:
            raise ResourceNotFoundError(
                "No case intelligence analysis exists for this case.",
            )
        return [self._timeline_response(item) for item in run.timeline_events]

    async def _fail_run(
        self,
        analysis_id: UUID,
        error_code: str,
        message: str,
    ) -> None:
        run = await self.repository.get_run(analysis_id)
        if run is not None:
            run.status = CaseIntelligenceRunStatus.FAILED
            run.error_code = error_code
            run.error_message = message
            run.completed_at = datetime.now(UTC)
        await self.session.commit()

    @staticmethod
    def _run_response(run: CaseIntelligenceRun) -> CaseIntelligenceRunResponse:
        return CaseIntelligenceRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            verdict=run.verdict,
            risk_score=run.risk_score,
            confidence=run.confidence,
            evidence_count=run.evidence_count,
            conflicts_count=run.conflicts_count,
            relationships_count=run.relationships_count,
            created_at=run.created_at,
            started_at=run.started_at,
            completed_at=run.completed_at,
            error_code=run.error_code,
            error_message=run.error_message,
            metadata=run.metadata_json,
            provenance=run.provenance_json,
        )

    def _detail_response(
        self,
        run: CaseIntelligenceRun,
    ) -> CaseIntelligenceDetailResponse:
        base = self._run_response(run)
        coverage = EvidenceCoverageResponse(**run.coverage_json)
        return CaseIntelligenceDetailResponse(
            **base.model_dump(),
            coverage=coverage,
            participations=[
                EvidenceParticipationResponse(
                    evidence_id=item.evidence_id,
                    evidence_number=item.evidence_number,
                    evidence_type=item.evidence_type,
                    evidence_hash=item.evidence_hash,
                    evidence_status=item.evidence_status,
                    coverage_status=EvidenceCoverageStatus(item.coverage_status),
                    fusion_run_id=item.fusion_run_id,
                    fusion_verdict=item.fusion_verdict,
                    risk_score=item.risk_score,
                    confidence=item.confidence,
                    supporting_finding_ids=list(item.supporting_finding_ids),
                    contradictory_finding_ids=list(item.contradictory_finding_ids),
                    conflicts_count=item.conflicts_count,
                    participating_modalities=list(item.participating_modalities),
                    unavailable_modalities=list(item.unavailable_modalities),
                    fusion_engine_version=item.fusion_engine_version,
                    fusion_policy_version=item.fusion_policy_version,
                    fusion_completed_at=item.fusion_completed_at,
                    reason=item.reason,
                )
                for item in run.participations
            ],
            relationships=[
                self._relationship_response(item) for item in run.relationships
            ],
            conflicts=[self._conflict_response(item) for item in run.conflicts],
            timeline=[self._timeline_response(item) for item in run.timeline_events],
            explanation=run.metadata_json.get("explanation"),
            limitations=run.metadata_json.get("limitations"),
            supporting_evidence_ids=list(
                run.metadata_json.get("supporting_evidence_ids", [])
            ),
            contradictory_evidence_ids=list(
                run.metadata_json.get("contradictory_evidence_ids", [])
            ),
        )

    @staticmethod
    def _relationship_response(
        record: CaseRelationshipRecord,
    ) -> CaseRelationshipResponse:
        return CaseRelationshipResponse(
            id=record.id,
            relationship_id=record.relationship_id,
            evidence_a_id=record.evidence_a_id,
            evidence_b_id=record.evidence_b_id,
            relationship_type=record.relationship_type,
            confidence=record.confidence,
            supporting_reason=record.supporting_reason,
            source_reference=record.source_reference,
            status=record.status,
        )

    @staticmethod
    def _conflict_response(record: CaseConflictRecord) -> CaseConflictResponse:
        return CaseConflictResponse(
            id=record.id,
            conflict_id=record.conflict_id,
            conflict_type=record.conflict_type,
            severity=record.severity,
            involved_evidence_ids=list(record.involved_evidence_ids),
            involved_finding_ids=list(record.involved_finding_ids),
            explanation=record.explanation,
            resolution_status=record.resolution_status,
        )

    @staticmethod
    def _timeline_response(record: CaseTimelineEventRecord) -> TimelineEventResponse:
        return TimelineEventResponse(
            id=record.id,
            event_id=record.event_id,
            event_type=record.event_type,
            timestamp=record.timestamp,
            timestamp_known=record.timestamp_known,
            evidence_id=record.evidence_id,
            source_reference=record.source_reference,
            description=record.description,
            metadata=record.metadata_json,
        )
