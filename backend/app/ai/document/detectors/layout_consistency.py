"""Layout consistency detector for document AI analysis."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.app.ai.document.detectors._utils import artifact_json, records_by_type
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
from backend.app.forensics.models import Severity


class LayoutConsistencyDetector(DocumentAIDetector):
    """Detect page layout and alignment inconsistencies."""

    name = "layout_consistency"
    version = "1.0.0"

    def __init__(self) -> None:
        self._loaded = False

    def load(self, *, device: str) -> None:
        self._loaded = True

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
            description="Checks page dimensions and structure consistency.",
            supported_tasks=("layout_consistency", "alignment"),
            model_name="layout_consistency_classical",
            model_version=self.version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: DocumentAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.DOCUMENT

    def health(self) -> dict[str, Any]:
        return {"loaded": self._loaded, "method": DetectionMethod.CLASSICAL.value}

    async def predict(self, context: DocumentAnalysisContext) -> DocumentDetectorOutput:
        started = time.perf_counter()
        findings = await asyncio.to_thread(self._analyze, context)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return DocumentDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=findings,
            latency_ms=latency_ms,
            model_name="layout_consistency_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: DocumentAnalysisContext,
    ) -> tuple[DocumentAIFindingItem, ...]:
        pages = records_by_type(context.extraction_records, ExtractionType.PAGE.value)
        structure = artifact_json(context.extraction_artifacts, "DOCUMENT_STRUCTURE")
        widths: list[float] = []
        heights: list[float] = []
        for page in pages:
            meta = page.get("metadata")
            if isinstance(meta, dict):
                width = meta.get("width")
                height = meta.get("height")
                if isinstance(width, (int, float)) and isinstance(height, (int, float)):
                    widths.append(float(width))
                    heights.append(float(height))
        if isinstance(structure, dict):
            for page_info in structure.get("pages", []):
                if not isinstance(page_info, dict):
                    continue
                width = page_info.get("width")
                height = page_info.get("height")
                if isinstance(width, (int, float)) and isinstance(height, (int, float)):
                    widths.append(float(width))
                    heights.append(float(height))
        if len(widths) < 2:
            return ()
        width_spread = max(widths) - min(widths)
        height_spread = max(heights) - min(heights)
        if width_spread < 1 and height_spread < 1:
            return ()
        confidence = min(0.85, 0.5 + (width_spread + height_spread) / 200.0)
        return (
            DocumentAIFindingItem(
                detector=self.name,
                category=DocumentFindingCategory.LAYOUT_INCONSISTENCY,
                severity=Severity.MEDIUM,
                description="Page dimension inconsistencies detected.",
                explanation=(
                    f"Page width spread {width_spread:.1f} and height spread "
                    f"{height_spread:.1f} suggest non-uniform layout."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=round(confidence, 4),
                recommendation=(
                    "Compare page layout against a trusted reference document."
                ),
                metadata={
                    "width_spread": round(width_spread, 2),
                    "height_spread": round(height_spread, 2),
                    "page_count": len(widths),
                },
                model_name="layout_consistency_classical",
                model_version=self.version,
                model_framework="NATIVE",
            ),
        )
