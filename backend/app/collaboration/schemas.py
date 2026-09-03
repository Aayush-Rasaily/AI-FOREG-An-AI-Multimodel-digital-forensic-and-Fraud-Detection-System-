"""Pydantic schemas for collaboration APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CaseMemberCreateRequest(BaseModel):
    user_id: UUID
    role: str = Field(min_length=1, max_length=64)


class CaseMemberUpdateRequest(BaseModel):
    role: str | None = Field(default=None, max_length=64)
    transfer_ownership: bool = False


class CaseMemberResponse(BaseModel):
    id: UUID
    case_id: UUID
    user_id: UUID
    username: str | None = None
    display_name: str | None = None
    role: str
    invited_by: UUID | None
    created_at: datetime


class CaseMemberListResponse(BaseModel):
    items: list[CaseMemberResponse]
    total: int


class EvidenceAssignRequest(BaseModel):
    assignee_id: UUID
    priority: str = "medium"
    due_date: datetime | None = None
    notes: str | None = None


class EvidenceAssignmentResponse(BaseModel):
    id: UUID
    case_id: UUID
    evidence_id: UUID
    assignee_id: UUID
    assigned_by: UUID
    priority: str
    status: str
    due_date: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class EvidenceAssignmentListResponse(BaseModel):
    items: list[EvidenceAssignmentResponse]
    total: int


class CommentCreateRequest(BaseModel):
    case_id: UUID
    resource_type: str
    resource_id: str
    body: str = Field(min_length=1, max_length=20000)
    parent_id: UUID | None = None
    body_markdown: bool = True


class CommentUpdateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=20000)


class CommentResponse(BaseModel):
    id: UUID
    case_id: UUID
    author_id: UUID
    author_username: str | None = None
    resource_type: str
    resource_id: str
    parent_id: UUID | None
    body: str
    body_markdown: bool
    edit_history: list[dict]
    is_deleted: bool
    mentions: list[UUID]
    created_at: datetime
    updated_at: datetime


class CommentListResponse(BaseModel):
    items: list[CommentResponse]
    total: int


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    assignee_id: UUID | None = None
    priority: str = "medium"
    due_date: datetime | None = None
    linked_evidence_id: UUID | None = None
    linked_report_id: UUID | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    assignee_id: UUID | None = None
    priority: str | None = None
    status: str | None = None
    due_date: datetime | None = None
    linked_evidence_id: UUID | None = None
    linked_report_id: UUID | None = None


class TaskResponse(BaseModel):
    id: UUID
    case_id: UUID
    title: str
    description: str | None
    assignee_id: UUID | None
    created_by: UUID
    priority: str
    status: str
    due_date: datetime | None
    linked_evidence_id: UUID | None
    linked_report_id: UUID | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    items: list[TaskResponse]
    total: int


class ReviewCreateRequest(BaseModel):
    case_id: UUID
    resource_type: str
    resource_id: str
    reviewer_id: UUID | None = None
    comments: str | None = None


class ReviewUpdateRequest(BaseModel):
    decision: str
    comments: str | None = None
    reviewer_id: UUID | None = None


class ReviewResponse(BaseModel):
    id: UUID
    case_id: UUID
    resource_type: str
    resource_id: str
    state: str
    requested_by: UUID
    reviewer_id: UUID | None
    decision: str | None
    comments: str | None
    decided_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationResponse(BaseModel):
    id: UUID
    user_id: UUID
    case_id: UUID | None
    kind: str
    title: str
    body: str
    status: str
    payload: dict
    created_at: datetime
    read_at: datetime | None


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int


class NotificationUpdateRequest(BaseModel):
    status: str


class ActivityResponse(BaseModel):
    id: UUID
    case_id: UUID
    actor_id: UUID | None
    actor_username: str
    action: str
    summary: str
    details: dict
    created_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int


class WorkflowResponse(BaseModel):
    case_id: UUID
    stage: str
    version: int
    updated_by: UUID | None
    updated_at: datetime
    allowed_transitions: list[str]


class WorkflowUpdateRequest(BaseModel):
    stage: str
