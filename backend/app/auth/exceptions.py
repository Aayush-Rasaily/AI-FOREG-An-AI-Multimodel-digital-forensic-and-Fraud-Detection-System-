"""Authentication and authorization exceptions."""

from fastapi import status

from backend.app.core.exceptions import ApplicationError


class AuthenticationError(ApplicationError):
    """Raised when credentials or tokens are missing or invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHENTICATED"


class AuthorizationError(ApplicationError):
    """Raised when an authenticated user lacks a required permission."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class AccountLockedError(ApplicationError):
    """Raised when an account is locked after failed logins."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "ACCOUNT_LOCKED"


class PasswordPolicyError(ApplicationError):
    """Raised when a password does not meet policy requirements."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "PASSWORD_POLICY"


class AuthConflictError(ApplicationError):
    """Raised when a username or email is already registered."""

    status_code = status.HTTP_409_CONFLICT
    code = "AUTH_CONFLICT"
