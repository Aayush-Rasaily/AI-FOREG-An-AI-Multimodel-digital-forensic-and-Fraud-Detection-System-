"""Case intelligence engine orchestration."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.case_intelligence.aggregation import collect_case_evidence
from backend.app.case_intelligence.models import CaseIntelligenceResult
from backend.app.case_intelligence.policy import synthesize_case
from backend.app.models.case import Case


class CaseIntelligenceEngine:
    """Orchestrate case-level synthesis using Phase 6F fusion results."""

    async def analyze(
        self,
        session: AsyncSession,
        case: Case,
    ) -> CaseIntelligenceResult:
        participations = await collect_case_evidence(session, case.id)
        return await synthesize_case(
            session=session,
            case_id=case.id,
            case_number=case.case_number,
            participations=participations,
        )
