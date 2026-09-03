"""Activity feed helpers."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.collaboration import ActivityLog


async def record_activity(
    session: AsyncSession,
    *,
    case_id: UUID,
    actor_id: UUID | None,
    actor_username: str,
    action: str,
    summary: str,
    details: dict[str, Any] | None = None,
) -> ActivityLog:
    """Persist one collaborative activity entry."""

    row = ActivityLog(
        case_id=case_id,
        actor_id=actor_id,
        actor_username=actor_username,
        action=action,
        summary=summary,
        details_json=details or {},
    )
    session.add(row)
    await session.flush()
    return row
