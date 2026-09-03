"""Exceptions for the investigation intelligence layer."""

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class IntelligenceError(ApplicationError):
    """Base error for investigation intelligence failures."""

    code = "INTELLIGENCE_ERROR"


class IntelligenceNotFoundError(ResourceNotFoundError):
    """Raised when an investigation summary cannot be found."""

    code = "INTELLIGENCE_NOT_FOUND"


__all__ = [
    "IntelligenceError",
    "IntelligenceNotFoundError",
]
