"""Domain models for the investigation timeline engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class TimelineRunStatus(StrEnum):
    """Lifecycle states for one timeline reconstruction run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class TimelineEventType(StrEnum):
    """Supported timeline event categories."""

    EVIDENCE_UPLOADED = "evidence_uploaded"
    EVIDENCE_UPDATED = "evidence_updated"
    PROCESSING_QUEUED = "processing_queued"
    PROCESSING_STARTED = "processing_started"
    PROCESSING_COMPLETED = "processing_completed"
    EXTRACTION_COMPLETED = "extraction_completed"
    CUSTODY_EVENT = "custody_event"
    FORENSIC_ANALYSIS_COMPLETED = "forensic_analysis_completed"
    IMAGE_AI_COMPLETED = "image_ai_completed"
    DOCUMENT_AI_COMPLETED = "document_ai_completed"
    SIGNATURE_AI_COMPLETED = "signature_ai_completed"
    VIDEO_AI_COMPLETED = "video_ai_completed"
    AUDIO_AI_COMPLETED = "audio_ai_completed"
    FUSION_COMPLETED = "fusion_completed"
    CASE_INTELLIGENCE_COMPLETED = "case_intelligence_completed"
    REPORT_GENERATED = "report_generated"
    METADATA_TIMESTAMP = "metadata_timestamp"
    TIMESTAMP_MISSING = "timestamp_missing"


class TimelineConflictType(StrEnum):
    """Detected timestamp inconsistencies."""

    MULTIPLE_TIMESTAMPS = "multiple_timestamps"
    FILESYSTEM_BEFORE_EXIF = "filesystem_before_exif"
    FUTURE_TIMESTAMP = "future_timestamp"
    CLOCK_DRIFT = "clock_drift"
    TIMEZONE_MISMATCH = "timezone_mismatch"
    DUPLICATE_EVENT = "duplicate_event"


@dataclass(frozen=True)
class NormalizedTimestamp:
    """Normalized timestamp with confidence metadata."""

    original_timestamp: datetime | None
    normalized_timestamp: datetime | None
    timezone: str | None
    confidence: float
    uncertainty_ms: int


@dataclass(frozen=True)
class TimelineEvent:
    """One chronological investigation event."""

    event_id: str
    case_id: UUID
    evidence_id: UUID | None
    event_type: TimelineEventType
    timestamp: datetime | None
    timezone: str | None
    normalized_timestamp: datetime | None
    confidence: float
    uncertainty_ms: int
    description: str
    source: str
    source_id: str
    provenance: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    supporting_artifacts: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TimelineConflict:
    """One persisted timestamp conflict."""

    conflict_id: str
    conflict_type: TimelineConflictType
    evidence_id: UUID | None
    involved_event_ids: tuple[str, ...]
    explanation: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TimelineBuildResult:
    """Engine output for one timeline reconstruction."""

    events: tuple[TimelineEvent, ...]
    conflicts: tuple[TimelineConflict, ...]
    provenance: dict[str, Any]
    metadata: dict[str, Any]
