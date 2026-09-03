"""Audit log export helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from backend.app.audit.models import AuditExportResult


def _serialize_event(event: Any) -> dict[str, Any]:
    return {
        "id": str(event.id),
        "timestamp": event.timestamp.isoformat(),
        "user": event.user,
        "operation": event.operation,
        "category": event.category,
        "case_id": str(event.case_id) if event.case_id else None,
        "evidence_id": (
            str(event.evidence_id) if event.evidence_id else None
        ),
        "previous_state": event.previous_state_json,
        "new_state": event.new_state_json,
        "client_ip": event.client_ip,
        "user_agent": event.user_agent,
        "engine_version": event.engine_version,
        "policy_version": event.policy_version,
        "sha256_checksum": event.sha256_checksum,
        "integrity_hash": event.integrity_hash,
        "metadata": event.metadata_json,
    }


def export_json(events: list[Any]) -> AuditExportResult:
    """Export audit events as canonical JSON."""
    items = [_serialize_event(e) for e in events]
    payload = json.dumps(
        {"audit_events": items, "total": len(items)},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    checksum = hashlib.sha256(payload).hexdigest()
    return AuditExportResult(
        format="json",
        total_events=len(items),
        payload=payload,
        checksum=checksum,
        metadata={"export_format": "json"},
    )
