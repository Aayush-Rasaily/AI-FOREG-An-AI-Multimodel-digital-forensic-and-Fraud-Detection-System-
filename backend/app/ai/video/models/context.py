"""Video analysis context supplied to detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from backend.app.ai.video.models.base import VideoFrameReference
from backend.app.domain.processing import EvidenceClassification


@dataclass(frozen=True, slots=True)
class VideoAnalysisContext:
    """Inputs supplied to video AI detectors."""

    evidence_id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    storage_key: str
    classification: EvidenceClassification
    source_sha256: str
    storage: Any
    settings: Any
    video_settings: Any
    duration_ms: int | None = None
    fps: float | None = None
    frame_count: int | None = None
    width: int | None = None
    height: int | None = None
    codec: str | None = None
    container: str | None = None
    sampled_frames: tuple[VideoFrameReference, ...] = ()
    frame_index_artifact: dict[str, Any] = field(default_factory=dict)
    extraction_metadata: dict[str, Any] = field(default_factory=dict)
    extraction_artifacts: tuple[dict[str, Any], ...] = ()
    device: str = "cpu"
    preprocessing: dict[str, Any] = field(default_factory=dict)
