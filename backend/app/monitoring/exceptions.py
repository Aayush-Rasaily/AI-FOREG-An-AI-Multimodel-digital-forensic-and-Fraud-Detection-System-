"""Exceptions for the operational monitoring layer."""

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class MonitoringError(ApplicationError):
    """Base error for monitoring failures."""

    code = "MONITORING_ERROR"


class MonitoringSnapshotNotFoundError(ResourceNotFoundError):
    """Raised when a monitoring snapshot cannot be found."""

    code = "MONITORING_SNAPSHOT_NOT_FOUND"


__all__ = [
    "MonitoringError",
    "MonitoringSnapshotNotFoundError",
]
