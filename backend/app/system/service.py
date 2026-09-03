"""Application service for system administration."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.models.system import SystemDiagnosticsRun
from backend.app.system.diagnostics import run_diagnostics
from backend.app.system.health import build_health_snapshot
from backend.app.system.jobs import collect_job_summary
from backend.app.system.metrics import collect_metrics
from backend.app.system.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.system.repository import SystemRepository
from backend.app.system.schemas import (
    DiagnosticsResponse,
    DiagnosticsRunResponse,
    HealthSnapshotResponse,
    JobsSummaryResponse,
    MetricsResponse,
    StorageStatsResponse,
)
from backend.app.system.storage import collect_storage_stats


class SystemService:
    """Operational health, metrics, jobs, storage, diagnostics."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
    ) -> None:
        self.session = session
        self.settings = settings
        self.repository = SystemRepository(session)

    async def get_health(self) -> HealthSnapshotResponse:
        data = await build_health_snapshot(
            self.session, self.settings,
        )
        return HealthSnapshotResponse(**data)

    async def get_metrics(self) -> MetricsResponse:
        data = await collect_metrics(self.session)
        return MetricsResponse(**data)

    async def get_jobs(self) -> JobsSummaryResponse:
        data = await collect_job_summary(self.session)
        return JobsSummaryResponse(**data)

    async def get_storage(self) -> StorageStatsResponse:
        data = collect_storage_stats(self.settings)
        return StorageStatsResponse(**data)

    async def get_diagnostics(self) -> DiagnosticsResponse:
        data = await run_diagnostics(
            self.session, self.settings,
        )
        return DiagnosticsResponse(**data)

    async def run_diagnostics(self) -> DiagnosticsRunResponse:
        results = await run_diagnostics(
            self.session, self.settings,
        )
        run = SystemDiagnosticsRun(
            id=uuid4(),
            overall_status=results["overall_status"],
            results_json=results,
            engine_version=ENGINE_VERSION,
            policy_version=POLICY_VERSION,
            created_at=datetime.now(UTC),
        )
        await self.repository.add_run(run)
        await self.session.commit()
        return DiagnosticsRunResponse(
            id=run.id,
            overall_status=run.overall_status,
            results_json=run.results_json,
            engine_version=run.engine_version,
            policy_version=run.policy_version,
            created_at=run.created_at,
        )
