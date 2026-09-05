"""Persistence repository for integrity monitoring."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.case import Case
from backend.app.models.integrity import (
    IntegrityAlert,
    IntegrityCheck,
    IntegrityDriftRecord,
    IntegrityMonitorRun,
)


class IntegrityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_case(self, case_id: UUID) -> Case | None:
        return await self.session.get(Case, case_id)

    async def add_run(self, run: IntegrityMonitorRun) -> IntegrityMonitorRun:
        self.session.add(run)
        await self.session.flush()
        return run

    async def add_checks(self, rows: list[IntegrityCheck]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_alerts(self, rows: list[IntegrityAlert]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def add_drifts(self, rows: list[IntegrityDriftRecord]) -> None:
        self.session.add_all(rows)
        await self.session.flush()

    async def get_run(self, run_id: UUID) -> IntegrityMonitorRun | None:
        return await self.session.get(IntegrityMonitorRun, run_id)

    async def get_latest_run(self, case_id: UUID) -> IntegrityMonitorRun | None:
        result = await self.session.execute(
            select(IntegrityMonitorRun)
            .where(IntegrityMonitorRun.case_id == case_id)
            .order_by(IntegrityMonitorRun.created_at.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def checks_for_run(self, run_id: UUID) -> list[IntegrityCheck]:
        result = await self.session.execute(
            select(IntegrityCheck).where(IntegrityCheck.run_id == run_id)
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (item.check_code, item.evidence_id or "", item.check_key)
        )
        return rows

    async def alerts_for_run(self, run_id: UUID) -> list[IntegrityAlert]:
        result = await self.session.execute(
            select(IntegrityAlert).where(IntegrityAlert.run_id == run_id)
        )
        rows = list(result.scalars().all())
        rows.sort(
            key=lambda item: (item.severity, item.alert_code, item.evidence_id or "")
        )
        return rows

    async def drifts_for_run(self, run_id: UUID) -> list[IntegrityDriftRecord]:
        result = await self.session.execute(
            select(IntegrityDriftRecord).where(IntegrityDriftRecord.run_id == run_id)
        )
        rows = list(result.scalars().all())
        rows.sort(key=lambda item: (item.evidence_id, item.field_name, item.drift_key))
        return rows

    async def list_runs(
        self,
        case_id: UUID,
        *,
        limit: int = 50,
    ) -> list[IntegrityMonitorRun]:
        result = await self.session.execute(
            select(IntegrityMonitorRun)
            .where(IntegrityMonitorRun.case_id == case_id)
            .order_by(IntegrityMonitorRun.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
