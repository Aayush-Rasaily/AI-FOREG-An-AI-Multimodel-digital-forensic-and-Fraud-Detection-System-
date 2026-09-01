"""Document tampering detector plugin."""

from __future__ import annotations

import time
from typing import Any

from backend.app.ai.document.detectors._utils import (
    artifact_json,
    unavailable_finding,
)
from backend.app.ai.document.detectors.base import DocumentAIDetector
from backend.app.ai.document.models.base import (
    DetectionMethod,
    DocumentAIFindingItem,
    DocumentAnalysisContext,
    DocumentDetectorMetadata,
    DocumentDetectorOutput,
    DocumentFindingCategory,
)
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class TamperingDetector(DocumentAIDetector):
    """Extensible tampering detector using classical forensic artifacts."""

    name = "tampering"
    version = "1.0.0"
    model_name = "document_tampering"
    model_version = "1.0.0"

    def __init__(self) -> None:
        self._loaded = False
        self._device = "cpu"
        self._ai_model_available = False

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = True
        self._ai_model_available = False

    def unload(self) -> None:
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> DocumentDetectorMetadata:
        return DocumentDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description=(
                "Detects suspicious regions using classical forensic artifacts "
                "and future AI tampering models."
            ),
            supported_tasks=("tampering", "splicing", "copy_move"),
            model_name=self.model_name,
            model_version=self.model_version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: DocumentAnalysisContext) -> bool:
        if context.classification not in {
            EvidenceClassification.DOCUMENT,
            EvidenceClassification.IMAGE,
        }:
            return False
        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return extension in {"pdf", "png", "jpg", "jpeg", "tif", "tiff"}

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "ai_model_available": self._ai_model_available,
            "method": DetectionMethod.CLASSICAL.value,
        }

    async def predict(self, context: DocumentAnalysisContext) -> DocumentDetectorOutput:
        started = time.perf_counter()
        findings: list[DocumentAIFindingItem] = []
        forensic = context.forensic_artifacts
        overlay_meta = artifact_json(forensic, "FORENSIC_OVERLAY")
        heatmap_meta = artifact_json(forensic, "FORENSIC_HEATMAP")
        if overlay_meta or heatmap_meta:
            findings.append(
                DocumentAIFindingItem(
                    detector=self.name,
                    category=DocumentFindingCategory.TAMPERING,
                    severity=Severity.MEDIUM,
                    description=(
                        "Potential manipulation indicators from classical forensics."
                    ),
                    explanation=(
                        "Existing forensic overlay or heatmap artifacts suggest "
                        "localized inconsistencies worth review."
                    ),
                    method=DetectionMethod.CLASSICAL,
                    confidence=None,
                    metadata={
                        "source": "phase5_forensics",
                        "overlay_present": bool(overlay_meta),
                        "heatmap_present": bool(heatmap_meta),
                    },
                    model_name=self.model_name,
                    model_version=self.model_version,
                    model_framework="NATIVE",
                    recommendation="Review highlighted regions in forensic artifacts.",
                )
            )
        if not self._ai_model_available:
            findings.append(
                unavailable_finding(
                    detector=self.name,
                    category=DocumentFindingCategory.TAMPERING,
                    reason=(
                        "No trained document tampering AI model is configured. "
                        "Classical forensic artifacts were used when available."
                    ),
                    model_name=self.model_name,
                    model_version=self.model_version,
                )
            )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return DocumentDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={"method": DetectionMethod.CLASSICAL.value},
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
            method=DetectionMethod.CLASSICAL,
        )
