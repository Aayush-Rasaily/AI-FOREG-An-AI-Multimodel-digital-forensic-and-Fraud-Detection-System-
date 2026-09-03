"""Domain models for cross-evidence correlation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID


class CorrelationRunStatus(StrEnum):
    """Lifecycle states for one correlation analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class CorrelationType(StrEnum):
    """Deterministic cross-evidence relationship types supported by Phase 7B."""

    SAME_HASH = "same_hash"
    SAME_EMAIL = "same_email"
    SAME_PHONE = "same_phone"
    SAME_DEVICE = "same_device"
    SAME_CAMERA = "same_camera"
    SAME_SIGNATURE = "same_signature"
    SAME_LOGO = "same_logo"
    SAME_QR = "same_qr"
    SAME_AUDIO_SPEAKER = "same_audio_speaker"
    SAME_LOCATION = "same_location"
    SAME_DOCUMENT = "same_document"
    SIMILAR_FILENAME = "similar_filename"
    TEMPORAL_OVERLAP = "temporal_overlap"
    SHARED_METADATA = "shared_metadata"
    SHARED_IDENTIFIER = "shared_identifier"


@dataclass(frozen=True)
class CorrelationSupport:
    """One supporting artifact or finding behind a correlation."""

    support_kind: str
    support_id: str
    label: str
    value: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvidenceCorrelation:
    """One deterministic relationship between two evidence items."""

    correlation_id: str
    case_id: UUID
    left_evidence_id: UUID
    right_evidence_id: UUID
    correlation_type: CorrelationType
    score: float
    confidence: float
    explanation: str
    supporting_findings: tuple[str, ...] = ()
    supporting_metadata: dict[str, Any] = field(default_factory=dict)
    supporting_entities: tuple[str, ...] = ()
    supports: tuple[CorrelationSupport, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CorrelationBuildResult:
    """Engine output for one correlation analysis."""

    correlations: tuple[EvidenceCorrelation, ...]
    provenance: dict[str, Any]
    metadata: dict[str, Any]
