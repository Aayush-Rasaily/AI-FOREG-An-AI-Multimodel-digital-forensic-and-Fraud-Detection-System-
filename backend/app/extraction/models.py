"""Framework-independent extraction and localization contracts."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID

from backend.app.application.processors.base import DerivedArtifactPayload


class ExtractionType(StrEnum):
    """Controlled structured evidence types."""

    TEXT = "TEXT"
    WORD = "WORD"
    LINE = "LINE"
    IMAGE_REGION = "IMAGE_REGION"
    FACE_REGION = "FACE_REGION"
    SIGNATURE_REGION = "SIGNATURE_REGION"
    LOGO_REGION = "LOGO_REGION"
    STAMP_REGION = "STAMP_REGION"
    NUMBER = "NUMBER"
    DATE = "DATE"
    QR_CODE = "QR_CODE"
    BARCODE = "BARCODE"
    TABLE = "TABLE"
    PAGE = "PAGE"
    FRAME = "FRAME"
    AUDIO_STREAM = "AUDIO_STREAM"
    METADATA = "METADATA"


class ExtractionSourceType(StrEnum):
    """Source classes used in provenance records."""

    ORIGINAL = "ORIGINAL"
    ARTIFACT = "ARTIFACT"


class ExtractionStatus(StrEnum):
    """Extraction run outcomes, including explicit capability gaps."""

    SUCCEEDED = "SUCCEEDED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"
    FAILED = "FAILED"


def normalize_bbox(
    bbox: "BoundingBox",
    width: float,
    height: float,
) -> "BoundingBox":
    """Convert a pixel/unit box to bounded 0..1 coordinates."""

    if width <= 0 or height <= 0:
        raise ValueError("Coordinate dimensions must be positive.")
    normalized = BoundingBox(
        x=bbox.x / width,
        y=bbox.y / height,
        width=bbox.width / width,
        height=bbox.height / height,
    )
    if any(
        value < 0 or value > 1
        for value in (
            normalized.x,
            normalized.y,
            normalized.width,
            normalized.height,
        )
    ):
        raise ValueError("Normalized coordinates must be between 0 and 1.")
    if normalized.x + normalized.width > 1 or normalized.y + normalized.height > 1:
        raise ValueError("Normalized boxes must remain inside the source.")
    return normalized


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """Pixel or document-unit box with a top-left origin."""

    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True, slots=True)
class ExtractionItem:
    """One source-linked, optionally localized extraction result."""

    evidence_id: UUID
    source_type: ExtractionSourceType
    source_identifier: str
    extraction_type: ExtractionType
    method: str
    version: str
    content: str | None = None
    artifact_id: UUID | None = None
    page_number: int | None = None
    frame_number: int | None = None
    timestamp_ms: int | None = None
    confidence: float | None = None
    bbox: BoundingBox | None = None
    normalized_bbox: BoundingBox | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExtractionContext:
    """Dependencies and immutable evidence facts supplied to extractors."""

    evidence_id: UUID
    original_filename: str
    mime_type: str
    storage_key: str
    storage: Any
    settings: Any
    ocr_provider: Any


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Extractor output with explicit capability status."""

    status: ExtractionStatus
    items: tuple[ExtractionItem, ...] = ()
    artifacts: tuple[DerivedArtifactPayload, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    error_code: str | None = None
    error_message_safe: str | None = None
