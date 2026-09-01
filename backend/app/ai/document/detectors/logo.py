"""Logo anomaly detector for document AI analysis."""

from __future__ import annotations

import time
from typing import Any

from backend.app.ai.document.detectors._utils import (
    records_by_type,
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
from backend.app.extraction.models import ExtractionType
from backend.app.forensics.models import RegionBox, Severity


class LogoDetector(DocumentAIDetector):
    """Detect logo regions and report AI capability status."""

    name = "logo"
    version = "1.0.0"
    model_name = "logo_detector"
    model_version = "1.0.0"

    def __init__(self) -> None:
        self._loaded = False
        self._ai_model_available = False

    def load(self, *, device: str) -> None:
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
            description="Localizes logo regions and supports future logo AI models.",
            supported_tasks=("logo_localization", "logo_mismatch"),
            model_name=self.model_name,
            model_version=self.model_version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: DocumentAnalysisContext) -> bool:
        return context.classification in {
            EvidenceClassification.DOCUMENT,
            EvidenceClassification.IMAGE,
        }

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "ai_model_available": self._ai_model_available,
        }

    async def predict(self, context: DocumentAnalysisContext) -> DocumentDetectorOutput:
        started = time.perf_counter()
        findings: list[DocumentAIFindingItem] = []
        logo_regions = records_by_type(
            context.extraction_records,
            ExtractionType.LOGO_REGION.value,
        )
        regions: list[RegionBox] = []
        for record in logo_regions:
            bbox = record.get("bbox")
            if isinstance(bbox, dict):
                regions.append(
                    RegionBox(
                        x=float(bbox.get("x", 0)),
                        y=float(bbox.get("y", 0)),
                        width=float(bbox.get("width", 0)),
                        height=float(bbox.get("height", 0)),
                        page_number=record.get("page_number"),
                    )
                )
        if regions:
            findings.append(
                DocumentAIFindingItem(
                    detector=self.name,
                    category=DocumentFindingCategory.LOGO,
                    severity=Severity.INFO,
                    description="Logo regions localized from extraction records.",
                    explanation=(
                        "Logo regions were mapped for downstream validation. "
                        "No authenticity verdict is issued at this stage."
                    ),
                    method=DetectionMethod.CLASSICAL,
                    confidence=None,
                    regions=tuple(regions),
                    metadata={"region_count": len(regions)},
                    model_name="logo_localization_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                )
            )
        if not self._ai_model_available:
            findings.append(
                unavailable_finding(
                    detector=self.name,
                    category=DocumentFindingCategory.LOGO,
                    reason=(
                        "No trained logo replacement AI model is configured. "
                        "Only extraction-based localization is available."
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
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
            method=DetectionMethod.CLASSICAL,
        )
