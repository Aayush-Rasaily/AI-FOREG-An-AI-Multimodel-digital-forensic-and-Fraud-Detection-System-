"""API schemas for reference comparison runs and differences."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.comparison.models import (
    ComparisonRunStatus,
    DifferenceSeverity,
    DifferenceType,
)


class CompareRequest(BaseModel):
    """Request body to compare questioned evidence against a reference."""

    model_config = ConfigDict(extra="forbid")

    reference_evidence_id: UUID


class ReferenceEvidenceCreateRequest(BaseModel):
    """Register existing processed evidence as a trusted reference."""

    model_config = ConfigDict(extra="forbid")

    evidence_id: UUID
    label: str = Field(min_length=1, max_length=128)
    description: str | None = None


class ReferenceEvidenceResponse(BaseModel):
    """One immutable trusted reference record."""

    id: UUID
    case_id: UUID
    evidence_id: UUID
    label: str
    description: str | None
    reference_hash: str
    original_filename: str
    mime_type: str
    metadata: dict[str, Any]
    created_at: datetime


class ReferenceEvidenceListResponse(BaseModel):
    """References registered for one case."""

    items: list[ReferenceEvidenceResponse]
    total: int
    limit: int
    offset: int


class DifferenceRegionResponse(BaseModel):
    """Localized region attached to a comparison difference."""

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    page_number: int | None = None
    frame_number: int | None = None
    polygon: list[tuple[float, float]] | None = None
    normalized_location: dict[str, float] | None = None


class DifferenceResponse(BaseModel):
    """One persisted comparison difference."""

    id: UUID
    comparison_run_id: UUID
    matcher: str
    difference_type: DifferenceType
    severity: DifferenceSeverity
    confidence: float = Field(ge=0, le=1)
    description: str
    explanation: str
    original_value: str | None
    submitted_value: str | None
    regions: list[DifferenceRegionResponse]
    metadata: dict[str, Any]
    created_at: datetime


class DifferenceListResponse(BaseModel):
    """Bounded differences for one evidence item."""

    items: list[DifferenceResponse]
    total: int
    limit: int
    offset: int


class ComparisonRunResponse(BaseModel):
    """One reference comparison execution."""

    id: UUID
    evidence_id: UUID
    reference_evidence_id: UUID
    reference_record_id: UUID
    status: ComparisonRunStatus
    engine_version: str
    differences_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]


class ComparisonRunListResponse(BaseModel):
    """Comparison history for one evidence item."""

    items: list[ComparisonRunResponse]
    total: int
    limit: int
    offset: int


class ComparisonSummaryResponse(BaseModel):
    """Latest comparison summary."""

    status: ComparisonRunStatus
    comparison_run_id: UUID | None
    differences_count: int
    type_counts: dict[str, int]
    error_code: str | None = None
