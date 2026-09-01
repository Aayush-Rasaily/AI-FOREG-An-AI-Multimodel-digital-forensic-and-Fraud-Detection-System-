"""API schemas for AI video forensic analysis."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.ai.video.models.base import (
    DetectionMethod,
    VideoAnalysisRunStatus,
    VideoFindingCategory,
)
from backend.app.forensics.models import Severity


class TemporalEvidenceResponse(BaseModel):
    """Temporal localization attached to a video finding."""

    model_config = ConfigDict(extra="forbid")

    start_frame: int | None = None
    end_frame: int | None = None
    start_timestamp_ms: int | None = None
    end_timestamp_ms: int | None = None
    evidence_type: str = "TEMPORAL_INCONSISTENCY"


class VideoFindingRegionResponse(BaseModel):
    """Localized region attached to a video AI finding."""

    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(ge=0)
    height: float = Field(ge=0)
    frame_number: int | None = None
    timestamp_ms: int | None = None
    polygon: list[tuple[float, float]] | None = None
    normalized_location: dict[str, float] | None = None


class VideoAIFindingResponse(BaseModel):
    """One persisted video AI finding."""

    id: UUID
    analysis_run_id: UUID
    detector: str
    category: VideoFindingCategory
    severity: Severity
    confidence: float | None = Field(default=None, ge=0, le=1)
    method: DetectionMethod
    description: str
    explanation: str
    recommendation: str | None
    model_name: str
    model_version: str
    model_framework: str
    temporal: TemporalEvidenceResponse | None
    artifact_id: UUID | None
    regions: list[VideoFindingRegionResponse]
    metadata: dict[str, Any]
    limitations: str | None
    created_at: datetime


class VideoAIFindingListResponse(BaseModel):
    """Bounded video AI findings for one evidence item."""

    items: list[VideoAIFindingResponse]
    total: int
    limit: int
    offset: int


class VideoFrameResponse(BaseModel):
    """One sampled frame reference."""

    frame_index: int
    frame_number: int
    timestamp_ms: int
    timestamp_seconds: float
    frame_id: str
    artifact_id: UUID | None = None
    width: int | None = None
    height: int | None = None


class VideoTimelineEntryResponse(BaseModel):
    """One timeline entry derived from findings."""

    detector: str
    category: str
    severity: str
    confidence: float | None
    method: str
    start_frame: int | None
    end_frame: int | None
    start_timestamp_ms: int | None
    end_timestamp_ms: int | None
    description: str


class VideoAnalysisRunResponse(BaseModel):
    """One AI video analysis execution."""

    id: UUID
    evidence_id: UUID
    status: VideoAnalysisRunStatus
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
    video: dict[str, Any] | None = None


class VideoAnalysisRunListResponse(BaseModel):
    """AI video analysis history for one evidence item."""

    items: list[VideoAnalysisRunResponse]
    total: int
    limit: int
    offset: int


class VideoAnalysisDetailResponse(VideoAnalysisRunResponse):
    """Detailed analysis response including timeline and frames."""

    timeline: list[VideoTimelineEntryResponse]
    frames: list[VideoFrameResponse]
    artifacts: list[dict[str, Any]]
