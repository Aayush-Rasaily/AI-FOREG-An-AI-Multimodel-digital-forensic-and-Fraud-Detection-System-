"""Monitoring engine: health assessment and dashboard aggregation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.monitoring.analytics import (
    collect_ai_metrics,
    collect_investigation_metrics,
    collect_kpis,
    collect_processing_metrics,
)
from backend.app.monitoring.audit import (
    collect_audit_events,
    find_inactive_cases,
    recent_activity,
    summarize_api_usage,
    summarize_user_activity,
)
from backend.app.monitoring.models import PlatformHealthStatus
from backend.app.monitoring.policy import (
    CRITICAL_FAILURE_RATE,
    CRITICAL_QUEUE_BACKLOG,
    DEGRADED_FAILURE_RATE,
    DEGRADED_QUEUE_BACKLOG,
    ENGINE_VERSION,
    POLICY_VERSION,
    WARNING_FAILURE_RATE,
    WARNING_QUEUE_BACKLOG,
)


def assess_health(
    *,
    processing: dict[str, Any],
    ai: dict[str, Any],
    api: dict[str, Any],
) -> dict[str, Any]:
    """Deterministically classify platform health from aggregate rates."""

    reasons: list[str] = []
    failure_rate = float(processing.get("failure_rate") or 0.0)
    ai_failures = int(ai.get("total_failures") or 0)
    ai_executions = sum(
        int(item.get("executions") or 0) for item in ai.get("modalities", [])
    )
    ai_failure_rate = (
        round(ai_failures / ai_executions, 4) if ai_executions else 0.0
    )
    backlog = int(processing.get("queued") or 0) + int(
        processing.get("running") or 0
    )
    api_error_codes = 0
    for code, count in (api.get("response_codes") or {}).items():
        try:
            if int(code) >= 500:
                api_error_codes += int(count)
        except (TypeError, ValueError):
            continue
    api_total = int(api.get("request_counts") or 0)
    api_failure_rate = (
        round(api_error_codes / api_total, 4) if api_total else 0.0
    )

    status = PlatformHealthStatus.HEALTHY
    peak_rate = max(failure_rate, ai_failure_rate, api_failure_rate)

    if (
        peak_rate >= CRITICAL_FAILURE_RATE
        or backlog >= CRITICAL_QUEUE_BACKLOG
    ):
        status = PlatformHealthStatus.CRITICAL
        reasons.append("Critical failure rate or queue backlog detected.")
    elif (
        peak_rate >= DEGRADED_FAILURE_RATE
        or backlog >= DEGRADED_QUEUE_BACKLOG
    ):
        status = PlatformHealthStatus.DEGRADED
        reasons.append("Elevated failure rate or queue backlog.")
    elif (
        peak_rate >= WARNING_FAILURE_RATE
        or backlog >= WARNING_QUEUE_BACKLOG
        or int(ai.get("total_unavailable") or 0) > 0
    ):
        status = PlatformHealthStatus.WARNING
        reasons.append("Warning thresholds exceeded.")
    else:
        reasons.append("All monitored indicators within healthy thresholds.")

    return {
        "status": status.value,
        "reasons": reasons,
        "signals": {
            "processing_failure_rate": failure_rate,
            "ai_failure_rate": ai_failure_rate,
            "api_failure_rate": api_failure_rate,
            "queue_backlog": backlog,
            "ai_unavailable": int(ai.get("total_unavailable") or 0),
            "detector_failures": ai_failures,
        },
        "assessed_at": datetime.now(UTC).isoformat(),
        "engine_version": ENGINE_VERSION,
        "policy_version": POLICY_VERSION,
    }


class MonitoringEngine:
    """Collect persisted metrics and produce operational intelligence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def compute(self) -> dict[str, Any]:
        """Build a full monitoring dashboard payload."""

        processing = await collect_processing_metrics(self.session)
        ai = await collect_ai_metrics(self.session)
        investigation = await collect_investigation_metrics(self.session)
        events = await collect_audit_events(self.session)
        activity = summarize_user_activity(events)
        api = summarize_api_usage(events)
        inactive = await find_inactive_cases(self.session)
        health = assess_health(processing=processing, ai=ai, api=api)
        kpis = await collect_kpis(processing, ai, investigation)
        bottlenecks = {
            "processing_failures": processing.get("recent_failures", []),
            "detector_failure_rankings": ai.get("detector_failure_rankings", []),
            "inactive_investigations": inactive,
        }
        audit_summary = {
            **activity,
            "inactive_investigations": inactive,
            "processing_bottlenecks": processing.get("recent_failures", []),
            "detector_failure_rankings": ai.get("detector_failure_rankings", []),
            "evidence_processing_distribution": processing.get(
                "job_type_counts", {}
            ),
            "report_generation_statistics": {
                "reports_generated": investigation.get("reports_generated", 0),
                "status_distribution": investigation.get(
                    "report_status_distribution", {}
                ),
                "average_ms": investigation.get("average_report_generation_ms"),
                "p95_ms": investigation.get("report_generation_p95_ms"),
            },
        }
        trends = {
            "cases_created": investigation.get("cases_created", 0),
            "evidence_uploaded": investigation.get("evidence_uploaded", 0),
            "jobs_created": processing.get("jobs_created", 0),
            "jobs_failed": processing.get("failures", 0),
            "ai_executions": ai.get("model_executions", 0),
            "audit_events": activity.get("event_count", 0),
        }
        return {
            "system_health": health,
            "processing": processing,
            "ai": ai,
            "cases": investigation,
            "reports": {
                "reports_generated": investigation.get("reports_generated", 0),
                "status_distribution": investigation.get(
                    "report_status_distribution", {}
                ),
                "average_generation_ms": investigation.get(
                    "average_report_generation_ms"
                ),
                "p95_generation_ms": investigation.get(
                    "report_generation_p95_ms"
                ),
            },
            "api": api,
            "activity": {
                **activity,
                "recent_events": recent_activity(events),
            },
            "bottlenecks": bottlenecks,
            "audit_summary": audit_summary,
            "kpis": kpis,
            "trends": trends,
            "recent_failures": processing.get("recent_failures", []),
            "generated_at": datetime.now(UTC).isoformat(),
            "engine_version": ENGINE_VERSION,
            "policy_version": POLICY_VERSION,
        }
