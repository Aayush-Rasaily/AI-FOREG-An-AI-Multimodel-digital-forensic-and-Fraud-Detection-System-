"""API schemas for extraction records and localized evidence."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.extraction.models import (
    ExtractionSourceType,
    ExtractionStatus,
    ExtractionType,
)


class BoundingBoxResponse(BaseModel):
    """Top-left origin coordinates in source or normalized units."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)


class NormalizedBoundingBoxResponse(BoundingBoxResponse):
    """A box bounded to the source in normalized coordinates."""

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(ge=0, le=1)
    height: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def stays_inside_source(self) -> "NormalizedBoundingBoxResponse":
        """Prevent boxes that extend beyond the normalized source."""

        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("Normalized boxes must remain inside the source.")
        return self


class ExtractionResponse(BaseModel):
    """One provenance-preserving extraction record."""

    id: UUID
    evidence_id: UUID
    artifact_id: UUID | None
    extraction_type: ExtractionType
    source_type: ExtractionSourceType
    source_identifier: str
    page_number: int | None
    frame_number: int | None
    timestamp_ms: int | None
    content: str | None
    confidence: float | None = Field(default=None, ge=0, le=1)
    location: BoundingBoxResponse | None
    normalized_location: NormalizedBoundingBoxResponse | None
    method: str
    version: str
    metadata: dict[str, object]
    created_at: datetime


class ExtractionListResponse(BaseModel):
    """Bounded extraction records plus run capability status."""

    status: ExtractionStatus
    error_code: str | None
    items: list[ExtractionResponse]
    total: int
    limit: int
    offset: int
