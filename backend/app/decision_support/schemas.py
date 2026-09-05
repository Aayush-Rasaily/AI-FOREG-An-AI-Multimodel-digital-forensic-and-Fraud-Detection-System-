"""API schemas for Phase 9D decision support."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WorkloadMetricsResponse(BaseModel):
    open_tasks: int
    completed_tasks: int
    pending_reviews: int
    average_priority: float
    critical_evidence_count: int
    workflow_completion: float
    investigation_progress: float
    evidence_review_coverage: float


class WorkflowTaskResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    task_key: str
    task_type: str
    stage: str
    title: str
    description: str
    priority: str
    status: str
    estimated_effort_hours: float
    priority_score: float = 0.0
    required_evidence_ids: list[str] = Field(default_factory=list)
    supporting_intelligence: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ReviewQueueItemResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    queue_key: str
    evidence_id: str
    priority: str
    priority_score: float
    reasons: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)


class DecisionLogResponse(BaseModel):
    id: UUID
    case_id: UUID
    run_id: UUID | None = None
    task_id: UUID | None = None
    decision_type: str
    investigator: str
    justification: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DecisionCreateRequest(BaseModel):
    case_id: UUID
    decision_type: str
    investigator: str
    justification: str
    task_id: UUID | None = None
    run_id: UUID | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)


class TaskUpdateRequest(BaseModel):
    status: str | None = None
    priority: str | None = None


class WorkflowRunResponse(BaseModel):
    id: UUID | None = None
    case_id: UUID
    status: str
    current_stage: str
    task_count: int
    review_count: int
    metrics: WorkloadMetricsResponse
    open_conflicts: list[dict[str, Any]] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    policy_version: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    tasks: list[WorkflowTaskResponse] = Field(default_factory=list)
    review_queue: list[ReviewQueueItemResponse] = Field(default_factory=list)
    persisted: bool = True


class WorkflowPreviewResponse(WorkflowRunResponse):
    persisted: bool = False


class WorkflowTaskListResponse(BaseModel):
    items: list[WorkflowTaskResponse]
    total: int


class ReviewQueueListResponse(BaseModel):
    items: list[ReviewQueueItemResponse]
    total: int


class DecisionLogListResponse(BaseModel):
    items: list[DecisionLogResponse]
    total: int
