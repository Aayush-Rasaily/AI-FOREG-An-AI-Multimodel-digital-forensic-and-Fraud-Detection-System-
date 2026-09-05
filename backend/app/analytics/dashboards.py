"""Dashboard section assembly from metrics and raw aggregates."""

from __future__ import annotations

from typing import Any

from backend.app.analytics.models import MetricPoint
from backend.app.analytics.policy import DASHBOARD_SECTIONS


def build_sections(
    metrics: list[MetricPoint],
    raw: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    by_key = {item.key: item for item in metrics}
    overview_keys = [
        "cases_opened",
        "evidence_processed",
        "ai_analyses_completed",
        "integrity_alerts",
        "workflow_completion_pct",
        "storage_usage_bytes",
    ]
    sections: dict[str, dict[str, Any]] = {}
    for section in DASHBOARD_SECTIONS:
        if section == "overview":
            sections[section] = {
                "kpis": [
                    {
                        "key": key,
                        "label": by_key[key].label,
                        "value": by_key[key].value,
                        "unit": by_key[key].unit,
                    }
                    for key in overview_keys
                    if key in by_key
                ]
            }
        elif section == "cases":
            sections[section] = {
                "opened": raw["cases_opened"],
                "completed": raw["cases_completed"],
                "in_progress": raw["cases_in_progress"],
                "reports_generated": raw["reports_generated"],
            }
        elif section == "evidence":
            sections[section] = {
                "processed": raw["evidence_processed"],
                "timeline_events": raw["timeline_events"],
                "correlations": raw["correlation_counts"],
                "storage_usage_bytes": raw["storage_usage_bytes"],
                "avg_processing_seconds": raw["processing_duration_seconds_avg"],
            }
        elif section == "ai":
            sections[section] = {
                "analyses_completed": raw["ai_analyses_completed"],
                "breakdown": dict(raw.get("ai_breakdown") or {}),
                "fusion_runs": raw["fusion_runs"],
                "knowledge_graph_size": raw["knowledge_graph_size"],
                "knowledge_graph_runs": raw["knowledge_graph_runs"],
            }
        elif section == "workflow":
            sections[section] = {
                "workflow_completion_pct": raw["workflow_completion_pct"],
                "review_completion_pct": raw["review_completion_pct"],
                "queue_utilization": raw["queue_utilization"],
                "queue_active": raw["queue_active"],
                "queue_total": raw["queue_total"],
                "user_activity": raw["user_activity"],
                "user_count": raw["user_count"],
            }
        elif section == "integrity":
            sections[section] = {
                "alerts": raw["integrity_alerts"],
                "runs": raw["integrity_runs"],
            }
    return sections


def build_dashboard(
    sections: dict[str, dict[str, Any]],
    trends: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "title": "Investigation Analytics",
        "sections": sections,
        "trends": trends,
        "section_order": list(DASHBOARD_SECTIONS),
    }
