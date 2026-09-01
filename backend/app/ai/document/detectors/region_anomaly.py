"""Region anomaly detector for document AI analysis."""

from __future__ import annotations

import asyncio
import re
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

DATE_PATTERN = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
NUMBER_PATTERN = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b")


class RegionAnomalyDetector(DocumentAIDetector):
    """Analyze extracted dates, numbers, and regions for inconsistencies."""

    name = "region_anomaly"
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
                "Checks extracted dates, numbers, and signature/logo regions "
                "for formatting inconsistencies."
            ),
            supported_tasks=("date_analysis", "number_analysis", "region_anomaly"),
            model_name="region_anomaly_classical",
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
            model_name="region_anomaly_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: DocumentAnalysisContext,
    ) -> tuple[DocumentAIFindingItem, ...]:
        findings: list[DocumentAIFindingItem] = []
        dates = records_by_type(context.extraction_records, ExtractionType.DATE.value)
        numbers = records_by_type(
            context.extraction_records,
            ExtractionType.NUMBER.value,
        )
        signatures = records_by_type(
            context.extraction_records,
            ExtractionType.SIGNATURE_REGION.value,
        )
        invalid_dates = [
            record
            for record in dates
            if isinstance(record.get("content"), str)
            and not self._valid_date(record["content"])
        ]
        if invalid_dates:
            findings.append(
                DocumentAIFindingItem(
                    detector=self.name,
                    category=DocumentFindingCategory.DATE_INCONSISTENCY,
                    severity=Severity.MEDIUM,
                    description="Suspicious or invalid date values detected.",
                    explanation=(
                        f"{len(invalid_dates)} extracted date value(s) failed "
                        "basic validity checks."
                    ),
                    method=DetectionMethod.CLASSICAL,
                    confidence=0.75,
                    metadata={"invalid_date_count": len(invalid_dates)},
                    model_name="region_anomaly_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                    recommendation=(
                        "Review date fields manually; unusual values are not "
                        "automatically fraudulent."
                    ),
                )
            )
        if numbers:
            formats = {
                self._number_format(str(record.get("content", "")))
                for record in numbers
            }
            formats.discard("")
            if len(formats) > 2:
                findings.append(
                    DocumentAIFindingItem(
                        detector=self.name,
                        category=DocumentFindingCategory.NUMBER_INCONSISTENCY,
                        severity=Severity.LOW,
                        description="Mixed numeric formatting detected.",
                        explanation=(
                            f"Observed {len(formats)} distinct numeric formatting "
                            "patterns across extracted number fields."
                        ),
                        method=DetectionMethod.CLASSICAL,
                        confidence=min(0.8, 0.4 + len(formats) * 0.1),
                        metadata={"format_variants": sorted(formats)},
                        model_name="region_anomaly_classical",
                        model_version=self.version,
                        model_framework="NATIVE",
                    )
                )
        if signatures:
            regions = tuple(
                RegionBox(
                    x=float((record.get("bbox") or {}).get("x", 0)),
                    y=float((record.get("bbox") or {}).get("y", 0)),
                    width=float((record.get("bbox") or {}).get("width", 0)),
                    height=float((record.get("bbox") or {}).get("height", 0)),
                    page_number=record.get("page_number"),
                )
                for record in signatures
                if isinstance(record.get("bbox"), dict)
            )
            if regions:
                findings.append(
                    DocumentAIFindingItem(
                        detector=self.name,
                        category=DocumentFindingCategory.SIGNATURE,
                        severity=Severity.INFO,
                        description="Signature regions localized from extraction.",
                        explanation=(
                            "Signature regions were mapped for downstream "
                            "verification. No authenticity verdict is issued."
                        ),
                        method=DetectionMethod.CLASSICAL,
                        confidence=None,
                        regions=regions,
                        metadata={"signature_region_count": len(regions)},
                        model_name="region_anomaly_classical",
                        model_version=self.version,
                        model_framework="NATIVE",
                    )
                )
        for diff in context.comparison_differences:
            findings.append(
                DocumentAIFindingItem(
                    detector=self.name,
                    category=DocumentFindingCategory.REFERENCE_MISMATCH,
                    severity=Severity.MEDIUM,
                    description=str(
                        diff.get("description", "Reference mismatch detected.")
                    ),
                    explanation=str(diff.get("explanation", "")),
                    method=DetectionMethod.REFERENCE,
                    confidence=(
                        float(diff["confidence"])
                        if isinstance(diff.get("confidence"), (int, float))
                        else None
                    ),
                    metadata={
                        "matcher": diff.get("matcher"),
                        "difference_type": diff.get("difference_type"),
                    },
                    model_name="reference_comparison",
                    model_version="1.0.0",
                    model_framework="NATIVE",
                )
            )
        return tuple(findings)

    @staticmethod
    def _valid_date(value: str) -> bool:
        match = DATE_PATTERN.search(value)
        if not match:
            return False
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
        return 1 <= month <= 12 and 1 <= day <= 31 and 1900 <= year <= 2100

    @staticmethod
    def _number_format(value: str) -> str:
        if "," in value and "." in value:
            return "grouped_decimal"
        if "," in value:
            return "grouped_integer"
        if "." in value:
            return "decimal"
        if NUMBER_PATTERN.fullmatch(value):
            return "plain_integer"
        return ""
