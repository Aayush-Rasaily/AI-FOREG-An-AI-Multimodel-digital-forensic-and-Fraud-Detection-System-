"""Document metadata consistency detector."""

import asyncio
import io

from pypdf import PdfReader

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    Severity,
)


class DocumentMetadataDetector:
    """Inspect PDF document metadata for producer/creator/date anomalies."""

    name = "document_metadata"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return (
            context.classification == EvidenceClassification.DOCUMENT
            and extension == "pdf"
        )

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        async with context.storage.open(context.storage_key) as stream:
            data = await asyncio.to_thread(stream.read, max_bytes + 1)
        meta = await asyncio.to_thread(_read_pdf_metadata, data)
        findings: list[FindingItem] = []
        if not meta:
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.METADATA,
                    severity=Severity.INFO,
                    confidence=0.75,
                    description="PDF metadata block is empty or unavailable.",
                    explanation=(
                        "No producer, creator, or modification fields were found."
                    ),
                )
            )
        else:
            producer = meta.get("/Producer")
            creator = meta.get("/Creator")
            mod_date = meta.get("/ModDate")
            if producer:
                findings.append(
                    FindingItem(
                        detector=self.name,
                        category=FindingCategory.METADATA,
                        severity=Severity.INFO,
                        confidence=0.85,
                        description="PDF producer metadata present.",
                        explanation=f"Producer field: {producer}",
                        metadata={"producer": producer},
                    )
                )
            if creator and creator != producer:
                findings.append(
                    FindingItem(
                        detector=self.name,
                        category=FindingCategory.METADATA,
                        severity=Severity.LOW,
                        confidence=0.8,
                        description="Creator differs from producer metadata.",
                        explanation=f"Creator: {creator}; Producer: {producer}",
                        metadata={"creator": creator, "producer": producer},
                    )
                )
            if mod_date:
                findings.append(
                    FindingItem(
                        detector=self.name,
                        category=FindingCategory.DATE,
                        severity=Severity.INFO,
                        confidence=0.8,
                        description="Modification timestamp recorded in PDF metadata.",
                        explanation=f"ModDate: {mod_date}",
                        metadata={"mod_date": mod_date},
                    )
                )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={"field_count": len(meta)},
        )


def _read_pdf_metadata(data: bytes) -> dict[str, str]:
    reader = PdfReader(io.BytesIO(data))
    info = reader.metadata
    if info is None:
        return {}
    return {str(key): str(value) for key, value in info.items() if value is not None}
