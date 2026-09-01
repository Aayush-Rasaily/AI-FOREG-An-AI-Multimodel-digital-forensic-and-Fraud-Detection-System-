"""API schemas for forensic analysis runs and findings."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.forensics.models import (
    AnalysisRunStatus,
    FindingCategory,
    Severity,
)


class FindingRegionResponse(BaseModel):
    """Localized region attached to a forensic finding."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    page_number: int | None = None
    frame_number: int | None = None
    polygon: list[tuple[float, float]] | None = None
    normalized_location: dict[str, float] | None = None


class FindingResponse(BaseModel):
    """One persisted forensic finding."""

    id: UUID
    analysis_run_id: UUID
    detector: str
    category: FindingCategory
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    description: str
    explanation: str
    recommendation: str | None
    regions: list[FindingRegionResponse]
    metadata: dict[str, Any]
    created_at: datetime


class FindingListResponse(BaseModel):
    """Bounded findings for one evidence item."""

    items: list[FindingResponse]
    total: int
    limit: int
    offset: int


class AnalysisRunResponse(BaseModel):
    """One forensic analysis execution."""

    id: UUID
    evidence_id: UUID
    status: AnalysisRunStatus
    engine_version: str
    findings_count: int
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]


class AnalysisRunListResponse(BaseModel):
    """Analysis history for one evidence item."""

    items: list[AnalysisRunResponse]
    total: int
    limit: int
    offset: int


class AnalysisSummaryResponse(BaseModel):
    """Latest analysis summary with finding counts by severity."""

    status: AnalysisRunStatus
    analysis_run_id: UUID | None
    findings_count: int
    severity_counts: dict[str, int]
    error_code: str | None = None
