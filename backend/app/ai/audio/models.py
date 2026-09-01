"""Domain models for AI audio forensic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

import numpy as np

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class AudioFindingCategory(StrEnum):
    """Categories for audio AI findings."""

    SYNTHETIC_AUDIO = "SYNTHETIC_AUDIO"
    VOICE_CLONE = "VOICE_CLONE"
    DEEPFAKE_VOICE = "DEEPFAKE_VOICE"
    SPEAKER_INCONSISTENCY = "SPEAKER_INCONSISTENCY"
    REFERENCE_MISMATCH = "REFERENCE_MISMATCH"
    SPLICING = "SPLICING"
    WAVEFORM = "WAVEFORM"
    SPECTRAL = "SPECTRAL"
    COMPRESSION = "COMPRESSION"
    NOISE = "NOISE"
    SILENCE = "SILENCE"
    METADATA = "METADATA"
    CAPABILITY = "CAPABILITY"
    AUDIO = "AUDIO"


class AudioAnalysisRunStatus(StrEnum):
    """Lifecycle for one audio AI analysis run."""

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
    REFERENCE = "reference"


class DetectorCapabilityStatus(StrEnum):
    """Capability state when a model or detector is unavailable."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TemporalEvidence:
    """Temporal localization for an audio finding."""

    start_time_ms: int | None = None
    end_time_ms: int | None = None
    duration_ms: int | None = None
    evidence_type: str = "TEMPORAL_INCONSISTENCY"

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_time_ms": self.start_time_ms,
            "end_time_ms": self.end_time_ms,
            "duration_ms": self.duration_ms,
            "evidence_type": self.evidence_type,
        }


@dataclass(frozen=True, slots=True)
class AudioFeatureSummary:
    """Deterministic feature summary for one audio analysis."""

    sample_rate: int
    duration_seconds: float
    channels: int
    rms_energy: float
    zero_crossing_rate: float
    spectral_centroid_hz: float
    mfcc_mean: tuple[float, ...] = ()
    window_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_rate": self.sample_rate,
            "duration_seconds": self.duration_seconds,
            "channels": self.channels,
            "rms_energy": round(self.rms_energy, 6),
            "zero_crossing_rate": round(self.zero_crossing_rate, 6),
            "spectral_centroid_hz": round(self.spectral_centroid_hz, 3),
            "mfcc_mean": [round(value, 4) for value in self.mfcc_mean],
            "window_count": self.window_count,
        }


@dataclass(frozen=True, slots=True)
class AudioDetectorMetadata:
    """Metadata reported by one audio AI detector."""

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
            "detector_id": self.name,
            "detector_name": self.name,
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
class AudioAnalysisContext:
    """Inputs supplied to audio AI detectors."""

    evidence_id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    storage_key: str
    classification: EvidenceClassification
    source_sha256: str
    storage: Any
    settings: Any
    audio_settings: Any
    duration_ms: int | None = None
    sample_rate: int | None = None
    channels: int | None = None
    codec: str | None = None
    bit_depth: int | None = None
    frame_count: int | None = None
    samples: np.ndarray | None = None
    reference_evidence_id: UUID | None = None
    reference_samples: np.ndarray | None = None
    reference_sample_rate: int | None = None
    extraction_metadata: dict[str, Any] = field(default_factory=dict)
    feature_summary: AudioFeatureSummary | None = None
    capabilities: dict[str, bool] = field(default_factory=dict)
    device: str = "cpu"
    preprocessing: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AudioAIFindingItem:
    """One normalized audio AI finding."""

    detector: str
    category: AudioFindingCategory
    severity: Severity
    description: str
    explanation: str
    method: DetectionMethod
    confidence: float | None = None
    temporal: TemporalEvidence | None = None
    recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    model_name: str = ""
    model_version: str = ""
    model_framework: str = ""
    capability_status: DetectorCapabilityStatus | None = None
    limitations: str | None = None


@dataclass(frozen=True, slots=True)
class AudioDetectorOutput:
    """Output from one audio AI detector."""

    detector: str
    version: str
    findings: tuple[AudioAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""
    method: DetectionMethod = DetectionMethod.CLASSICAL
    status: DetectorCapabilityStatus = DetectorCapabilityStatus.AVAILABLE


@dataclass(frozen=True, slots=True)
class AudioAnalysisResult:
    """Aggregated output from all enabled audio AI detectors."""

    status: AudioAnalysisRunStatus
    findings: tuple[AudioAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    detector_outputs: tuple[AudioDetectorOutput, ...] = ()
    timeline: tuple[dict[str, Any], ...] = ()
    segments: tuple[dict[str, Any], ...] = ()
    feature_summary: AudioFeatureSummary | None = None
    latency_ms: float = 0.0
    device: str = "cpu"
    error_code: str | None = None
    error_message_safe: str | None = None
