"""Security governance domain exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class SecurityError(ApplicationError):
    """Base security governance failure."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "SECURITY_ERROR"


class SecurityForbiddenError(ApplicationError):
    """Raised when case or resource access is denied."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "SECURITY_FORBIDDEN"


class SecurityConflictError(ApplicationError):
    """Raised when a security resource already exists."""

    status_code = status.HTTP_409_CONFLICT
    code = "SECURITY_CONFLICT"


class PolicyViolationError(ApplicationError):
    """Raised when an action violates a governance policy."""

    status_code = status.HTTP_409_CONFLICT
    code = "POLICY_VIOLATION"
