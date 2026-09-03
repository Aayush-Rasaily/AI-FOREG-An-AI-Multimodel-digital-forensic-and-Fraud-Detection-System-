"""Deterministic system metrics collection."""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.processing import ProcessingJobStatus
from backend.app.models.ai import InferenceJob
from backend.app.models.case import Case
from backend.app.models.correlation import CorrelationAnalysisRun
from backend.app.models.entity import EntityResolutionRun
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.processing import ProcessingJob
from backend.app.models.timeline import InvestigationTimeline


async def _count(session: AsyncSession, model: type) -> int:
    result = await session.scalar(
        select(func.count()).select_from(model),
    )
    return int(result or 0)


async def collect_metrics(
    session: AsyncSession,
) -> dict[str, Any]:
    """Collect deterministic operational metrics."""
    evidence_count = await _count(session, Evidence)
    case_count = await _count(session, Case)
    report_count = await _count(session, ForensicReport)
    timeline_count = await _count(
        session, InvestigationTimeline,
    )
    fusion_count = await _count(session, FusionAnalysisRun)
    entity_count = await _count(
        session, EntityResolutionRun,
    )
    correlation_count = await _count(
        session, CorrelationAnalysisRun,
    )
    ai_count = await _count(session, InferenceJob)
    processing_count = await _count(session, ProcessingJob)

    failed_jobs = await session.scalar(
        select(func.count())
        .select_from(ProcessingJob)
        .where(
            ProcessingJob.status == ProcessingJobStatus.FAILED,
        ),
    )
    total_jobs = processing_count or 1
    failure_rate = round(
        int(failed_jobs or 0) / total_jobs, 4,
    )

    return {
        "evidence_count": evidence_count,
        "case_count": case_count,
        "report_count": report_count,
        "timeline_count": timeline_count,
        "fusion_run_count": fusion_count,
        "entity_graph_count": entity_count,
        "correlation_count": correlation_count,
        "ai_analysis_count": ai_count,
        "processing_job_count": processing_count,
        "average_processing_time_ms": None,
        "failure_rate": failure_rate,
        "storage_growth_bytes": None,
    }
