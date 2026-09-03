"""Background job monitoring across pipeline categories."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.correlation import CorrelationAnalysisRun
from backend.app.models.entity import EntityResolutionRun
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.processing import ProcessingJob
from backend.app.models.timeline import InvestigationTimeline
from backend.app.system.policy import JOB_CATEGORIES


def _status_counts(
    rows: list[tuple[str, int]],
) -> dict[str, int]:
    base = {
        "queued": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0,
    }
    mapping = {
        "QUEUED": "queued",
        "GENERATING": "running",
        "RUNNING": "running",
        "SUCCEEDED": "completed",
        "COMPLETED": "completed",
        "FAILED": "failed",
        "CANCELLED": "cancelled",
    }
    for status, count in rows:
        key = mapping.get(status)
        if key:
            base[key] += count
    return base


async def _aggregate_status(
    session: AsyncSession,
    model: type,
    status_column: Any,
) -> dict[str, int]:
    result = await session.execute(
        select(status_column, func.count())
        .group_by(status_column),
    )
    rows = result.all()
    pairs: list[tuple[str, int]] = [
        (str(row[0]), int(row[1])) for row in rows
    ]
    return _status_counts(pairs)


async def collect_job_summary(
    session: AsyncSession,
) -> dict[str, Any]:
    """Aggregate job counts across pipeline categories."""
    processing = await _aggregate_status(
        session, ProcessingJob, ProcessingJob.status,
    )
    fusion = await _aggregate_status(
        session, FusionAnalysisRun, FusionAnalysisRun.status,
    )
    timeline = await _aggregate_status(
        session, InvestigationTimeline, InvestigationTimeline.status,
    )
    correlation = await _aggregate_status(
        session,
        CorrelationAnalysisRun,
        CorrelationAnalysisRun.status,
    )
    entity = await _aggregate_status(
        session,
        EntityResolutionRun,
        EntityResolutionRun.status,
    )
    reports = await _aggregate_status(
        session, ForensicReport, ForensicReport.status,
    )

    categories = {
        "processing": processing,
        "extraction": processing,
        "ai": processing,
        "fusion": fusion,
        "timeline": timeline,
        "correlation": correlation,
        "entity_resolution": entity,
        "reports": reports,
    }

    totals = {
        "queued": 0,
        "running": 0,
        "completed": 0,
        "failed": 0,
        "cancelled": 0,
    }
    for cat in categories.values():
        for key in totals:
            totals[key] += cat.get(key, 0)

    active = totals["queued"] + totals["running"]
    queue_length = totals["queued"]

    return {
        "categories": categories,
        "totals": totals,
        "active_analyses": active,
        "queue_length": queue_length,
        "category_list": list(JOB_CATEGORIES),
    }
