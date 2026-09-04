"""Persistence repository for investigation intelligence runs."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.investigation_intelligence import (
    EvidenceGapRecordRow,
    InvestigationHypothesis,
    InvestigationIntelligenceRun,
    InvestigationRecommendation,
)


class InvestigationIntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def add_run(
        self, run: InvestigationIntelligenceRun,
    ) -> InvestigationIntelligenceRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_hypotheses(
        self, rows: list[InvestigationHypothesis],
    ) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_gaps(self, rows: list[EvidenceGapRecordRow]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_recommendations(
        self, rows: list[InvestigationRecommendation],
    ) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def get_run(
        self, run_id: UUID,
    ) -> InvestigationIntelligenceRun | None:
        return await self.session.get(InvestigationIntelligenceRun, run_id)

    async def get_latest_run(
        self, case_id: UUID,
    ) -> InvestigationIntelligenceRun | None:
        result = await self.session.execute(
            select(InvestigationIntelligenceRun)
            .where(InvestigationIntelligenceRun.case_id == case_id)
            .order_by(InvestigationIntelligenceRun.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def list_hypotheses(
        self,
        case_id: UUID,
        *,
        run_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[InvestigationHypothesis], int]:
        filters = [InvestigationHypothesis.case_id == case_id]
        if run_id is not None:
            filters.append(InvestigationHypothesis.run_id == run_id)
        total = await self.session.scalar(
            select(func.count()).select_from(InvestigationHypothesis).where(
                *filters
            )
        )
        result = await self.session.execute(
            select(InvestigationHypothesis)
            .where(*filters)
            .order_by(
                InvestigationHypothesis.priority.asc(),
                InvestigationHypothesis.confidence.desc(),
                InvestigationHypothesis.hypothesis_key.asc(),
            )
            .limit(limit)
            .offset(offset)
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.priority, 9),
                -item.confidence,
                item.hypothesis_key,
            )
        )
        return rows, int(total or 0)

    async def list_gaps(
        self,
        case_id: UUID,
        *,
        run_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[EvidenceGapRecordRow], int]:
        filters = [EvidenceGapRecordRow.case_id == case_id]
        if run_id is not None:
            filters.append(EvidenceGapRecordRow.run_id == run_id)
        total = await self.session.scalar(
            select(func.count()).select_from(EvidenceGapRecordRow).where(
                *filters
            )
        )
        result = await self.session.execute(
            select(EvidenceGapRecordRow)
            .where(*filters)
            .limit(limit)
            .offset(offset)
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.severity, 9),
                item.gap_type,
                item.gap_key,
            )
        )
        return rows, int(total or 0)

    async def list_recommendations(
        self,
        case_id: UUID,
        *,
        run_id: UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[InvestigationRecommendation], int]:
        filters = [InvestigationRecommendation.case_id == case_id]
        if run_id is not None:
            filters.append(InvestigationRecommendation.run_id == run_id)
        total = await self.session.scalar(
            select(func.count())
            .select_from(InvestigationRecommendation)
            .where(*filters)
        )
        result = await self.session.execute(
            select(InvestigationRecommendation)
            .where(*filters)
            .limit(limit)
            .offset(offset)
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.priority, 9),
                item.code,
                item.recommendation_key,
            )
        )
        return rows, int(total or 0)

    async def hypotheses_for_run(
        self, run_id: UUID,
    ) -> list[InvestigationHypothesis]:
        result = await self.session.execute(
            select(InvestigationHypothesis)
            .where(InvestigationHypothesis.run_id == run_id)
            .order_by(
                InvestigationHypothesis.priority.asc(),
                InvestigationHypothesis.confidence.desc(),
                InvestigationHypothesis.hypothesis_key.asc(),
            )
        )
        return list(result.scalars().all())

    async def gaps_for_run(self, run_id: UUID) -> list[EvidenceGapRecordRow]:
        result = await self.session.execute(
            select(EvidenceGapRecordRow)
            .where(EvidenceGapRecordRow.run_id == run_id)
            .order_by(
                EvidenceGapRecordRow.severity.asc(),
                EvidenceGapRecordRow.gap_type.asc(),
                EvidenceGapRecordRow.gap_key.asc(),
            )
        )
        return list(result.scalars().all())

    async def recommendations_for_run(
        self, run_id: UUID,
    ) -> list[InvestigationRecommendation]:
        result = await self.session.execute(
            select(InvestigationRecommendation)
            .where(InvestigationRecommendation.run_id == run_id)
            .order_by(
                InvestigationRecommendation.priority.asc(),
                InvestigationRecommendation.code.asc(),
                InvestigationRecommendation.recommendation_key.asc(),
            )
        )
        return list(result.scalars().all())
