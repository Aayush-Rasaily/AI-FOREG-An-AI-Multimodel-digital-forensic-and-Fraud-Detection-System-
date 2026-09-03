"""Combined system monitoring overview."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import Settings
from backend.app.system.health import build_health_snapshot
from backend.app.system.jobs import collect_job_summary
from backend.app.system.metrics import collect_metrics
from backend.app.system.storage import collect_storage_stats


async def collect_overview(
    session: AsyncSession,
    settings: Settings,
) -> dict[str, Any]:
    """Build a combined operational overview."""
    health = await build_health_snapshot(session, settings)
    metrics = await collect_metrics(session)
    jobs = await collect_job_summary(session)
    storage = collect_storage_stats(settings)
    return {
        "health": health,
        "metrics": metrics,
        "jobs": jobs,
        "storage": storage,
    }
