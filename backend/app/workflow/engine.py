"""Deterministic investigation workflow state machine."""

from __future__ import annotations

from backend.app.workflow.exceptions import (
    InvalidReviewTransitionError,
    InvalidTaskTransitionError,
    InvalidWorkflowTransitionError,
    ReportNotApprovedError,
)
from backend.app.workflow.policy import (
    ALLOWED_REPORT_APPROVAL_TRANSITIONS,
    ALLOWED_STATUS_TRANSITIONS,
    ALLOWED_TASK_TRANSITIONS,
    InvestigationStatus,
    ReportApprovalStatus,
    TaskStatus,
)


def allowed_status_transitions(status: str) -> list[str]:
    """Return sorted allowed next investigation statuses."""

    current = InvestigationStatus(status)
    return sorted(item.value for item in ALLOWED_STATUS_TRANSITIONS[current])


def assert_status_transition(
    current: str,
    target: str,
) -> InvestigationStatus:
    """Validate an investigation status transition."""

    try:
        current_status = InvestigationStatus(current)
        target_status = InvestigationStatus(target)
    except ValueError as exc:
        raise InvalidWorkflowTransitionError(
            f"Unknown investigation status: {target}"
        ) from exc
    allowed = ALLOWED_STATUS_TRANSITIONS[current_status]
    if target_status not in allowed:
        raise InvalidWorkflowTransitionError(
            f"Cannot transition from {current} to {target}."
        )
    return target_status


def assert_task_transition(current: str, target: str) -> TaskStatus:
    """Validate a task status transition."""

    try:
        current_status = TaskStatus(current)
        target_status = TaskStatus(target)
    except ValueError as exc:
        raise InvalidTaskTransitionError(
            f"Unknown task status: {target}"
        ) from exc
    allowed = ALLOWED_TASK_TRANSITIONS[current_status]
    if target_status not in allowed:
        raise InvalidTaskTransitionError(
            f"Cannot transition task from {current} to {target}."
        )
    return target_status


def assert_report_approval_transition(
    current: str,
    target: str,
) -> ReportApprovalStatus:
    """Validate a report approval status transition."""

    try:
        current_status = ReportApprovalStatus(current)
        target_status = ReportApprovalStatus(target)
    except ValueError as exc:
        raise InvalidReviewTransitionError(
            f"Unknown report approval status: {target}"
        ) from exc
    allowed = ALLOWED_REPORT_APPROVAL_TRANSITIONS[current_status]
    if target_status not in allowed:
        raise InvalidReviewTransitionError(
            f"Cannot transition report approval from {current} to {target}."
        )
    if (
        target_status is ReportApprovalStatus.PUBLISHED
        and current_status is not ReportApprovalStatus.APPROVED
    ):
        raise ReportNotApprovedError(
            "Reports cannot publish unless approved."
        )
    return target_status


def can_publish_report(status: str) -> bool:
    """Return True when a report approval status may publish."""

    return status == ReportApprovalStatus.APPROVED.value
