"""Workflow activity timeline helpers (extends forensic timeline)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.workflow import InvestigationWorkflow


def _iso_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


async def append_activity(
    session: AsyncSession,
    workflow: InvestigationWorkflow,
    *,
    action: str,
    summary: str,
    actor_id: UUID | None,
    actor_username: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a deterministic activity event to the workflow record.

    This is additive to the forensic investigation timeline and does not
    mutate timeline event records produced by Phase 6 timeline analysis.
    """

    event = {
        "action": action,
        "summary": summary,
        "actor_id": str(actor_id) if actor_id else None,
        "actor_username": actor_username,
        "timestamp": _iso_now(),
        "details": details or {},
    }
    history = list(workflow.activity_json or [])
    history.append(event)
    workflow.activity_json = history
    await session.flush()
    return event
