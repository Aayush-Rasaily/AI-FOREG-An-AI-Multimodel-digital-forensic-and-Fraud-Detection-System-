"""Raw count aggregation from persisted tables (read-only)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.domain.case import CaseStatus
from backend.app.models.audio_ai import AudioAnalysisRun
from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case
from backend.app.models.case_review import CaseReviewRun
from backend.app.models.correlation import EvidenceCorrelationRecord
from backend.app.models.decision_support import DecisionSupportRun
from backend.app.models.document_ai import DocumentAnalysisRun
from backend.app.models.evidence import Evidence
from backend.app.models.forensic_report import ForensicReport
from backend.app.models.fusion import FusionAnalysisRun
from backend.app.models.image_ai import ImageAnalysisRun
from backend.app.models.integrity import IntegrityAlert, IntegrityMonitorRun
from backend.app.models.knowledge_graph import GraphEntity, KnowledgeGraphRun
from backend.app.models.processing import ProcessingJob
from backend.app.models.timeline import TimelineEventRecord
from backend.app.models.user import User
from backend.app.models.video_ai import VideoAnalysisRun


async def _scalar(session: AsyncSession, stmt: Any) -> int:
    value = await session.scalar(stmt)
    return int(value or 0)


async def collect_raw_counts(session: AsyncSession) -> dict[str, Any]:
    """Return deterministic scalar aggregates from existing tables."""

    cases_opened = await _scalar(session, select(func.count()).select_from(Case))
    cases_completed = await _scalar(
        session,
        select(func.count())
        .select_from(Case)
        .where(Case.status.in_([CaseStatus.COMPLETED, CaseStatus.ARCHIVED])),
    )
    cases_in_progress = await _scalar(
        session,
        select(func.count())
        .select_from(Case)
        .where(
            Case.status.in_(
                [CaseStatus.OPEN, CaseStatus.IN_PROGRESS, CaseStatus.ON_HOLD]
            )
        ),
    )
    evidence_processed = await _scalar(
        session, select(func.count()).select_from(Evidence)
    )
    storage_usage = await session.scalar(
        select(func.coalesce(func.sum(Evidence.file_size), 0))
    )
    storage_usage_bytes = int(storage_usage or 0)

    ai_image = await _scalar(
        session, select(func.count()).select_from(ImageAnalysisRun)
    )
    ai_doc = await _scalar(
        session, select(func.count()).select_from(DocumentAnalysisRun)
    )
    ai_video = await _scalar(
        session, select(func.count()).select_from(VideoAnalysisRun)
    )
    ai_audio = await _scalar(
        session, select(func.count()).select_from(AudioAnalysisRun)
    )
    ai_analyses_completed = ai_image + ai_doc + ai_video + ai_audio

    fusion_runs = await _scalar(
        session, select(func.count()).select_from(FusionAnalysisRun)
    )
    timeline_events = await _scalar(
        session, select(func.count()).select_from(TimelineEventRecord)
    )
    correlation_counts = await _scalar(
        session, select(func.count()).select_from(EvidenceCorrelationRecord)
    )
    kg_entities = await _scalar(session, select(func.count()).select_from(GraphEntity))
    kg_runs = await _scalar(
        session, select(func.count()).select_from(KnowledgeGraphRun)
    )
    knowledge_graph_size = kg_entities

    # Workflow completion: average of latest decision-support metrics
    ds_result = await session.execute(
        select(DecisionSupportRun.metrics_json).order_by(
            DecisionSupportRun.created_at.desc()
        )
    )
    ds_rows = list(ds_result.scalars().all())
    if ds_rows:
        completions = [
            float(dict(row or {}).get("workflow_completion") or 0)
            for row in ds_rows[:50]
        ]
        workflow_completion_pct = round(sum(completions) / len(completions), 4)
    else:
        workflow_completion_pct = 0.0

    cr_result = await session.execute(
        select(CaseReviewRun.metrics_json).order_by(CaseReviewRun.created_at.desc())
    )
    cr_rows = list(cr_result.scalars().all())
    if cr_rows:
        reviews = [
            float(dict(row or {}).get("review_completion_pct") or 0)
            for row in cr_rows[:50]
        ]
        review_completion_pct = round(sum(reviews) / len(reviews), 4)
    else:
        review_completion_pct = 0.0

    integrity_alerts = await _scalar(
        session, select(func.count()).select_from(IntegrityAlert)
    )
    integrity_runs = await _scalar(
        session, select(func.count()).select_from(IntegrityMonitorRun)
    )

    # Processing duration average for completed jobs
    duration_expr = case(
        (
            ProcessingJob.completed_at.is_not(None),
            func.extract(
                "epoch",
                ProcessingJob.completed_at - ProcessingJob.created_at,
            ),
        ),
        else_=None,
    )
    avg_duration = await session.scalar(
        select(func.avg(duration_expr)).where(ProcessingJob.completed_at.is_not(None))
    )
    processing_duration_seconds_avg = round(float(avg_duration or 0), 4)

    queue_active = await _scalar(
        session,
        select(func.count())
        .select_from(ProcessingJob)
        .where(ProcessingJob.status.in_(["QUEUED", "RUNNING"])),
    )
    queue_total = await _scalar(
        session, select(func.count()).select_from(ProcessingJob)
    )
    queue_utilization = round(queue_active / queue_total, 4) if queue_total else 0.0

    reports_generated = await _scalar(
        session, select(func.count()).select_from(ForensicReport)
    )
    user_count = await _scalar(session, select(func.count()).select_from(User))
    audit_events = await _scalar(session, select(func.count()).select_from(AuditEvent))
    user_activity = audit_events

    return {
        "cases_opened": cases_opened,
        "cases_completed": cases_completed,
        "cases_in_progress": cases_in_progress,
        "evidence_processed": evidence_processed,
        "ai_analyses_completed": ai_analyses_completed,
        "ai_breakdown": {
            "image": ai_image,
            "document": ai_doc,
            "video": ai_video,
            "audio": ai_audio,
        },
        "fusion_runs": fusion_runs,
        "timeline_events": timeline_events,
        "correlation_counts": correlation_counts,
        "knowledge_graph_size": knowledge_graph_size,
        "knowledge_graph_runs": kg_runs,
        "workflow_completion_pct": workflow_completion_pct,
        "review_completion_pct": review_completion_pct,
        "integrity_alerts": integrity_alerts,
        "integrity_runs": integrity_runs,
        "processing_duration_seconds_avg": processing_duration_seconds_avg,
        "reports_generated": reports_generated,
        "user_activity": user_activity,
        "user_count": user_count,
        "storage_usage_bytes": storage_usage_bytes,
        "queue_utilization": queue_utilization,
        "queue_active": queue_active,
        "queue_total": queue_total,
    }
