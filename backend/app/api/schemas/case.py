"""Pydantic contracts for case management APIs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.domain.case import CasePriority, CaseStatus


class CaseCreateRequest(BaseModel):
    """Client input for creating a case."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    priority: CasePriority = CasePriority.MEDIUM


class CaseUpdateRequest(BaseModel):
    """Optional fields accepted by the case PATCH endpoint."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=10_000)
    status: CaseStatus | None = None
    priority: CasePriority | None = None


class CaseResponse(BaseModel):
    """Public case representation."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    case_number: str
    title: str
    description: str | None
    status: CaseStatus
    priority: CasePriority
    created_at: datetime
    updated_at: datetime


class CaseListResponse(BaseModel):
    """Paginated case collection."""

    items: list[CaseResponse]
    total: int
    limit: int
    offset: int
