"""API schemas for AI image forensic analysis."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.ai.image.models import ImageAnalysisRunStatus, ImageFindingCategory
from backend.app.forensics.models import Severity


class ImageFindingRegionResponse(BaseModel):
    """Localized region attached to an AI image finding."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    page_number: int | None = None
    frame_number: int | None = None
    polygon: list[tuple[float, float]] | None = None
    normalized_location: dict[str, float] | None = None


class ImageAIFindingResponse(BaseModel):
    """One persisted AI image finding."""

    id: UUID
    analysis_run_id: UUID
    detector: str
    category: ImageFindingCategory
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    description: str
    explanation: str
    recommendation: str | None
    model_name: str
    model_version: str
    model_framework: str
    heatmap_artifact_id: UUID | None
    mask_artifact_id: UUID | None
    regions: list[ImageFindingRegionResponse]
    metadata: dict[str, Any]
    created_at: datetime


class ImageAIFindingListResponse(BaseModel):
    """Bounded AI image findings for one evidence item."""

    items: list[ImageAIFindingResponse]
    total: int
    limit: int
    offset: int


class ImageAnalysisRunResponse(BaseModel):
    """One AI image analysis execution."""

    id: UUID
    evidence_id: UUID
    status: ImageAnalysisRunStatus
    engine_version: str
    device: str
    latency_ms: float | None
    findings_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]


class ImageAnalysisRunListResponse(BaseModel):
    """AI image analysis history for one evidence item."""

    items: list[ImageAnalysisRunResponse]
    total: int
    limit: int
    offset: int
