"""Domain exceptions for decision support."""

from __future__ import annotations

from fastapi import status

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class DecisionSupportError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "DECISION_SUPPORT_ERROR"


class WorkflowRunNotFoundError(ResourceNotFoundError):
    code = "DECISION_SUPPORT_RUN_NOT_FOUND"


class WorkflowTaskNotFoundError(ResourceNotFoundError):
    code = "DECISION_SUPPORT_TASK_NOT_FOUND"
