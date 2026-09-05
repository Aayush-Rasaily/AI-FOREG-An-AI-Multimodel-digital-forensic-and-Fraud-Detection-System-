"""Build metric points from raw aggregates."""

from __future__ import annotations

from typing import Any

from backend.app.analytics.models import MetricPoint
from backend.app.analytics.policy import METRIC_KEYS
from backend.app.analytics.provenance import metric_provenance

_LABELS: dict[str, tuple[str, str, str]] = {
    "cases_opened": ("Cases Opened", "count", "cases"),
    "cases_completed": ("Cases Completed", "count", "cases"),
    "cases_in_progress": ("Cases In Progress", "count", "cases"),
    "evidence_processed": ("Evidence Processed", "count", "evidence"),
    "ai_analyses_completed": ("AI Analyses Completed", "count", "ai"),
    "fusion_runs": ("Fusion Runs", "count", "ai"),
    "timeline_events": ("Timeline Events", "count", "evidence"),
    "correlation_counts": ("Correlation Counts", "count", "evidence"),
    "knowledge_graph_size": ("Knowledge Graph Size", "entities", "ai"),
    "workflow_completion_pct": (
        "Workflow Completion",
        "ratio",
        "workflow",
    ),
    "review_completion_pct": ("Review Completion", "ratio", "workflow"),
    "integrity_alerts": ("Integrity Alerts", "count", "integrity"),
    "processing_duration_seconds_avg": (
        "Avg Processing Duration",
        "seconds",
        "evidence",
    ),
    "reports_generated": ("Reports Generated", "count", "cases"),
    "user_activity": ("User Activity Events", "count", "overview"),
    "storage_usage_bytes": ("Storage Usage", "bytes", "evidence"),
    "queue_utilization": ("Queue Utilization", "ratio", "workflow"),
}


def build_metrics(raw: dict[str, Any]) -> list[MetricPoint]:
    points: list[MetricPoint] = []
    for key in METRIC_KEYS:
        label, unit, category = _LABELS[key]
        points.append(
            MetricPoint(
                key=key,
                label=label,
                value=float(raw.get(key) or 0),
                unit=unit,
                category=category,
                provenance=metric_provenance(
                    sources=[category, key],
                    detail="deterministic_aggregate",
                ),
            )
        )
    return points
