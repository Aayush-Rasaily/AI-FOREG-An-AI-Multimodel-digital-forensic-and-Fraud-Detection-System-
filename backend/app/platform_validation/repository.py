"""Persistence repository for platform validation."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.platform_validation import (
    PlatformValidationIssue,
    PlatformValidationResult,
    PlatformValidationRun,
)


class PlatformValidationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_run(self, run: PlatformValidationRun) -> PlatformValidationRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_results(self, rows: list[PlatformValidationResult]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_issues(self, rows: list[PlatformValidationIssue]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def get_run(self, run_id: UUID) -> PlatformValidationRun | None:
        return await self.session.get(PlatformValidationRun, run_id)

    async def get_latest_run(self) -> PlatformValidationRun | None:
        result = await self.session.execute(
            select(PlatformValidationRun)
            .order_by(PlatformValidationRun.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def list_runs(self, *, limit: int = 20) -> list[PlatformValidationRun]:
        result = await self.session.execute(
            select(PlatformValidationRun)
            .order_by(PlatformValidationRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def results_for_run(
        self,
        run_id: UUID,
    ) -> list[PlatformValidationResult]:
        result = await self.session.execute(
            select(PlatformValidationResult).where(
                PlatformValidationResult.run_id == run_id
            )
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda item: (item.category, item.check_key))
        return rows

    async def issues_for_run(
        self,
        run_id: UUID,
    ) -> list[PlatformValidationIssue]:
        result = await self.session.execute(
            select(PlatformValidationIssue).where(
                PlatformValidationIssue.run_id == run_id
            )
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda item: (item.severity, item.check_key))
        return rows
