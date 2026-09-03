"""System diagnostics persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.system import SystemDiagnosticsRun


class SystemRepository:
    """Database operations for system diagnostics runs."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_run(
        self, run_id: UUID,
    ) -> SystemDiagnosticsRun | None:
        return await self.session.get(
            SystemDiagnosticsRun, run_id,
        )

    async def get_latest(self) -> SystemDiagnosticsRun | None:
        result = await self.session.scalars(
            select(SystemDiagnosticsRun)
            .order_by(SystemDiagnosticsRun.created_at.desc())
            .limit(1),
        )
        return result.first()

    async def add_run(
        self, run: SystemDiagnosticsRun,
    ) -> SystemDiagnosticsRun:
        self.session.add(run)
        await self.session.flush()
        return run
