"""Investigation workflow domain exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class WorkflowError(ApplicationError):
    """Base investigation workflow failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "WORKFLOW_ERROR"


class InvalidWorkflowTransitionError(ApplicationError):
    """Raised when an investigation status transition is not allowed."""

    status_code = status.HTTP_409_CONFLICT
    code = "INVALID_WORKFLOW_TRANSITION"


class InvalidTaskTransitionError(ApplicationError):
    """Raised when a task status transition is not allowed."""

    status_code = status.HTTP_409_CONFLICT
    code = "INVALID_TASK_TRANSITION"


class InvalidReviewTransitionError(ApplicationError):
    """Raised when a review/approval transition is not allowed."""

    status_code = status.HTTP_409_CONFLICT
    code = "INVALID_REVIEW_TRANSITION"


class WorkflowConflictError(ApplicationError):
    """Raised when a workflow resource already exists or conflicts."""

    status_code = status.HTTP_409_CONFLICT
    code = "WORKFLOW_CONFLICT"


class ReportNotApprovedError(ApplicationError):
    """Raised when a report is published without prior approval."""

    status_code = status.HTTP_409_CONFLICT
    code = "REPORT_NOT_APPROVED"
