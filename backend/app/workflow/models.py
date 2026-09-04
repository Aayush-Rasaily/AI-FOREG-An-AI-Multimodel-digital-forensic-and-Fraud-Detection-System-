"""Domain models for Phase 8E investigation workflow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ActivityEvent:
    """One immutable workflow activity entry."""

    action: str
    summary: str
    actor_id: str | None
    actor_username: str
    timestamp: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    """Deterministic view of an investigation workflow."""

    id: UUID
    case_id: UUID
    status: str
    assigned_analyst_id: UUID | None
    allowed_transitions: list[str]
    activity: list[dict[str, Any]]
    policy_version: str
    engine_version: str
    created_at: datetime
    updated_at: datetime
    status_changed_at: datetime | None
    status_changed_by: UUID | None
