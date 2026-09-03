"""Service facade for investigation intelligence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.intelligence.engine import InvestigationIntelligenceEngine
from backend.app.intelligence.exceptions import IntelligenceNotFoundError
from backend.app.intelligence.repository import IntelligenceRepository
from backend.app.intelligence.schemas import (
    InvestigationSummaryListResponse,
    InvestigationSummaryResponse,
)
from backend.app.models.investigation_summary import InvestigationSummary


class InvestigationIntelligenceService:
    """Generate and retrieve investigation intelligence summaries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = IntelligenceRepository(session)
        self.engine = InvestigationIntelligenceEngine(session)

    def _to_response(
        self, row: InvestigationSummary,
    ) -> InvestigationSummaryResponse:
        return InvestigationSummaryResponse(
            id=row.id,
            case_id=row.case_id,
            generated_at=row.generated_at,
            overall_risk=row.overall_risk,
            overall_confidence=row.overall_confidence,
            overview=row.overview_json,
            key_findings=row.key_findings_json,
            timeline_summary=row.timeline_summary_json,
            correlation_summary=row.correlation_summary_json,
            ai_summary=row.ai_summary_json,
            recommendations=row.recommendations_json,
            provenance=row.provenance_json,
            narrative=row.narrative_json,
            engine_version=row.engine_version,
            policy_version=row.policy_version,
        )

    async def generate(self, case_id: UUID) -> InvestigationSummaryResponse:
        case = await self.repository.get_case(case_id)
        if case is None:
            raise ResourceNotFoundError("The case was not found.")
        snapshot = self.engine.normalize(await self.engine.collect(case))
        payload = self.engine.build(snapshot)
        row = self.engine.to_orm(case_id=case_id, payload=payload)
        await self.repository.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return self._to_response(row)

    async def list_summaries(
        self,
        case_id: UUID,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> InvestigationSummaryListResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")
        rows, total = await self.repository.list_for_case(
            case_id, limit=limit, offset=offset,
        )
        return InvestigationSummaryListResponse(
            items=[self._to_response(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_latest(self, case_id: UUID) -> InvestigationSummaryResponse:
        if await self.repository.get_case(case_id) is None:
            raise ResourceNotFoundError("The case was not found.")
        row = await self.repository.get_latest(case_id)
        if row is None:
            raise IntelligenceNotFoundError(
                "No investigation summary exists for this case.",
            )
        return self._to_response(row)

    async def get_summary(
        self, summary_id: UUID,
    ) -> InvestigationSummaryResponse:
        row = await self.repository.get(summary_id)
        if row is None:
            raise IntelligenceNotFoundError(
                "The investigation summary was not found.",
            )
        return self._to_response(row)
