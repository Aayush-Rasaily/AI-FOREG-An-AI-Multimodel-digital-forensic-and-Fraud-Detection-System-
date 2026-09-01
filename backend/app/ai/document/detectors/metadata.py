"""Document metadata anomaly detector."""

from __future__ import annotations

import asyncio
import io
import time
from datetime import UTC, datetime
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


class MetadataDetector(DocumentAIDetector):
    """Analyze document metadata for suspicious editing traces."""

    name = "metadata"
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
            description="Checks PDF producer/creator metadata for editing traces.",
            supported_tasks=("metadata", "provenance"),
            model_name="metadata_classical",
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
            model_name="metadata_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze_bytes(self, data: bytes) -> tuple[DocumentAIFindingItem, ...]:
        if not data:
            return ()
        reader = PdfReader(io.BytesIO(data))
        meta: dict[str, Any] = dict(reader.metadata or {})
        producer = str(meta.get("/Producer", "") or "")
        creator = str(meta.get("/Creator", "") or "")
        mod_date = meta.get("/ModDate")
        findings: list[DocumentAIFindingItem] = []
        suspicious_tools = ("photoshop", "gimp", "canva", "pdfeditor", "foxit")
        combined = f"{producer} {creator}".lower()
        if any(tool in combined for tool in suspicious_tools):
            findings.append(
                DocumentAIFindingItem(
                    detector=self.name,
                    category=DocumentFindingCategory.METADATA,
                    severity=Severity.MEDIUM,
                    description="Editing software metadata detected in the PDF.",
                    explanation=f"Producer='{producer}' Creator='{creator}'.",
                    method=DetectionMethod.CLASSICAL,
                    confidence=0.7,
                    metadata={"producer": producer, "creator": creator},
                    model_name="metadata_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                    recommendation="Verify provenance against source system records.",
                )
            )
        if mod_date:
            findings.append(
                DocumentAIFindingItem(
                    detector=self.name,
                    category=DocumentFindingCategory.METADATA,
                    severity=Severity.INFO,
                    description="PDF modification date metadata present.",
                    explanation=f"ModDate={mod_date}.",
                    method=DetectionMethod.CLASSICAL,
                    confidence=None,
                    metadata={
                        "mod_date": str(mod_date),
                        "checked_at": datetime.now(UTC).isoformat(),
                    },
                    model_name="metadata_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                )
            )
        return tuple(findings)
