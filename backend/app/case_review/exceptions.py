"""Domain exceptions for case review."""

from __future__ import annotations

from fastapi import status

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class CaseReviewError(ApplicationError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "CASE_REVIEW_ERROR"


class CaseReviewNotFoundError(ResourceNotFoundError):
    code = "CASE_REVIEW_NOT_FOUND"


class ChecklistItemNotFoundError(ResourceNotFoundError):
    code = "CASE_REVIEW_CHECKLIST_ITEM_NOT_FOUND"
