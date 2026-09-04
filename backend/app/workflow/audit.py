"""Immutable audit trail helpers for investigation workflow actions."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.audit.recorder import AuditRecorder
from backend.app.workflow.policy import WORKFLOW_POLICY_VERSION


async def record_workflow_audit(
    session: AsyncSession,
    *,
    operation: str,
    case_id: UUID,
    user: str,
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
    evidence_id: UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> UUID:
    """Persist one immutable forensic audit event for a workflow action."""

    payload = dict(metadata or {})
    payload["workflow_policy_version"] = WORKFLOW_POLICY_VERSION
    recorder = AuditRecorder(session)
    return await recorder.record(
        operation=operation,
        category="investigation_workflow",
        user=user,
        case_id=case_id,
        evidence_id=evidence_id,
        previous_state=previous_state,
        new_state=new_state,
        metadata=payload,
    )
