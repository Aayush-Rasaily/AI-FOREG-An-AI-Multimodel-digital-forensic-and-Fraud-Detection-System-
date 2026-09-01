"""API schemas for document AI forensic analysis."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.ai.document.models.base import (
    DetectionMethod,
    DocumentAnalysisRunStatus,
    DocumentFindingCategory,
)
from backend.app.forensics.models import Severity


class DocumentFindingRegionResponse(BaseModel):
    """Localized region attached to a document AI finding."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    page_number: int | None = None
    frame_number: int | None = None
    polygon: list[tuple[float, float]] | None = None
    normalized_location: dict[str, float] | None = None


class DocumentAIFindingResponse(BaseModel):
    """One persisted document AI finding."""

    id: UUID
    analysis_run_id: UUID
    detector: str
    category: DocumentFindingCategory
    severity: Severity
    method: DetectionMethod
    confidence: float | None = Field(default=None, ge=0, le=1)
    description: str
    explanation: str
    recommendation: str | None
    model_name: str
    model_version: str
    model_framework: str
    artifact_id: UUID | None
    regions: list[DocumentFindingRegionResponse]
    metadata: dict[str, Any]
    created_at: datetime


class DocumentAIFindingListResponse(BaseModel):
    """Bounded document AI findings for one evidence item."""

    items: list[DocumentAIFindingResponse]
    total: int
    limit: int
    offset: int


class DocumentAnalysisRunResponse(BaseModel):
    """One document AI analysis execution."""

    id: UUID
    evidence_id: UUID
    status: DocumentAnalysisRunStatus
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


class DocumentAnalysisRunListResponse(BaseModel):
    """Document AI analysis history for one evidence item."""

    items: list[DocumentAnalysisRunResponse]
    total: int
    limit: int
    offset: int
