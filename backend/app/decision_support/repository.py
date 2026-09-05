"""Persistence repository for decision support."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.decision_support import (
    DecisionSupportDecision,
    DecisionSupportReviewItem,
    DecisionSupportRun,
    DecisionSupportTask,
)


class DecisionSupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def add_run(self, run: DecisionSupportRun) -> DecisionSupportRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_tasks(self, rows: list[DecisionSupportTask]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_reviews(self, rows: list[DecisionSupportReviewItem]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_decision(
        self, row: DecisionSupportDecision,
    ) -> DecisionSupportDecision:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_run(self, run_id: UUID) -> DecisionSupportRun | None:
        return await self.session.get(DecisionSupportRun, run_id)

    async def get_latest_run(
        self, case_id: UUID,
    ) -> DecisionSupportRun | None:
        result = await self.session.execute(
            select(DecisionSupportRun)
            .where(DecisionSupportRun.case_id == case_id)
            .order_by(DecisionSupportRun.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def get_task(self, task_id: UUID) -> DecisionSupportTask | None:
        return await self.session.get(DecisionSupportTask, task_id)

    async def tasks_for_run(
        self, run_id: UUID,
    ) -> list[DecisionSupportTask]:
        result = await self.session.execute(
            select(DecisionSupportTask).where(
                DecisionSupportTask.run_id == run_id
            )
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.priority, 9),
                -item.priority_score,
                item.stage,
                item.task_key,
            )
        )
        return rows

    async def reviews_for_run(
        self, run_id: UUID,
    ) -> list[DecisionSupportReviewItem]:
        result = await self.session.execute(
            select(DecisionSupportReviewItem).where(
                DecisionSupportReviewItem.run_id == run_id
            )
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(item.priority, 9),
                -item.priority_score,
                item.evidence_id,
            )
        )
        return rows

    async def list_decisions(
        self, case_id: UUID, *, limit: int = 100, offset: int = 0,
    ) -> tuple[list[DecisionSupportDecision], int]:
        total = await self.session.scalar(
            select(func.count())
            .select_from(DecisionSupportDecision)
            .where(DecisionSupportDecision.case_id == case_id)
        )
        result = await self.session.execute(
            select(DecisionSupportDecision)
            .where(DecisionSupportDecision.case_id == case_id)
            .order_by(DecisionSupportDecision.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), int(total or 0)
