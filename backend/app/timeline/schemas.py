"""Pydantic schemas for investigation timeline APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.timeline.models import (
    TimelineConflictType,
    TimelineEventType,
    TimelineRunStatus,
)


class TimelineEventResponse(BaseModel):
    """One timeline event returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timeline_id: UUID
    case_id: UUID
    evidence_id: UUID | None
    event_id: str
    event_type: TimelineEventType
    timestamp: datetime | None
    timezone: str | None
    normalized_timestamp: datetime | None
    confidence: float
    uncertainty_ms: int
    description: str
    source: str
    source_id: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    supporting_artifacts: list[str] = Field(default_factory=list)
    created_at: datetime


class TimelineConflictResponse(BaseModel):
    """One timeline conflict returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timeline_id: UUID
    case_id: UUID
    conflict_id: str
    conflict_type: TimelineConflictType
    evidence_id: UUID | None
    involved_event_ids: list[str]
    explanation: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TimelineRunResponse(BaseModel):
    """Summary of one timeline reconstruction run."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    status: TimelineRunStatus
    engine_version: str
    policy_version: str
    event_count: int
    conflicts_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)


class TimelineDetailResponse(TimelineRunResponse):
    """Timeline run with ordered events and conflicts."""

    events: list[TimelineEventResponse] = Field(default_factory=list)
    conflicts: list[TimelineConflictResponse] = Field(default_factory=list)


class TimelineRunListResponse(BaseModel):
    """Paginated timeline history for one case."""

    items: list[TimelineRunResponse]
    total: int
    limit: int
    offset: int
