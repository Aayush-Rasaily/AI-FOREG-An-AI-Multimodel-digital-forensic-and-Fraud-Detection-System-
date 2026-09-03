"""Persistence helpers for investigation summaries."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.investigation_summary import InvestigationSummary


class IntelligenceRepository:
    """Repository for investigation summary persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def add(self, row: InvestigationSummary) -> InvestigationSummary:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get(self, summary_id: UUID) -> InvestigationSummary | None:
        return await self.session.get(InvestigationSummary, summary_id)

    async def get_latest(self, case_id: UUID) -> InvestigationSummary | None:
        statement = (
            select(InvestigationSummary)
            .where(InvestigationSummary.case_id == case_id)
            .order_by(
                InvestigationSummary.generated_at.desc(),
                InvestigationSummary.id.desc(),
            )
            .limit(1)
        )
        return await self.session.scalar(statement)

    async def list_for_case(
        self,
        case_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> tuple[list[InvestigationSummary], int]:
        filters = InvestigationSummary.case_id == case_id
        total = int(
            await self.session.scalar(
                select(func.count()).select_from(InvestigationSummary).where(filters)
            )
            or 0
        )
        statement = (
            select(InvestigationSummary)
            .where(filters)
            .order_by(
                InvestigationSummary.generated_at.desc(),
                InvestigationSummary.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        rows = list(await self.session.scalars(statement))
        return rows, total
