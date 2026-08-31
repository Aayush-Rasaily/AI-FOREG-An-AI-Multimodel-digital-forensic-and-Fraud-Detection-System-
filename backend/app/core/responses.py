"""Shared API response contracts."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ApiResponse[ResponseData](BaseModel):
    """Consistent successful response envelope."""

    success: Literal[True] = True
    data: ResponseData
    request_id: UUID | None = None
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )


class ErrorDetail(BaseModel):
    """Client-safe details for one application error."""

    code: str
    message: str
    request_id: UUID | None = None
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Consistent unsuccessful response envelope."""

    success: Literal[False] = False
    error: ErrorDetail
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
