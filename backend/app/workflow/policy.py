"""Investigation workflow policy constants and enumerations."""

from __future__ import annotations

from enum import StrEnum

ENGINE_VERSION = "8e.1.0"
WORKFLOW_POLICY_VERSION = "1.0"
POLICY_VERSION = WORKFLOW_POLICY_VERSION


class InvestigationStatus(StrEnum):
    """Deterministic investigation lifecycle states."""

    NEW = "NEW"
    ACTIVE = "ACTIVE"
    UNDER_REVIEW = "UNDER_REVIEW"
    REQUIRES_CHANGES = "REQUIRES_CHANGES"
    APPROVED = "APPROVED"
    REPORTED = "REPORTED"
    ARCHIVED = "ARCHIVED"


ALLOWED_STATUS_TRANSITIONS: dict[
    InvestigationStatus, frozenset[InvestigationStatus]
] = {
    InvestigationStatus.NEW: frozenset({InvestigationStatus.ACTIVE}),
    InvestigationStatus.ACTIVE: frozenset(
        {InvestigationStatus.UNDER_REVIEW, InvestigationStatus.ARCHIVED}
    ),
    InvestigationStatus.UNDER_REVIEW: frozenset(
        {
            InvestigationStatus.REQUIRES_CHANGES,
            InvestigationStatus.APPROVED,
            InvestigationStatus.ACTIVE,
        }
    ),
    InvestigationStatus.REQUIRES_CHANGES: frozenset(
        {InvestigationStatus.ACTIVE, InvestigationStatus.UNDER_REVIEW}
    ),
    InvestigationStatus.APPROVED: frozenset(
        {InvestigationStatus.REPORTED, InvestigationStatus.UNDER_REVIEW}
    ),
    InvestigationStatus.REPORTED: frozenset({InvestigationStatus.ARCHIVED}),
    InvestigationStatus.ARCHIVED: frozenset(),
}


class TaskType(StrEnum):
    AI_ANALYSIS = "AI_ANALYSIS"
    FORENSIC_REVIEW = "FORENSIC_REVIEW"
    REPORT_REVIEW = "REPORT_REVIEW"
    EVIDENCE_VALIDATION = "EVIDENCE_VALIDATION"
    TIMELINE_REVIEW = "TIMELINE_REVIEW"
    CORRELATION_REVIEW = "CORRELATION_REVIEW"
    FUSION_REVIEW = "FUSION_REVIEW"
    GENERAL = "GENERAL"


class TaskStatus(StrEnum):
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    COMPLETED = "COMPLETED"
    REOPENED = "REOPENED"
    CANCELLED = "CANCELLED"


ALLOWED_TASK_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.OPEN: frozenset(
        {TaskStatus.ASSIGNED, TaskStatus.COMPLETED, TaskStatus.CANCELLED}
    ),
    TaskStatus.ASSIGNED: frozenset(
        {TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.OPEN}
    ),
    TaskStatus.COMPLETED: frozenset({TaskStatus.REOPENED}),
    TaskStatus.REOPENED: frozenset(
        {TaskStatus.ASSIGNED, TaskStatus.COMPLETED, TaskStatus.CANCELLED}
    ),
    TaskStatus.CANCELLED: frozenset(),
}


class EvidenceReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReportApprovalStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    REVISION_REQUIRED = "revision_required"


ALLOWED_REPORT_APPROVAL_TRANSITIONS: dict[
    ReportApprovalStatus, frozenset[ReportApprovalStatus]
] = {
    ReportApprovalStatus.DRAFT: frozenset(
        {ReportApprovalStatus.REVIEW, ReportApprovalStatus.APPROVED}
    ),
    ReportApprovalStatus.REVIEW: frozenset(
        {
            ReportApprovalStatus.APPROVED,
            ReportApprovalStatus.REVISION_REQUIRED,
            ReportApprovalStatus.DRAFT,
        }
    ),
    ReportApprovalStatus.APPROVED: frozenset(
        {ReportApprovalStatus.PUBLISHED, ReportApprovalStatus.REVISION_REQUIRED}
    ),
    ReportApprovalStatus.PUBLISHED: frozenset(),
    ReportApprovalStatus.REVISION_REQUIRED: frozenset(
        {ReportApprovalStatus.DRAFT, ReportApprovalStatus.REVIEW}
    ),
}


class ReviewKind(StrEnum):
    EVIDENCE = "evidence"
    REPORT = "report"


class NoteCategory(StrEnum):
    GENERAL = "general"
    ANALYTICAL = "analytical"
    PROCEDURAL = "procedural"
    REVIEW = "review"
    MILESTONE = "milestone"


class NoteVisibility(StrEnum):
    INTERNAL = "internal"
    TEAM = "team"
    RESTRICTED = "restricted"


class MilestoneType(StrEnum):
    INVESTIGATION_STARTED = "Investigation Started"
    EVIDENCE_COLLECTION_COMPLETE = "Evidence Collection Complete"
    AI_ANALYSIS_COMPLETE = "AI Analysis Complete"
    FUSION_COMPLETE = "Fusion Complete"
    CORRELATION_COMPLETE = "Correlation Complete"
    TIMELINE_COMPLETE = "Timeline Complete"
    REPORT_DRAFTED = "Report Drafted"
    REPORT_APPROVED = "Report Approved"
    CASE_CLOSED = "Case Closed"


class NotificationKind(StrEnum):
    ASSIGNED_TASK = "assigned_task"
    REVIEW_REQUEST = "review_request"
    APPROVAL_REQUIRED = "approval_required"
    WORKFLOW_COMPLETED = "workflow_completed"
    REPORT_PUBLISHED = "report_published"


class NotificationStatus(StrEnum):
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class ActivityAction(StrEnum):
    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_REOPENED = "task_reopened"
    TASK_CANCELLED = "task_cancelled"
    REVIEW_REQUESTED = "review_requested"
    REVIEW_COMPLETED = "review_completed"
    REPORT_APPROVED = "report_approved"
    REPORT_PUBLISHED = "report_published"
    EVIDENCE_APPROVED = "evidence_approved"
    STATUS_CHANGED = "status_changed"
    MILESTONE_REACHED = "milestone_reached"
    NOTE_CREATED = "note_created"
    NOTE_REVISED = "note_revised"
    WORKFLOW_INITIALIZED = "workflow_initialized"
