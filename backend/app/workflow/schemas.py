"""Pydantic schemas for Phase 8E investigation workflow API."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_id: UUID
    status: str
    assigned_analyst_id: UUID | None = None
    allowed_transitions: list[str]
    activity: list[dict[str, Any]] = Field(default_factory=list)
    policy_version: str
    engine_version: str
    created_at: datetime
    updated_at: datetime
    status_changed_at: datetime | None = None
    status_changed_by: UUID | None = None


class WorkflowStatusUpdateRequest(BaseModel):
    status: str
    assigned_analyst_id: UUID | None = None


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=256)
    task_type: str = "GENERAL"
    description: str | None = None
    assignee_id: UUID | None = None
    linked_evidence_id: UUID | None = None
    linked_report_id: UUID | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=256)
    description: str | None = None
    assignee_id: UUID | None = None
    status: str | None = None
    action: str | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    case_id: UUID
    task_type: str
    title: str
    description: str | None = None
    status: str
    assignee_id: UUID | None = None
    created_by: UUID | None = None
    linked_evidence_id: UUID | None = None
    linked_report_id: UUID | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class NoteCreateRequest(BaseModel):
    content_markdown: str = Field(min_length=1)
    category: str = "general"
    visibility: str = "internal"


class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    case_id: UUID
    category: str
    visibility: str
    content_markdown: str
    author_id: UUID | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    items: list[NoteResponse]
    total: int


class ReviewCreateRequest(BaseModel):
    review_kind: str
    status: str | None = None
    evidence_id: UUID | None = None
    report_id: UUID | None = None
    reviewer_id: UUID | None = None
    comments: str | None = None
    reason: str | None = None


class ReviewUpdateRequest(BaseModel):
    status: str
    comments: str | None = None
    reason: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    case_id: UUID
    review_kind: str
    status: str
    evidence_id: UUID | None = None
    report_id: UUID | None = None
    reviewer_id: UUID | None = None
    comments: str | None = None
    reason: str | None = None
    decided_at: datetime | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)
    created_by: UUID | None = None
    created_at: datetime
    updated_at: datetime


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int


class MilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    case_id: UUID
    milestone_type: str
    label: str
    reached_at: datetime
    reached_by: UUID | None = None
    auto_derived: bool
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MilestoneListResponse(BaseModel):
    items: list[MilestoneResponse]
    total: int


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    case_id: UUID
    user_id: UUID
    kind: str
    title: str
    body: str
    status: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
