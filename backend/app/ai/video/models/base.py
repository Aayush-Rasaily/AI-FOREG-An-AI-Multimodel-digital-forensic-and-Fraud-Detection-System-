"""Core domain types for video AI forensic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.forensics.models import RegionBox, Severity


class VideoFindingCategory(StrEnum):
    """Categories for video AI findings."""

    DEEPFAKE = "DEEPFAKE"
    SYNTHETIC_VIDEO = "SYNTHETIC_VIDEO"
    FRAME_MANIPULATION = "FRAME_MANIPULATION"
    TEMPORAL_INCONSISTENCY = "TEMPORAL_INCONSISTENCY"
    FACE_MANIPULATION = "FACE_MANIPULATION"
    FACE_INCONSISTENCY = "FACE_INCONSISTENCY"
    COMPRESSION = "COMPRESSION"
    METADATA = "METADATA"
    CAPABILITY = "CAPABILITY"
    VIDEO = "VIDEO"


class VideoAnalysisRunStatus(StrEnum):
    """Lifecycle for one video AI analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"
    CANCELLED = "CANCELLED"


class DetectionMethod(StrEnum):
    """How a finding was produced."""

    CLASSICAL = "classical"
    AI = "ai"


class DetectorCapabilityStatus(StrEnum):
    """Capability state when a model or detector is unavailable."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class TemporalEvidence:
    """Temporal localization for a video finding."""

    start_frame: int | None = None
    end_frame: int | None = None
    start_timestamp_ms: int | None = None
    end_timestamp_ms: int | None = None
    evidence_type: str = "TEMPORAL_INCONSISTENCY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_frame": self.start_frame,
            "end_frame": self.end_frame,
            "start_timestamp_ms": self.start_timestamp_ms,
            "end_timestamp_ms": self.end_timestamp_ms,
            "evidence_type": self.evidence_type,
        }


@dataclass(frozen=True, slots=True)
class VideoFrameReference:
    """One sampled frame with deterministic identity."""

    frame_index: int
    frame_number: int
    timestamp_ms: int
    timestamp_seconds: float
    source_video_hash: str
    frame_id: str
    width: int | None = None
    height: int | None = None
    image_array: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_index": self.frame_index,
            "frame_number": self.frame_number,
            "timestamp_ms": self.timestamp_ms,
            "timestamp_seconds": self.timestamp_seconds,
            "source_video_hash": self.source_video_hash,
            "frame_id": self.frame_id,
            "width": self.width,
            "height": self.height,
        }


@dataclass(frozen=True, slots=True)
class VideoDetectorMetadata:
    """Metadata reported by one video AI detector."""

    name: str
    version: str
    author: str
    description: str
    supported_tasks: tuple[str, ...]
    model_name: str
    model_version: str
    framework: str
    method: DetectionMethod

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "supported_tasks": list(self.supported_tasks),
            "model_name": self.model_name,
            "model_version": self.model_version,
            "framework": self.framework,
            "method": self.method.value,
        }


@dataclass(frozen=True, slots=True)
class VideoAIFindingItem:
    """One normalized video AI finding."""

    detector: str
    category: VideoFindingCategory
    severity: Severity
    description: str
    explanation: str
    method: DetectionMethod
    confidence: float | None = None
    regions: tuple[RegionBox, ...] = ()
    temporal: TemporalEvidence | None = None
    recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    model_name: str = ""
    model_version: str = ""
    model_framework: str = ""
    capability_status: DetectorCapabilityStatus | None = None
    limitations: str | None = None


@dataclass(frozen=True, slots=True)
class VideoDetectorOutput:
    """Output from one video AI detector."""

    detector: str
    version: str
    findings: tuple[VideoAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""
    method: DetectionMethod = DetectionMethod.CLASSICAL


@dataclass(frozen=True, slots=True)
class VideoAnalysisResult:
    """Aggregated output from all enabled video AI detectors."""

    status: VideoAnalysisRunStatus
    findings: tuple[VideoAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    detector_outputs: tuple[VideoDetectorOutput, ...] = ()
    timeline: tuple[dict[str, Any], ...] = ()
    sampled_frames: tuple[VideoFrameReference, ...] = ()
    latency_ms: float = 0.0
    device: str = "cpu"
    error_code: str | None = None
    error_message_safe: str | None = None


from backend.app.ai.video.models.context import (  # noqa: E402
    VideoAnalysisContext as VideoAnalysisContext,
)
