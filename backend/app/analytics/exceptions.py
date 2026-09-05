"""Domain exceptions for analytics."""

from __future__ import annotations

from fastapi import status

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class AnalyticsError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "ANALYTICS_ERROR"


class AnalyticsRunNotFoundError(ResourceNotFoundError):
    code = "ANALYTICS_RUN_NOT_FOUND"
