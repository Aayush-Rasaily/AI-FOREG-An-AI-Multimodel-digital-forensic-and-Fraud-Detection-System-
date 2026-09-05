"""Domain exceptions for platform validation."""

from __future__ import annotations

from fastapi import status

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class PlatformValidationError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "PLATFORM_VALIDATION_ERROR"


class PlatformValidationRunNotFoundError(ResourceNotFoundError):
    code = "PLATFORM_VALIDATION_RUN_NOT_FOUND"
