"""In-memory domain models for Phase 9E case review."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class ReviewStage(StrEnum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VALIDATED = "VALIDATED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    FINALIZED = "FINALIZED"


class ChecklistItemStatus(StrEnum):
    PENDING = "PENDING"
    PASS = "PASS"
    FAIL = "FAIL"
    NA = "NA"
    BLOCKED = "BLOCKED"


class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    DEFERRED = "DEFERRED"


class ApproverRole(StrEnum):
    TECHNICAL_REVIEWER = "TECHNICAL_REVIEWER"
    FORENSIC_REVIEWER = "FORENSIC_REVIEWER"
    LEAD_INVESTIGATOR = "LEAD_INVESTIGATOR"
    CASE_SUPERVISOR = "CASE_SUPERVISOR"


@dataclass(frozen=True)
class ProvenanceBundle:
    evidence_ids: tuple[str, ...] = ()
    timeline_ids: tuple[str, ...] = ()
    correlation_ids: tuple[str, ...] = ()
    fusion_ids: tuple[str, ...] = ()
    knowledge_graph_ids: tuple[str, ...] = ()
    workflow_task_ids: tuple[str, ...] = ()
    hypothesis_ids: tuple[str, ...] = ()
    recommendation_ids: tuple[str, ...] = ()
    report_ids: tuple[str, ...] = ()
    detail: str | None = None


@dataclass
class ChecklistItemDraft:
    item_key: str
    item_code: str
    title: str
    status: ChecklistItemStatus
    suggested_status: ChecklistItemStatus
    blocking: bool
    outstanding: bool
    notes: str
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class ValidationMetrics:
    validation_pct: float = 0.0
    evidence_coverage_pct: float = 0.0
    review_completion_pct: float = 0.0
    approval_completion_pct: float = 0.0
    outstanding_issues: int = 0
    blocking_issues: int = 0


@dataclass
class ReviewPlan:
    stage: ReviewStage
    checklist: list[ChecklistItemDraft]
    metrics: ValidationMetrics
    outstanding: list[str]
    blocking: list[str]
    provenance: dict[str, Any]
    required_approver_roles: list[str] = field(default_factory=list)
