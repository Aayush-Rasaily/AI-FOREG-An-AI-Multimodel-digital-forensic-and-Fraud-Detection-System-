"""Collaboration policy constants and enumerations."""

from __future__ import annotations

from enum import StrEnum

ENGINE_VERSION = "1.0"
POLICY_VERSION = "1.0"


class CaseMemberRole(StrEnum):
    OWNER = "owner"
    LEAD_INVESTIGATOR = "lead_investigator"
    INVESTIGATOR = "investigator"
    ANALYST = "analyst"
    REVIEWER = "reviewer"
    VIEWER = "viewer"


class AssignmentStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REOPENED = "reopened"
    CANCELLED = "cancelled"


class ReviewState(StrEnum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    REJECT = "reject"


class NotificationKind(StrEnum):
    ASSIGNMENT = "assignment"
    MENTION = "mention"
    APPROVAL_REQUEST = "approval_request"
    REVIEW_COMPLETED = "review_completed"
    REPORT_GENERATED = "report_generated"
    CASE_INVITATION = "case_invitation"
    TASK_COMPLETED = "task_completed"
    TASK_OVERDUE = "task_overdue"


class NotificationStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class CommentResourceType(StrEnum):
    CASE = "case"
    EVIDENCE = "evidence"
    TIMELINE = "timeline"
    AI_FINDING = "ai_finding"
    FUSION = "fusion"
    CORRELATION = "correlation"
    ENTITY = "entity"
    REPORT = "report"


class ReviewResourceType(StrEnum):
    REPORT = "report"
    FUSION = "fusion"
    ENTITY_GRAPH = "entity_graph"
    TIMELINE = "timeline"
    CASE_CLOSURE = "case_closure"


class CaseWorkflowStage(StrEnum):
    OPEN = "open"
    EVIDENCE_COLLECTION = "evidence_collection"
    ANALYSIS = "analysis"
    REVIEW = "review"
    REPORTING = "reporting"
    CLOSED = "closed"
    ARCHIVED = "archived"


WORKFLOW_ORDER: tuple[CaseWorkflowStage, ...] = (
    CaseWorkflowStage.OPEN,
    CaseWorkflowStage.EVIDENCE_COLLECTION,
    CaseWorkflowStage.ANALYSIS,
    CaseWorkflowStage.REVIEW,
    CaseWorkflowStage.REPORTING,
    CaseWorkflowStage.CLOSED,
    CaseWorkflowStage.ARCHIVED,
)

ALLOWED_WORKFLOW_TRANSITIONS: dict[CaseWorkflowStage, frozenset[CaseWorkflowStage]] = {
    CaseWorkflowStage.OPEN: frozenset({CaseWorkflowStage.EVIDENCE_COLLECTION}),
    CaseWorkflowStage.EVIDENCE_COLLECTION: frozenset(
        {CaseWorkflowStage.ANALYSIS, CaseWorkflowStage.OPEN}
    ),
    CaseWorkflowStage.ANALYSIS: frozenset(
        {CaseWorkflowStage.REVIEW, CaseWorkflowStage.EVIDENCE_COLLECTION}
    ),
    CaseWorkflowStage.REVIEW: frozenset(
        {CaseWorkflowStage.REPORTING, CaseWorkflowStage.ANALYSIS}
    ),
    CaseWorkflowStage.REPORTING: frozenset(
        {CaseWorkflowStage.CLOSED, CaseWorkflowStage.REVIEW}
    ),
    CaseWorkflowStage.CLOSED: frozenset(
        {CaseWorkflowStage.ARCHIVED, CaseWorkflowStage.REPORTING}
    ),
    CaseWorkflowStage.ARCHIVED: frozenset(),
}

MEMBER_MANAGE_ROLES = frozenset(
    {CaseMemberRole.OWNER, CaseMemberRole.LEAD_INVESTIGATOR}
)
