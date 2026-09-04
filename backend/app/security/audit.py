"""Immutable audit helpers for security governance actions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.recorder import AuditRecorder
from backend.app.security.policy import SECURITY_POLICY_VERSION


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
