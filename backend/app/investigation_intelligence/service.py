"""Service facade for Phase 9C investigation intelligence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.investigation_intelligence.engine import (
    InvestigationIntelligenceEngine,
)
from backend.app.investigation_intelligence.exceptions import (
    IntelligenceRunNotFoundError,
)
from backend.app.investigation_intelligence.models import (
    CoverageMetrics,
    IntelligenceResult,
    RunStatus,
)
from backend.app.investigation_intelligence.policy import (
    II_ENGINE_VERSION,
    II_POLICY_VERSION,
)
from backend.app.investigation_intelligence.provenance import provenance_to_dict
from backend.app.investigation_intelligence.repository import (
    InvestigationIntelligenceRepository,
)
from backend.app.investigation_intelligence.schemas import (
    CoverageMetricsResponse,
    EvidenceGapListResponse,
    EvidenceGapResponse,
    HypothesisListResponse,
    HypothesisResponse,
    IntelligencePreviewResponse,
    IntelligenceRunResponse,
    InvestigationSummaryResponse,
    RecommendationListResponse,
    RecommendationResponse,
)
from backend.app.models.investigation_intelligence import (
    EvidenceGapRecordRow,
    InvestigationHypothesis,
    InvestigationIntelligenceRun,
    InvestigationRecommendation,
)


class InvestigationIntelligenceEngineService:
    """Analyze cases into hypotheses, gaps, and recommendations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InvestigationIntelligenceRepository(session)
        self.engine = InvestigationIntelligenceEngine(session)

    def _coverage_response(
        self, coverage: CoverageMetrics | dict,
    ) -> CoverageMetricsResponse:
        if isinstance(coverage, CoverageMetrics):
            data = coverage
            return CoverageMetricsResponse(
                evidence_total=data.evidence_total,
                evidence_analyzed=data.evidence_analyzed,
                evidence_pending=data.evidence_pending,
                timeline_coverage=data.timeline_coverage,
                knowledge_graph_coverage=data.knowledge_graph_coverage,
                correlation_coverage=data.correlation_coverage,
                fusion_coverage=data.fusion_coverage,
                ai_coverage=data.ai_coverage,
                metadata_completeness=data.metadata_completeness,
                chain_of_custody_completeness=(
                    data.chain_of_custody_completeness
                ),
                overall_completeness=data.overall_completeness,
                open_conflicts=data.open_conflicts,
            )
        return CoverageMetricsResponse(**dict(coverage))

    def _hypothesis_response(
        self,
        row: InvestigationHypothesis | None = None,
        *,
        draft: HypothesisResponse | None = None,
    ) -> HypothesisResponse:
        if draft is not None:
            return draft
        assert row is not None
        return HypothesisResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            hypothesis_key=row.hypothesis_key,
            hypothesis_type=row.hypothesis_type,
            title=row.title,
            explanation=row.explanation,
            confidence=row.confidence,
            priority=row.priority,
            status=row.status,
            supporting_evidence_ids=list(
                row.supporting_evidence_ids_json or []
            ),
            contradicting_evidence_ids=list(
                row.contradicting_evidence_ids_json or []
            ),
            provenance=dict(row.provenance_json or {}),
            attributes=dict(row.attributes_json or {}),
        )

    def _gap_response(
        self,
        row: EvidenceGapRecordRow | None = None,
        *,
        draft: EvidenceGapResponse | None = None,
    ) -> EvidenceGapResponse:
        if draft is not None:
            return draft
        assert row is not None
        return EvidenceGapResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            gap_key=row.gap_key,
            gap_type=row.gap_type,
            severity=row.severity,
            reason=row.reason,
            recommended_action=row.recommended_action,
            affected_evidence_ids=list(row.affected_evidence_ids_json or []),
            provenance=dict(row.provenance_json or {}),
        )

    def _recommendation_response(
        self,
        row: InvestigationRecommendation | None = None,
        *,
        draft: RecommendationResponse | None = None,
    ) -> RecommendationResponse:
        if draft is not None:
            return draft
        assert row is not None
        return RecommendationResponse(
            id=row.id,
            run_id=row.run_id,
            case_id=row.case_id,
            recommendation_key=row.recommendation_key,
            code=row.code,
            action_text=row.action_text,
            priority=row.priority,
            related_hypothesis_keys=list(
                row.related_hypothesis_keys_json or []
            ),
            related_gap_keys=list(row.related_gap_keys_json or []),
            affected_evidence_ids=list(row.affected_evidence_ids_json or []),
            provenance=dict(row.provenance_json or {}),
        )

    def _result_to_drafts(
        self, case_id: UUID, result: IntelligenceResult,
    ) -> tuple[
        list[HypothesisResponse],
        list[EvidenceGapResponse],
        list[RecommendationResponse],
    ]:
        hypotheses = [
            HypothesisResponse(
                case_id=case_id,
                hypothesis_key=item.hypothesis_key,
                hypothesis_type=item.hypothesis_type.value,
                title=item.title,
                explanation=item.explanation,
                confidence=item.confidence,
                priority=item.priority.value,
                status=item.status.value,
                supporting_evidence_ids=item.supporting_evidence_ids,
                contradicting_evidence_ids=item.contradicting_evidence_ids,
                provenance=provenance_to_dict(item.provenance),
                attributes=item.attributes,
            )
            for item in result.hypotheses
        ]
        gaps = [
            EvidenceGapResponse(
                case_id=case_id,
                gap_key=item.gap_key,
                gap_type=item.gap_type.value,
                severity=item.severity.value,
                reason=item.reason,
                recommended_action=item.recommended_action.value,
                affected_evidence_ids=item.affected_evidence_ids,
                provenance=provenance_to_dict(item.provenance),
            )
            for item in result.gaps
        ]
        recommendations = [
            RecommendationResponse(
                case_id=case_id,
                recommendation_key=item.recommendation_key,
                code=item.code.value,
                action_text=item.action_text,
                priority=item.priority.value,
                related_hypothesis_keys=item.related_hypothesis_keys,
                related_gap_keys=item.related_gap_keys,
                affected_evidence_ids=item.affected_evidence_ids,
                provenance=provenance_to_dict(item.provenance),
            )
            for item in result.recommendations
        ]
        return hypotheses, gaps, recommendations

    def _run_response(
        self,
        run: InvestigationIntelligenceRun,
        *,
        hypotheses: list[HypothesisResponse] | None = None,
        gaps: list[EvidenceGapResponse] | None = None,
        recommendations: list[RecommendationResponse] | None = None,
    ) -> IntelligenceRunResponse:
        return IntelligenceRunResponse(
            id=run.id,
            case_id=run.case_id,
            status=run.status,
            investigation_score=run.investigation_score,
            overall_completeness=run.overall_completeness,
            hypothesis_count=run.hypothesis_count,
            gap_count=run.gap_count,
            recommendation_count=run.recommendation_count,
            open_conflict_count=run.open_conflict_count,
            coverage=self._coverage_response(run.coverage_json or {}),
            open_conflicts=list(run.open_conflicts_json or []),
            provenance=dict(run.provenance_json or {}),
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
            completed_at=run.completed_at,
            hypotheses=hypotheses or [],
            gaps=gaps or [],
            recommendations=recommendations or [],
            persisted=True,
        )

    async def _hydrate(
        self, run: InvestigationIntelligenceRun,
    ) -> IntelligenceRunResponse:
        hyp_rows = await self.repository.hypotheses_for_run(run.id)
        gap_rows = await self.repository.gaps_for_run(run.id)
        rec_rows = await self.repository.recommendations_for_run(run.id)
        return self._run_response(
            run,
            hypotheses=[self._hypothesis_response(row) for row in hyp_rows],
            gaps=[self._gap_response(row) for row in gap_rows],
            recommendations=[
                self._recommendation_response(row) for row in rec_rows
            ],
        )

    async def analyze(self, case_id: UUID) -> IntelligenceRunResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")

        result = await self.engine.analyze(case)
        run = InvestigationIntelligenceRun(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            investigation_score=result.investigation_score,
            overall_completeness=result.coverage.overall_completeness,
            hypothesis_count=len(result.hypotheses),
            gap_count=len(result.gaps),
            recommendation_count=len(result.recommendations),
            open_conflict_count=len(result.open_conflicts),
            coverage_json=self._coverage_response(result.coverage).model_dump(),
            open_conflicts_json=result.open_conflicts,
            provenance_json=result.provenance,
            engine_version=II_ENGINE_VERSION,
            policy_version=II_POLICY_VERSION,
            completed_at=datetime.now(UTC),
        )
        await self.repository.add_run(run)

        hyp_rows = [
            InvestigationHypothesis(
                run_id=run.id,
                case_id=case_id,
                hypothesis_key=item.hypothesis_key,
                hypothesis_type=item.hypothesis_type.value,
                title=item.title,
                explanation=item.explanation,
                confidence=item.confidence,
                priority=item.priority.value,
                status=item.status.value,
                supporting_evidence_ids_json=item.supporting_evidence_ids,
                contradicting_evidence_ids_json=(
                    item.contradicting_evidence_ids
                ),
                provenance_json=provenance_to_dict(item.provenance),
                attributes_json=item.attributes,
            )
            for item in result.hypotheses
        ]
        gap_rows = [
            EvidenceGapRecordRow(
                run_id=run.id,
                case_id=case_id,
                gap_key=item.gap_key,
                gap_type=item.gap_type.value,
                severity=item.severity.value,
                reason=item.reason,
                recommended_action=item.recommended_action.value,
                affected_evidence_ids_json=item.affected_evidence_ids,
                provenance_json=provenance_to_dict(item.provenance),
            )
            for item in result.gaps
        ]
        rec_rows = [
            InvestigationRecommendation(
                run_id=run.id,
                case_id=case_id,
                recommendation_key=item.recommendation_key,
                code=item.code.value,
                action_text=item.action_text,
                priority=item.priority.value,
                related_hypothesis_keys_json=item.related_hypothesis_keys,
                related_gap_keys_json=item.related_gap_keys,
                affected_evidence_ids_json=item.affected_evidence_ids,
                provenance_json=provenance_to_dict(item.provenance),
            )
            for item in result.recommendations
        ]
        await self.repository.add_hypotheses(hyp_rows)
        await self.repository.add_gaps(gap_rows)
        await self.repository.add_recommendations(rec_rows)
        await self.session.commit()
        await self.session.refresh(run)
        return await self._hydrate(run)

    async def preview(self, case_id: UUID) -> IntelligencePreviewResponse:
        case = await self.engine.load_case(case_id)
        if case is None:
            raise ResourceNotFoundError("Case not found.")
        result = await self.engine.analyze(case)
        hypotheses, gaps, recommendations = self._result_to_drafts(
            case_id, result,
        )
        return IntelligencePreviewResponse(
            case_id=case_id,
            status=RunStatus.SUCCEEDED.value,
            investigation_score=result.investigation_score,
            overall_completeness=result.coverage.overall_completeness,
            hypothesis_count=len(hypotheses),
            gap_count=len(gaps),
            recommendation_count=len(recommendations),
            open_conflict_count=len(result.open_conflicts),
            coverage=self._coverage_response(result.coverage),
            open_conflicts=result.open_conflicts,
            provenance=result.provenance,
            engine_version=II_ENGINE_VERSION,
            policy_version=II_POLICY_VERSION,
            hypotheses=hypotheses,
            gaps=gaps,
            recommendations=recommendations,
            persisted=False,
        )

    async def get_latest(self, case_id: UUID) -> IntelligenceRunResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            raise IntelligenceRunNotFoundError(
                "No investigation intelligence run for this case."
            )
        return await self._hydrate(run)

    async def get_run(self, run_id: UUID) -> IntelligenceRunResponse:
        run = await self.repository.get_run(run_id)
        if run is None:
            raise IntelligenceRunNotFoundError(
                "Investigation intelligence run not found."
            )
        return await self._hydrate(run)

    async def list_hypotheses(
        self, case_id: UUID, *, limit: int = 100, offset: int = 0,
    ) -> HypothesisListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return HypothesisListResponse(items=[], total=0)
        rows, total = await self.repository.list_hypotheses(
            case_id, run_id=run.id, limit=limit, offset=offset,
        )
        return HypothesisListResponse(
            items=[self._hypothesis_response(row) for row in rows],
            total=total,
        )

    async def list_gaps(
        self, case_id: UUID, *, limit: int = 100, offset: int = 0,
    ) -> EvidenceGapListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return EvidenceGapListResponse(items=[], total=0)
        rows, total = await self.repository.list_gaps(
            case_id, run_id=run.id, limit=limit, offset=offset,
        )
        return EvidenceGapListResponse(
            items=[self._gap_response(row) for row in rows],
            total=total,
        )

    async def list_recommendations(
        self, case_id: UUID, *, limit: int = 100, offset: int = 0,
    ) -> RecommendationListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            return RecommendationListResponse(items=[], total=0)
        rows, total = await self.repository.list_recommendations(
            case_id, run_id=run.id, limit=limit, offset=offset,
        )
        return RecommendationListResponse(
            items=[self._recommendation_response(row) for row in rows],
            total=total,
        )

    async def investigation_summary(
        self, case_id: UUID,
    ) -> InvestigationSummaryResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("Case not found.")
        run = await self.repository.get_latest_run(case_id)
        if run is None:
            # Live preview summary without persistence
            preview = await self.preview(case_id)
            return InvestigationSummaryResponse(
                case_id=case_id,
                run_id=None,
                investigation_score=preview.investigation_score,
                overall_completeness=preview.overall_completeness,
                coverage=preview.coverage,
                top_hypotheses=preview.hypotheses[:5],
                critical_gaps=[
                    gap
                    for gap in preview.gaps
                    if gap.severity == "HIGH"
                ][:5],
                top_recommendations=preview.recommendations[:5],
                open_conflicts=preview.open_conflicts,
                engine_version=preview.engine_version,
                policy_version=preview.policy_version,
            )
        hydrated = await self._hydrate(run)
        return InvestigationSummaryResponse(
            case_id=case_id,
            run_id=run.id,
            investigation_score=hydrated.investigation_score,
            overall_completeness=hydrated.overall_completeness,
            coverage=hydrated.coverage,
            top_hypotheses=hydrated.hypotheses[:5],
            critical_gaps=[
                gap for gap in hydrated.gaps if gap.severity == "HIGH"
            ][:5],
            top_recommendations=hydrated.recommendations[:5],
            open_conflicts=hydrated.open_conflicts,
            engine_version=hydrated.engine_version,
            policy_version=hydrated.policy_version,
        )
