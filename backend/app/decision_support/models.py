"""In-memory domain models for Phase 9D decision support."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class WorkflowStage(StrEnum):
    NEW = "NEW"
    TRIAGE = "TRIAGE"
    COLLECT = "COLLECT"
    VERIFY = "VERIFY"
    COMPARE = "COMPARE"
    AI_ANALYSIS = "AI_ANALYSIS"
    CORRELATE = "CORRELATE"
    REVIEW = "REVIEW"
    REPORT = "REPORT"
    COMPLETE = "COMPLETE"


class TaskType(StrEnum):
    ACQUIRE_ORIGINAL_EVIDENCE = "ACQUIRE_ORIGINAL_EVIDENCE"
    VERIFY_METADATA = "VERIFY_METADATA"
    RUN_SIGNATURE_VERIFICATION = "RUN_SIGNATURE_VERIFICATION"
    REVIEW_AI_CONFLICT = "REVIEW_AI_CONFLICT"
    REVIEW_TIMELINE_CONFLICT = "REVIEW_TIMELINE_CONFLICT"
    COMPARE_RELATED_EVIDENCE = "COMPARE_RELATED_EVIDENCE"
    VALIDATE_CORRELATION = "VALIDATE_CORRELATION"
    REVIEW_KNOWLEDGE_GRAPH = "REVIEW_KNOWLEDGE_GRAPH"
    COMPLETE_CHAIN_OF_CUSTODY = "COMPLETE_CHAIN_OF_CUSTODY"
    REVIEW_OCR = "REVIEW_OCR"
    VALIDATE_REPORT = "VALIDATE_REPORT"
    MANUAL_EXPERT_REVIEW = "MANUAL_EXPERT_REVIEW"
    CLOSE_INVESTIGATION = "CLOSE_INVESTIGATION"


class TaskStatus(StrEnum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PriorityLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class DecisionType(StrEnum):
    ACCEPTED_RECOMMENDATION = "ACCEPTED_RECOMMENDATION"
    REJECTED_RECOMMENDATION = "REJECTED_RECOMMENDATION"
    MARKED_REVIEWED = "MARKED_REVIEWED"
    ESCALATED = "ESCALATED"
    DEFERRED = "DEFERRED"
    CLOSED = "CLOSED"
    REOPENED = "REOPENED"


TASK_TITLES: dict[str, str] = {
    TaskType.ACQUIRE_ORIGINAL_EVIDENCE: "Acquire Original Evidence",
    TaskType.VERIFY_METADATA: "Verify Metadata",
    TaskType.RUN_SIGNATURE_VERIFICATION: "Run Signature Verification",
    TaskType.REVIEW_AI_CONFLICT: "Review AI Conflict",
    TaskType.REVIEW_TIMELINE_CONFLICT: "Review Timeline Conflict",
    TaskType.COMPARE_RELATED_EVIDENCE: "Compare Related Evidence",
    TaskType.VALIDATE_CORRELATION: "Validate Correlation",
    TaskType.REVIEW_KNOWLEDGE_GRAPH: "Review Knowledge Graph",
    TaskType.COMPLETE_CHAIN_OF_CUSTODY: "Complete Chain of Custody",
    TaskType.REVIEW_OCR: "Review OCR",
    TaskType.VALIDATE_REPORT: "Validate Report",
    TaskType.MANUAL_EXPERT_REVIEW: "Manual Expert Review",
    TaskType.CLOSE_INVESTIGATION: "Close Investigation",
}


@dataclass(frozen=True)
class ProvenanceBundle:
    evidence_ids: tuple[str, ...] = ()
    timeline_ids: tuple[str, ...] = ()
    correlation_ids: tuple[str, ...] = ()
    fusion_ids: tuple[str, ...] = ()
    knowledge_graph_ids: tuple[str, ...] = ()
    hypothesis_ids: tuple[str, ...] = ()
    recommendation_ids: tuple[str, ...] = ()
    gap_ids: tuple[str, ...] = ()
    detail: str | None = None


@dataclass
class WorkflowTaskDraft:
    task_key: str
    task_type: TaskType
    stage: WorkflowStage
    title: str
    description: str
    priority: PriorityLevel
    status: TaskStatus
    estimated_effort_hours: float
    required_evidence_ids: list[str] = field(default_factory=list)
    supporting_intelligence: dict[str, Any] = field(default_factory=dict)
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)
    priority_score: float = 0.0


@dataclass
class ReviewQueueDraft:
    queue_key: str
    evidence_id: str
    priority: PriorityLevel
    priority_score: float
    reasons: list[str] = field(default_factory=list)
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class WorkloadMetrics:
    open_tasks: int = 0
    completed_tasks: int = 0
    pending_reviews: int = 0
    average_priority: float = 0.0
    critical_evidence_count: int = 0
    workflow_completion: float = 0.0
    investigation_progress: float = 0.0
    evidence_review_coverage: float = 0.0


@dataclass
class WorkflowPlan:
    tasks: list[WorkflowTaskDraft]
    review_queue: list[ReviewQueueDraft]
    metrics: WorkloadMetrics
    current_stage: WorkflowStage
    provenance: dict[str, Any]
    open_conflicts: list[dict[str, Any]] = field(default_factory=list)
