"""Document font consistency detector."""

import asyncio
import io
import re

from pypdf import PdfReader

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    Severity,
)


class FontsDetector:
    """Detect mixed font families and size inconsistencies in PDF text."""

    name = "fonts"
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
        font_names, size_spread = await asyncio.to_thread(_collect_fonts, data)
        findings: list[FindingItem] = []
        if len(font_names) > 3:
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.FONT,
                    severity=Severity.MEDIUM,
                    confidence=min(0.9, 0.5 + len(font_names) / 20.0),
                    description="Multiple font families detected in document.",
                    explanation=(
                        f"Fonts referenced: {', '.join(sorted(font_names)[:8])}"
                    ),
                    metadata={
                        "font_count": len(font_names),
                        "fonts": sorted(font_names),
                    },
                )
            )
        if size_spread >= 6.0:
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.FONT,
                    severity=Severity.LOW,
                    confidence=0.75,
                    description="Wide font size spread across pages.",
                    explanation=f"Observed size range span: {size_spread:.1f} pt",
                    metadata={"size_spread": round(size_spread, 2)},
                )
            )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={"font_count": len(font_names)},
        )


def _collect_fonts(data: bytes) -> tuple[set[str], float]:
    reader = PdfReader(io.BytesIO(data))
    fonts: set[str] = set()
    sizes: list[float] = []
    font_pattern = re.compile(r"/([A-Za-z0-9+\-]+)\s+\d+(?:\.\d+)?\s+Tf")
    size_pattern = re.compile(r"/\S+\s+(\d+(?:\.\d+)?)\s+Tf")
    for page in reader.pages:
        content = page.extract_text() or ""
        for match in font_pattern.finditer(content):
            fonts.add(match.group(1))
        for match in size_pattern.finditer(content):
            sizes.append(float(match.group(1)))
    spread = max(sizes) - min(sizes) if sizes else 0.0
    return fonts, spread
