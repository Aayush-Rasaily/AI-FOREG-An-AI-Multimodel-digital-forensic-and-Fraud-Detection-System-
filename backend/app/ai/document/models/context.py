"""Analysis context for document AI detectors."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from backend.app.domain.processing import EvidenceClassification


@dataclass(frozen=True, slots=True)
class DocumentAnalysisContext:
    """Inputs supplied to document AI detectors."""

    evidence_id: UUID
    case_id: UUID
    original_filename: str
    mime_type: str
    storage_key: str
    classification: EvidenceClassification
    source_sha256: str
    storage: Any
    settings: Any
    device: str = "cpu"
    extraction_records: tuple[dict[str, Any], ...] = ()
    extraction_artifacts: tuple[dict[str, Any], ...] = ()
    forensic_artifacts: tuple[dict[str, Any], ...] = ()
    comparison_differences: tuple[dict[str, Any], ...] = ()
    document_text: str = ""
    metadata_json: dict[str, Any] = field(default_factory=dict)
