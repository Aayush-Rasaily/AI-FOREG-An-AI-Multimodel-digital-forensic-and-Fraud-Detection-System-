"""Audit-derived operational analytics."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit import AuditEvent
from backend.app.models.case import Case
from backend.app.monitoring.policy import INACTIVE_CASE_DAYS


async def collect_audit_events(
    session: AsyncSession,
    *,
    limit: int = 5000,
) -> list[AuditEvent]:
    """Load recent audit events in deterministic order."""

    statement = (
        select(AuditEvent)
        .order_by(AuditEvent.timestamp.desc(), AuditEvent.id.desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))


def summarize_user_activity(events: list[AuditEvent]) -> dict[str, Any]:
    """Aggregate investigator and operation activity from audit events."""

    by_user: Counter[str] = Counter()
    by_operation: Counter[str] = Counter()
    by_category: Counter[str] = Counter()
    case_activity: Counter[str] = Counter()
    investigations_opened = 0
    reports_downloaded = 0
    evidence_viewed = 0
    searches = 0

    for event in events:
        user = event.user or "system"
        by_user[user] += 1
        by_operation[event.operation] += 1
        by_category[event.category] += 1
        if event.case_id is not None:
            case_activity[str(event.case_id)] += 1
        op = event.operation.lower()
        if "case.view" in op or "case.open" in op or op.endswith(".opened"):
            investigations_opened += 1
        if "report.download" in op or "download" in op:
            reports_downloaded += 1
        if "evidence.view" in op or "evidence.get" in op:
            evidence_viewed += 1
        if "search" in op:
            searches += 1

    busiest_investigators = [
        {"user": user, "event_count": count}
        for user, count in sorted(
            by_user.items(), key=lambda item: (-item[1], item[0]),
        )[:20]
    ]
    busiest_cases = [
        {"case_id": case_id, "event_count": count}
        for case_id, count in sorted(
            case_activity.items(), key=lambda item: (-item[1], item[0]),
        )[:20]
    ]
    return {
        "busiest_investigators": busiest_investigators,
        "busiest_cases": busiest_cases,
        "operations": dict(sorted(by_operation.items())),
        "categories": dict(sorted(by_category.items())),
        "investigations_opened": investigations_opened,
        "reports_downloaded": reports_downloaded,
        "evidence_viewed": evidence_viewed,
        "searches_executed": searches,
        "event_count": len(events),
    }


def summarize_api_usage(events: list[AuditEvent]) -> dict[str, Any]:
    """Derive API-style usage from persisted audit operations (no secrets)."""

    endpoint_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    for event in events:
        endpoint_counts[event.operation] += 1
        metadata = event.metadata_json if isinstance(event.metadata_json, dict) else {}
        status = metadata.get("status_code") or metadata.get("http_status")
        if status is not None:
            status_counts[str(status)] += 1

    endpoints = [
        {"operation": op, "count": count}
        for op, count in sorted(
            endpoint_counts.items(), key=lambda item: (-item[1], item[0]),
        )[:50]
    ]
    return {
        "request_counts": len(events),
        "endpoint_usage": endpoints,
        "response_codes": dict(sorted(status_counts.items())),
        # HTTP latency is not persisted; derived only when audit metadata carries it.
        "average_latency_ms": None,
        "source": "audit_events",
    }


async def find_inactive_cases(session: AsyncSession) -> list[dict[str, Any]]:
    """List cases inactive beyond the configured threshold."""

    cutoff = datetime.now(UTC) - timedelta(days=INACTIVE_CASE_DAYS)
    rows = list(
        await session.scalars(
            select(Case).order_by(Case.updated_at.asc(), Case.id.asc())
        )
    )
    inactive: list[dict[str, Any]] = []
    for case in rows:
        updated = case.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)
        if updated <= cutoff:
            inactive.append(
                {
                    "case_id": str(case.id),
                    "case_number": case.case_number,
                    "title": case.title,
                    "status": case.status.value,
                    "updated_at": updated.isoformat(),
                }
            )
    return inactive[:50]


def recent_activity(
    events: list[AuditEvent], *, limit: int = 25,
) -> list[dict[str, Any]]:
    """Return recent operational audit events (newest first)."""

    items: list[dict[str, Any]] = []
    for event in events[:limit]:
        items.append(
            {
                "id": str(event.id),
                "timestamp": event.timestamp.isoformat(),
                "user": event.user,
                "operation": event.operation,
                "category": event.category,
                "case_id": str(event.case_id) if event.case_id else None,
                "evidence_id": str(event.evidence_id) if event.evidence_id else None,
            }
        )
    return items


def group_counts(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))
