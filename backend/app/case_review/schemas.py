"""API schemas for Phase 9E case review."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ValidationMetricsResponse(BaseModel):
    validation_pct: float
    evidence_coverage_pct: float
    review_completion_pct: float
    approval_completion_pct: float
    outstanding_issues: int
    blocking_issues: int


class ChecklistItemResponse(BaseModel):
    id: UUID | None = None
    checklist_id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    item_key: str
    item_code: str
    title: str
    status: str
    suggested_status: str
    blocking: bool
    outstanding: bool
    notes: str
    reviewer: str | None = None
    reviewed_at: datetime | None = None
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ApprovalResponse(BaseModel):
    id: UUID | None = None
    run_id: UUID | None = None
    case_id: UUID | None = None
    checklist_id: UUID | None = None
    checklist_item_id: UUID | None = None
    reviewer: str
    approver_role: str
    decision: str
    comments: str
    provenance: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class ChecklistItemUpdateRequest(BaseModel):
    status: str | None = None
    notes: str | None = None
    reviewer: str | None = None


class ApprovalCreateRequest(BaseModel):
    case_id: UUID
    run_id: UUID | None = None
    checklist_id: UUID | None = None
    checklist_item_id: UUID | None = None
    reviewer: str
    approver_role: str
    decision: str
    comments: str = ""
    provenance: dict[str, Any] = Field(default_factory=dict)


class CaseReviewRunResponse(BaseModel):
    id: UUID | None = None
    case_id: UUID
    status: str
    stage: str
    checklist_count: int
    approval_count: int
    metrics: ValidationMetricsResponse
    outstanding: list[str] = Field(default_factory=list)
    blocking: list[str] = Field(default_factory=list)
    required_roles: list[str] = Field(default_factory=list)
    provenance: dict[str, Any] = Field(default_factory=dict)
    engine_version: str
    policy_version: str
    created_at: datetime | None = None
    completed_at: datetime | None = None
    checklist: list[ChecklistItemResponse] = Field(default_factory=list)
    approvals: list[ApprovalResponse] = Field(default_factory=list)
    persisted: bool = True


class CaseReviewPreviewResponse(CaseReviewRunResponse):
    persisted: bool = False


class ChecklistListResponse(BaseModel):
    items: list[ChecklistItemResponse]
    total: int


class ApprovalListResponse(BaseModel):
    items: list[ApprovalResponse]
    total: int


class CaseReviewHistoryItem(BaseModel):
    id: UUID
    case_id: UUID
    status: str
    stage: str
    checklist_count: int
    approval_count: int
    metrics: ValidationMetricsResponse
    engine_version: str
    policy_version: str
    created_at: datetime
    completed_at: datetime | None = None


class CaseReviewHistoryResponse(BaseModel):
    items: list[CaseReviewHistoryItem]
    total: int
