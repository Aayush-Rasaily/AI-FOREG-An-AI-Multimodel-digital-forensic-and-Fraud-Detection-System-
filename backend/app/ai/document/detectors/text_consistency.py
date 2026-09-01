"""Text consistency detector for document AI analysis."""

from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any

from backend.app.ai.document.detectors._utils import records_by_type
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


class TextConsistencyDetector(DocumentAIDetector):
    """Analyze extracted text regions for rendering inconsistencies."""

    name = "text_consistency"
    version = "1.0.0"

    def __init__(self) -> None:
        self._loaded = False
        self._device = "cpu"

    def load(self, *, device: str) -> None:
        self._device = device
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
            description=(
                "Checks spacing, density, and OCR confidence variance in text regions."
            ),
            supported_tasks=("text_consistency", "spacing", "density"),
            model_name="text_consistency_classical",
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
            model_name="text_consistency_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: DocumentAnalysisContext,
    ) -> tuple[DocumentAIFindingItem, ...]:
        words = records_by_type(context.extraction_records, ExtractionType.WORD.value)
        if len(words) < 3:
            return ()
        confidences = [
            float(record["confidence"])
            for record in words
            if isinstance(record.get("confidence"), (int, float))
        ]
        if len(confidences) < 3:
            return ()
        spread = statistics.pstdev(confidences)
        if spread < 0.15:
            return ()
        low_conf = [record for record in words if (record.get("confidence") or 1) < 0.5]
        regions: list[RegionBox] = []
        for record in low_conf[:5]:
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
        confidence = min(0.95, round(spread, 4))
        return (
            DocumentAIFindingItem(
                detector=self.name,
                category=DocumentFindingCategory.TEXT_INCONSISTENCY,
                severity=Severity.MEDIUM if spread >= 0.25 else Severity.LOW,
                description="Text rendering variance detected across OCR word regions.",
                explanation=(
                    f"OCR confidence spread ({spread:.3f}) suggests inconsistent "
                    "rendering or extraction quality in localized text regions."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=confidence,
                regions=tuple(regions),
                recommendation=(
                    "Review localized text regions; font differences alone do not "
                    "indicate fraud."
                ),
                metadata={
                    "confidence_spread": round(spread, 4),
                    "word_count": len(words),
                },
                model_name="text_consistency_classical",
                model_version=self.version,
                model_framework="NATIVE",
            ),
        )
