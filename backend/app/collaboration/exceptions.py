"""Collaboration domain exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class CollaborationError(ApplicationError):
    """Base collaboration failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "COLLABORATION_ERROR"


class CollaborationConflictError(ApplicationError):
    """Raised when a collaboration resource already exists."""

    status_code = status.HTTP_409_CONFLICT
    code = "COLLABORATION_CONFLICT"


class CollaborationForbiddenError(ApplicationError):
    """Raised when case-level membership forbids an action."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "COLLABORATION_FORBIDDEN"


class InvalidWorkflowTransitionError(ApplicationError):
    """Raised when a workflow transition is not allowed."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "INVALID_WORKFLOW_TRANSITION"
