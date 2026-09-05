"""Domain exceptions for integrity monitoring."""

from __future__ import annotations

from fastapi import status

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class IntegrityMonitorError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "INTEGRITY_MONITOR_ERROR"


class IntegrityRunNotFoundError(ResourceNotFoundError):
    code = "INTEGRITY_RUN_NOT_FOUND"
