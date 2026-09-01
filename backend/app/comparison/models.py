"""Framework-independent comparison contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import EvidenceClassification


class ComparisonRunStatus(StrEnum):
    """Comparison run lifecycle."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class DifferenceType(StrEnum):
    """Controlled difference categories."""

    TEXT_CHANGED = "TEXT_CHANGED"
    TEXT_INSERTED = "TEXT_INSERTED"
    TEXT_REMOVED = "TEXT_REMOVED"
    NUMBER_CHANGED = "NUMBER_CHANGED"
    DATE_CHANGED = "DATE_CHANGED"
    IMAGE_CHANGED = "IMAGE_CHANGED"
    LOGO_CHANGED = "LOGO_CHANGED"
    LAYOUT_CHANGED = "LAYOUT_CHANGED"
    METADATA_CHANGED = "METADATA_CHANGED"
    PAGE_INSERTED = "PAGE_INSERTED"
    PAGE_REMOVED = "PAGE_REMOVED"
    SIGNATURE_CHANGED = "SIGNATURE_CHANGED"
    UNKNOWN = "UNKNOWN"


class DifferenceSeverity(StrEnum):
    """Severity for comparison differences."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class RegionBox:
    """Localized region for a comparison difference."""

    x: float
    y: float
    width: float
    height: float
    page_number: int | None = None
    frame_number: int | None = None
    polygon: tuple[tuple[float, float], ...] | None = None
    normalized: RegionBox | None = None


@dataclass(frozen=True, slots=True)
class DifferenceItem:
    """One deterministic comparison difference."""

    matcher: str
    difference_type: DifferenceType
    severity: DifferenceSeverity
    confidence: float
    description: str
    explanation: str
    original_value: str | None = None
    submitted_value: str | None = None
    regions: tuple[RegionBox, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ComparisonContext:
    """Inputs supplied to every comparison matcher."""

    case_id: UUID
    questioned_evidence_id: UUID
    reference_evidence_id: UUID
    questioned_filename: str
    reference_filename: str
    questioned_mime_type: str
    reference_mime_type: str
    questioned_storage_key: str
    reference_storage_key: str
    questioned_sha256: str
    reference_sha256: str
    questioned_classification: EvidenceClassification
    reference_classification: EvidenceClassification
    storage: Any
    settings: Any
    questioned_extractions: tuple[dict[str, Any], ...] = ()
    reference_extractions: tuple[dict[str, Any], ...] = ()
    questioned_metadata: dict[str, Any] = field(default_factory=dict)
    reference_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MatcherResult:
    """Output from one comparison matcher plugin."""

    matcher: str
    version: str
    differences: tuple[DifferenceItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    """Aggregated output from all compatible matchers."""

    status: ComparisonRunStatus
    differences: tuple[DifferenceItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message_safe: str | None = None
