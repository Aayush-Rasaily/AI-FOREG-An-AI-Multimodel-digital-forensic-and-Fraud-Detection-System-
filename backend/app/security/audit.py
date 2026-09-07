"""Immutable audit helpers for security governance and hardening actions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.recorder import AuditRecorder
from backend.app.security.policy import SECURITY_POLICY_VERSION

HARDENING_POLICY_VERSION = "10D.1"


async def record_security_audit(
    session: AsyncSession,
    *,
    operation: str,
    user: str,
    case_id: UUID | None = None,
    evidence_id: UUID | None = None,
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> UUID:
    """Persist one immutable audit event for a security action."""

    payload = dict(metadata or {})
    payload["security_policy_version"] = SECURITY_POLICY_VERSION
    recorder = AuditRecorder(session)
    return await recorder.record(
        operation=operation,
        category="security_governance",
        user=user,
        case_id=case_id,
        evidence_id=evidence_id,
        previous_state=previous_state,
        new_state=new_state,
        metadata=payload,
    )


async def record_hardening_audit(
    session: AsyncSession,
    *,
    operation: str,
    user: str = "system",
    metadata: dict[str, Any] | None = None,
) -> UUID:
    """Persist an audit event for enterprise hardening controls."""

    payload = dict(metadata or {})
    payload["hardening_policy_version"] = HARDENING_POLICY_VERSION
    payload["security_policy_version"] = SECURITY_POLICY_VERSION
    recorder = AuditRecorder(session)
    return await recorder.record(
        operation=operation,
        category="security_hardening",
        user=user,
        metadata=payload,
    )


def hardening_event_payload(
    *,
    event: str,
    path: str | None = None,
    category: str | None = None,
    client: str | None = None,
    detail: str | None = None,
) -> dict[str, Any]:
    """Build a safe metadata payload for rate-limit / upload rejections."""

    return {
        "event": event,
        "path": path,
        "category": category,
        "client": client,
        "detail": detail,
        "hardening_policy_version": HARDENING_POLICY_VERSION,
    }
