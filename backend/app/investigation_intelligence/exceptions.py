"""Domain exceptions for investigation intelligence."""

from __future__ import annotations

from fastapi import status

from backend.app.core.exceptions import ApplicationError, ResourceNotFoundError


class InvestigationIntelligenceError(ApplicationError):
    """Base error for Phase 9C intelligence operations."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "INVESTIGATION_INTELLIGENCE_ERROR"


class IntelligenceRunNotFoundError(ResourceNotFoundError):
    """Raised when a persisted intelligence run cannot be located."""

    code = "INVESTIGATION_INTELLIGENCE_NOT_FOUND"


class HypothesisNotFoundError(ResourceNotFoundError):
    """Raised when a hypothesis record is missing."""

    code = "HYPOTHESIS_NOT_FOUND"
