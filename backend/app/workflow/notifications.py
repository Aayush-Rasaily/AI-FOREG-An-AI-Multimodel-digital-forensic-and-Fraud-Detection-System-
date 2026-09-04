"""Deterministic in-app workflow notifications (no external channels)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workflow import WorkflowNotification
from backend.app.workflow.policy import NotificationStatus


async def create_workflow_notification(
    session: AsyncSession,
    *,
    workflow_id: UUID,
    case_id: UUID,
    user_id: UUID,
    kind: str,
    title: str,
    body: str,
    payload: dict[str, Any] | None = None,
) -> WorkflowNotification:
    """Create an unread in-app workflow notification."""

    row = WorkflowNotification(
        workflow_id=workflow_id,
        case_id=case_id,
        user_id=user_id,
        kind=kind,
        title=title,
        body=body,
        status=NotificationStatus.UNREAD.value,
        payload_json=payload or {},
    )
    session.add(row)
    await session.flush()
    return row
