"""Audit event construction helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from backend.app.audit.policy import ENGINE_VERSION, POLICY_VERSION


def _canonical(data: Any) -> str:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), default=str,
    )


def compute_integrity_hash(
    *,
    audit_id: str,
    timestamp: str,
    operation: str,
    case_id: str | None,
    evidence_id: str | None,
    sha256_checksum: str | None,
    previous_state: Any,
    new_state: Any,
) -> str:
    """Deterministic integrity hash for one audit record."""
    payload = _canonical({
        "audit_id": audit_id,
        "timestamp": timestamp,
        "operation": operation,
        "case_id": case_id,
        "evidence_id": evidence_id,
        "sha256_checksum": sha256_checksum,
        "previous_state": previous_state,
        "new_state": new_state,
    })
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_audit_event(
    *,
    operation: str,
    category: str,
    user: str = "system",
    case_id: UUID | None = None,
    evidence_id: UUID | None = None,
    previous_state: Any = None,
    new_state: Any = None,
    client_ip: str | None = None,
    user_agent: str | None = None,
    sha256_checksum: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete audit event dict ready for persistence."""
    audit_id = str(uuid4())
    ts = datetime.now(UTC).isoformat()
    integrity = compute_integrity_hash(
        audit_id=audit_id,
        timestamp=ts,
        operation=operation,
        case_id=str(case_id) if case_id else None,
        evidence_id=str(evidence_id) if evidence_id else None,
        sha256_checksum=sha256_checksum,
        previous_state=previous_state,
        new_state=new_state,
    )
    return {
        "id": audit_id,
        "timestamp": ts,
        "user": user,
        "operation": operation,
        "category": category,
        "case_id": str(case_id) if case_id else None,
        "evidence_id": (
            str(evidence_id) if evidence_id else None
        ),
        "previous_state": previous_state,
        "new_state": new_state,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "engine_version": ENGINE_VERSION,
        "policy_version": POLICY_VERSION,
        "sha256_checksum": sha256_checksum,
        "integrity_hash": integrity,
        "metadata": metadata or {},
    }
