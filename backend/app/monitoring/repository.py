"""Persistence helpers for monitoring snapshots."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.monitoring import (
    AuditStatistics,
    MonitoringSnapshot,
    SystemHealthRecord,
)


class MonitoringRepository:
    """Repository for monitoring summary persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_snapshot(
        self, row: MonitoringSnapshot,
    ) -> MonitoringSnapshot:
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_audit_statistics(
        self, row: AuditStatistics,
    ) -> AuditStatistics:
        self.session.add(row)
        await self.session.flush()
        return row

    async def add_health_record(
        self, row: SystemHealthRecord,
    ) -> SystemHealthRecord:
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_latest_snapshot(self) -> MonitoringSnapshot | None:
        statement = (
            select(MonitoringSnapshot)
            .order_by(
                MonitoringSnapshot.generated_at.desc(),
                MonitoringSnapshot.id.desc(),
            )
            .limit(1)
        )
        return await self.session.scalar(statement)

    async def get_snapshot(
        self, snapshot_id: UUID,
    ) -> MonitoringSnapshot | None:
        return await self.session.get(MonitoringSnapshot, snapshot_id)
