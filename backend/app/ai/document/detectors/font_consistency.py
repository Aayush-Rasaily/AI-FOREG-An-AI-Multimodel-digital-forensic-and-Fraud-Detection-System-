"""Font consistency detector for document AI analysis."""

from __future__ import annotations

import asyncio
import io
import time
from typing import Any

from pypdf import PdfReader

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


class FontConsistencyDetector(DocumentAIDetector):
    """Detect font family and size inconsistencies in PDF documents."""

    name = "font_consistency"
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
            description=(
                "Checks PDF font family and size spread using classical parsing."
            ),
            supported_tasks=("font_consistency",),
            model_name="font_consistency_classical",
            model_version=self.version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: DocumentAnalysisContext) -> bool:
        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return (
            context.classification == EvidenceClassification.DOCUMENT
            and extension == "pdf"
        )

    def health(self) -> dict[str, Any]:
        return {"loaded": self._loaded, "method": DetectionMethod.CLASSICAL.value}

    async def predict(self, context: DocumentAnalysisContext) -> DocumentDetectorOutput:
        started = time.perf_counter()
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        async with context.storage.open(context.storage_key) as stream:
            data = await asyncio.to_thread(stream.read, max_bytes + 1)
        findings = await asyncio.to_thread(self._analyze_bytes, data)
        latency_ms = (time.perf_counter() - started) * 1000.0
        return DocumentDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=findings,
            latency_ms=latency_ms,
            model_name="font_consistency_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze_bytes(self, data: bytes) -> tuple[DocumentAIFindingItem, ...]:
        if not data:
            return ()
        reader = PdfReader(io.BytesIO(data))
        families: set[str] = set()
        sizes: list[float] = []
        for page in reader.pages:
            resources = page.get("/Resources")
            if not resources:
                continue
            fonts = resources.get("/Font")
            if not isinstance(fonts, dict):
                continue
            for font_ref in fonts.values():
                font_obj = font_ref.get_object()
                base_font = str(font_obj.get("/BaseFont", ""))
                if base_font:
                    families.add(base_font)
                size = font_obj.get("/Size")
                if isinstance(size, (int, float)):
                    sizes.append(float(size))
        if len(families) <= 1 and (not sizes or max(sizes) - min(sizes) < 4):
            return ()
        spread = max(sizes) - min(sizes) if sizes else 0.0
        confidence = min(0.9, 0.4 + len(families) * 0.05 + spread * 0.02)
        return (
            DocumentAIFindingItem(
                detector=self.name,
                category=DocumentFindingCategory.FONT_INCONSISTENCY,
                severity=Severity.MEDIUM if len(families) > 2 else Severity.LOW,
                description="Multiple font families or sizes detected in the document.",
                explanation=(
                    f"Found {len(families)} font families and size spread "
                    f"{spread:.1f}. Mixed fonts may indicate pasted or edited content."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=round(confidence, 4),
                recommendation=(
                    "Compare font usage against a trusted reference; font differences "
                    "alone are not proof of fraud."
                ),
                metadata={
                    "font_families": sorted(families),
                    "size_spread": round(spread, 2),
                },
                model_name="font_consistency_classical",
                model_version=self.version,
                model_framework="NATIVE",
            ),
        )
