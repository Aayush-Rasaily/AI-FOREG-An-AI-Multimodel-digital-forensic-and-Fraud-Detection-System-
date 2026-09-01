"""Framework-independent forensic analysis contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import EvidenceClassification


class Severity(StrEnum):
    """Controlled finding severity levels."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FindingCategory(StrEnum):
    """Controlled forensic finding categories."""

    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    METADATA = "METADATA"
    COMPRESSION = "COMPRESSION"
    COPY_MOVE = "COPY_MOVE"
    SPLICING = "SPLICING"
    LAYOUT = "LAYOUT"
    FONT = "FONT"
    OVERLAY = "OVERLAY"
    NOISE = "NOISE"
    EDGE = "EDGE"
    DATE = "DATE"
    NUMBER = "NUMBER"
    OTHER = "OTHER"


class AnalysisRunStatus(StrEnum):
    """Forensic analysis run lifecycle."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class RegionBox:
    """Top-left origin region in pixel or normalized units."""

    x: float
    y: float
    width: float
    height: float
    page_number: int | None = None
    frame_number: int | None = None
    polygon: tuple[tuple[float, float], ...] | None = None
    normalized: RegionBox | None = None


@dataclass(frozen=True, slots=True)
class FindingItem:
    """One deterministic detector finding with provenance."""

    detector: str
    category: FindingCategory
    severity: Severity
    confidence: float
    description: str
    explanation: str
    regions: tuple[RegionBox, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    recommendation: str | None = None


@dataclass(frozen=True, slots=True)
class AnalysisContext:
    """Inputs supplied to every forensic detector."""

    evidence_id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    storage_key: str
    classification: EvidenceClassification
    source_sha256: str
    storage: Any
    settings: Any
    extraction_records: tuple[dict[str, Any], ...] = ()
    extraction_artifacts: tuple[dict[str, Any], ...] = ()
    image_width: int | None = None
    image_height: int | None = None


@dataclass(frozen=True, slots=True)
class DetectorResult:
    """Output from one forensic detector plugin."""

    detector: str
    version: str
    findings: tuple[FindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Aggregated output from all compatible detectors."""

    status: AnalysisRunStatus
    findings: tuple[FindingItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message_safe: str | None = None
