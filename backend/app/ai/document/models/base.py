"""Core domain types for document AI forensic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from backend.app.ai.document.models.context import DocumentAnalysisContext
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.forensics.models import RegionBox, Severity


class DocumentFindingCategory(StrEnum):
    """Categories for document AI findings."""

    TAMPERING = "TAMPERING"
    TEXT_INCONSISTENCY = "TEXT_INCONSISTENCY"
    FONT_INCONSISTENCY = "FONT_INCONSISTENCY"
    LAYOUT_INCONSISTENCY = "LAYOUT_INCONSISTENCY"
    LOGO = "LOGO"
    METADATA = "METADATA"
    REGION_ANOMALY = "REGION_ANOMALY"
    DATE_INCONSISTENCY = "DATE_INCONSISTENCY"
    NUMBER_INCONSISTENCY = "NUMBER_INCONSISTENCY"
    REFERENCE_MISMATCH = "REFERENCE_MISMATCH"
    SIGNATURE = "SIGNATURE"
    ID_DOCUMENT = "ID_DOCUMENT"
    CAPABILITY = "CAPABILITY"


class DocumentAnalysisRunStatus(StrEnum):
    """Lifecycle for one document AI analysis run."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class DetectionMethod(StrEnum):
    """How a finding was produced."""

    CLASSICAL = "classical"
    AI = "ai"
    REFERENCE = "reference"


class DetectorCapabilityStatus(StrEnum):
    """Capability state when a model or detector is unavailable."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class DocumentDetectorMetadata:
    """Metadata reported by one document AI detector."""

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
class DocumentAIFindingItem:
    """One normalized document AI finding."""

    detector: str
    category: DocumentFindingCategory
    severity: Severity
    description: str
    explanation: str
    method: DetectionMethod
    confidence: float | None = None
    regions: tuple[RegionBox, ...] = ()
    recommendation: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    model_name: str = ""
    model_version: str = ""
    model_framework: str = ""
    capability_status: DetectorCapabilityStatus | None = None


@dataclass(frozen=True, slots=True)
class DocumentDetectorOutput:
    """Output from one document AI detector."""

    detector: str
    version: str
    findings: tuple[DocumentAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    model_name: str = ""
    model_version: str = ""
    method: DetectionMethod = DetectionMethod.CLASSICAL


@dataclass(frozen=True, slots=True)
class DocumentAnalysisResult:
    """Aggregated output from all enabled document AI detectors."""

    status: DocumentAnalysisRunStatus
    findings: tuple[DocumentAIFindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    detector_outputs: tuple[DocumentDetectorOutput, ...] = ()
    latency_ms: float = 0.0
    device: str = "cpu"
    error_code: str | None = None
    error_message_safe: str | None = None


__all__ = [
    "DetectionMethod",
    "DetectorCapabilityStatus",
    "DocumentAIFindingItem",
    "DocumentAnalysisContext",
    "DocumentAnalysisResult",
    "DocumentAnalysisRunStatus",
    "DocumentDetectorMetadata",
    "DocumentDetectorOutput",
    "DocumentFindingCategory",
]
