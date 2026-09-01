"""API schemas for AI audio forensic analysis."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.ai.audio.models import (
    AudioAnalysisRunStatus,
    AudioFindingCategory,
    DetectionMethod,
)
from backend.app.forensics.models import Severity


class AudioAnalysisRequest(BaseModel):
    """Optional parameters when queueing audio AI analysis."""

    model_config = ConfigDict(extra="forbid")

    reference_evidence_id: UUID | None = None


class TemporalEvidenceResponse(BaseModel):
    """Temporal localization attached to an audio finding."""

    model_config = ConfigDict(extra="forbid")

    start_time_ms: int | None = None
    end_time_ms: int | None = None
    duration_ms: int | None = None
    evidence_type: str = "TEMPORAL_INCONSISTENCY"


class AudioFindingRegionResponse(BaseModel):
    """Localized region attached to an audio AI finding."""

    model_config = ConfigDict(extra="forbid")

    segment_id: str | None = None
    start_time_ms: int | None = None
    end_time_ms: int | None = None
    duration_ms: int | None = None
    metrics: dict[str, Any] | None = None


class AudioAIFindingResponse(BaseModel):
    """One persisted audio AI finding."""

    id: UUID
    analysis_run_id: UUID
    detector: str
    category: AudioFindingCategory
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
    regions: list[AudioFindingRegionResponse]
    metadata: dict[str, Any]
    limitations: str | None
    created_at: datetime


class AudioAIFindingListResponse(BaseModel):
    """Bounded audio AI findings for one evidence item."""

    items: list[AudioAIFindingResponse]
    total: int
    limit: int
    offset: int


class AudioTimelineEntryResponse(BaseModel):
    """One timeline entry derived from findings."""

    detector: str
    category: str
    severity: str
    confidence: float | None
    method: str
    start_time_ms: int | None
    end_time_ms: int | None
    duration_ms: int | None
    description: str


class AudioSegmentResponse(BaseModel):
    """One localized segment derived from findings."""

    segment_id: str
    detector: str
    category: str
    severity: str
    confidence: float | None
    start_time_ms: int | None
    end_time_ms: int | None
    duration_ms: int | None
    description: str


class AudioFeatureSummaryResponse(BaseModel):
    """Deterministic feature summary for one analysis run."""

    sample_rate: int
    duration_seconds: float
    channels: int
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid_hz: float
    mfcc_mean: list[float]
    window_count: int


class AudioAnalysisRunResponse(BaseModel):
    """One AI audio analysis execution."""

    id: UUID
    evidence_id: UUID
    reference_evidence_id: UUID | None
    status: AudioAnalysisRunStatus
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
    audio: dict[str, Any] | None = None


class AudioAnalysisRunListResponse(BaseModel):
    """AI audio analysis history for one evidence item."""

    items: list[AudioAnalysisRunResponse]
    total: int
    limit: int
    offset: int


class AudioAnalysisDetailResponse(AudioAnalysisRunResponse):
    """Detailed analysis response including timeline and features."""

    timeline: list[AudioTimelineEntryResponse]
    segments: list[AudioSegmentResponse]
    features: AudioFeatureSummaryResponse | None
    artifacts: list[dict[str, Any]]
