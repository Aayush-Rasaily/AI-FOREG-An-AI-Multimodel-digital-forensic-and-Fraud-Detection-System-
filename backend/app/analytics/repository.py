"""Persistence repository for analytics."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.analytics import (
    AnalyticsDashboard,
    AnalyticsMetric,
    AnalyticsRun,
    AnalyticsSnapshot,
)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_run(self, run: AnalyticsRun) -> AnalyticsRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_snapshot(self, row: AnalyticsSnapshot) -> None:
        self.session.add(row)
        await self.session.flush()

    async def add_metrics(self, rows: list[AnalyticsMetric]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_dashboard(self, row: AnalyticsDashboard) -> None:
        self.session.add(row)
        await self.session.flush()

    async def get_run(self, run_id: UUID) -> AnalyticsRun | None:
        return await self.session.get(AnalyticsRun, run_id)

    async def get_latest_run(self) -> AnalyticsRun | None:
        result = await self.session.execute(
            select(AnalyticsRun).order_by(AnalyticsRun.created_at.desc()).limit(1)
        )
        return result.scalars().first()

    async def get_snapshot_for_run(
        self,
        run_id: UUID,
    ) -> AnalyticsSnapshot | None:
        result = await self.session.execute(
            select(AnalyticsSnapshot)
            .where(AnalyticsSnapshot.run_id == run_id)
            .order_by(AnalyticsSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def metrics_for_run(self, run_id: UUID) -> list[AnalyticsMetric]:
        result = await self.session.execute(
            select(AnalyticsMetric).where(AnalyticsMetric.run_id == run_id)
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda item: (item.category, item.metric_key))
        return rows

    async def get_dashboard_for_run(
        self,
        run_id: UUID,
    ) -> AnalyticsDashboard | None:
        result = await self.session.execute(
            select(AnalyticsDashboard)
            .where(AnalyticsDashboard.run_id == run_id)
            .limit(1)
        )
        return result.scalars().first()

    async def list_recent_snapshots(
        self,
        *,
        limit: int = 20,
    ) -> list[AnalyticsSnapshot]:
        result = await self.session.execute(
            select(AnalyticsSnapshot)
            .order_by(AnalyticsSnapshot.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
