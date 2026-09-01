"""Domain models for AI image forensic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

import numpy as np

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import RegionBox, Severity


class ImageFindingCategory(StrEnum):
    """Categories for AI image forensic findings."""

    AI_GENERATED = "AI_GENERATED"
    DEEPFAKE = "DEEPFAKE"
    MANIPULATION = "MANIPULATION"
    LOGO = "LOGO"
    ID_DOCUMENT = "ID_DOCUMENT"
    IMAGE = "IMAGE"


class ImageAnalysisRunStatus(StrEnum):
    """Lifecycle for one AI image analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class ImageDetectorMetadata:
    """Metadata reported by one image AI detector."""

    name: str
    version: str
    author: str
    description: str
    supported_tasks: tuple[str, ...]
    model_name: str
    model_version: str
    framework: str

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
        }


@dataclass(frozen=True, slots=True)
class ImageAnalysisContext:
    """Inputs supplied to image AI detectors."""

    evidence_id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    storage_key: str
    classification: EvidenceClassification
    source_sha256: str
    storage: Any
    settings: Any
    image_array: np.ndarray
    width: int
    height: int
    device: str = "cpu"
    preprocessing: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ImageAIFindingItem:
    """One normalized AI image finding."""

    detector: str
    category: ImageFindingCategory
    severity: Severity
    confidence: float
    description: str
    explanation: str
    regions: tuple[RegionBox, ...] = ()
    recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    model_name: str = ""
    model_version: str = ""
    model_framework: str = ""
    heatmap_artifact_key: str | None = None
    mask_artifact_key: str | None = None


@dataclass(frozen=True, slots=True)
class ImageDetectorOutput:
    """Output from one image AI detector."""

    detector: str
    version: str
    findings: tuple[ImageAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""


@dataclass(frozen=True, slots=True)
class ImageAnalysisResult:
    """Aggregated output from all enabled image AI detectors."""

    status: ImageAnalysisRunStatus
    findings: tuple[ImageAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    detector_outputs: tuple[ImageDetectorOutput, ...] = ()
    latency_ms: float = 0.0
    device: str = "cpu"
    error_code: str | None = None
    error_message_safe: str | None = None
