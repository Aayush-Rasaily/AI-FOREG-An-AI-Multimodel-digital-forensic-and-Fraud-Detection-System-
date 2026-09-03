"""In-app notification helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.collaboration import Notification


async def create_notification(
    session: AsyncSession,
    *,
    user_id: UUID,
    kind: str,
    title: str,
    body: str,
    case_id: UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> Notification:
    """Create an unread in-app notification."""

    row = Notification(
        user_id=user_id,
        case_id=case_id,
        kind=kind,
        title=title,
        body=body,
        status="unread",
        payload_json=payload or {},
    )
    session.add(row)
    await session.flush()
    return row
