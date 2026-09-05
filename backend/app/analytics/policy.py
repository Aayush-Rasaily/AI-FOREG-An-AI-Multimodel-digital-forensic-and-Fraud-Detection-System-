"""Deterministic policy for Phase 9G analytics."""

from __future__ import annotations

AN_ENGINE_VERSION = "9g.1.0"
AN_POLICY_VERSION = "1.0"

METRIC_KEYS: tuple[str, ...] = (
    "cases_opened",
    "cases_completed",
    "cases_in_progress",
    "evidence_processed",
    "ai_analyses_completed",
    "fusion_runs",
    "timeline_events",
    "correlation_counts",
    "knowledge_graph_size",
    "workflow_completion_pct",
    "review_completion_pct",
    "integrity_alerts",
    "processing_duration_seconds_avg",
    "reports_generated",
    "user_activity",
    "storage_usage_bytes",
    "queue_utilization",
)

DASHBOARD_SECTIONS: tuple[str, ...] = (
    "overview",
    "cases",
    "evidence",
    "ai",
    "workflow",
    "integrity",
)

TREND_HISTORY_LIMIT = 20
