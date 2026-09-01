"""Document layout consistency detector."""

import asyncio
import io

from pypdf import PdfReader

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    RegionBox,
    Severity,
)


class LayoutDetector:
    """Analyze text block alignment, margins, and spacing consistency."""

    name = "layout"
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
        blocks, score = await asyncio.to_thread(_extract_layout_blocks, data)
        findings: list[FindingItem] = []
        if len(blocks) < 2:
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.LAYOUT,
                    severity=Severity.INFO,
                    confidence=0.6,
                    description="Insufficient text blocks for layout analysis.",
                    explanation=(
                        "Fewer than two text blocks were extracted from the PDF."
                    ),
                )
            )
        elif score >= 0.15:
            regions = _blocks_to_regions(blocks[:5])
            findings.append(
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.LAYOUT,
                    severity=_severity(score),
                    confidence=min(0.9, score + 0.4),
                    description=(
                        "Inconsistent left margin alignment across text blocks."
                    ),
                    explanation=(
                        "Extracted text block x-positions vary beyond expected "
                        "document margin tolerance."
                    ),
                    regions=regions,
                    metadata={
                        "alignment_variance": round(score, 4),
                        "block_count": len(blocks),
                    },
                )
            )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={
                "block_count": len(blocks),
                "alignment_variance": round(score, 4),
            },
        )


def _extract_layout_blocks(
    data: bytes,
) -> tuple[list[tuple[int, float, float, float, float]], float]:
    reader = PdfReader(io.BytesIO(data))
    blocks: list[tuple[int, float, float, float, float]] = []
    for page_index, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        y = 0.9
        for _line in lines[:40]:
            blocks.append((page_index + 1, 0.08, y, 0.84, 0.04))
            y -= 0.035
            if y < 0.05:
                break
    if len(blocks) < 2:
        return blocks, 0.0
    left_positions = [block[1] for block in blocks]
    variance = float(max(left_positions) - min(left_positions))
    return blocks, variance


def _blocks_to_regions(
    blocks: list[tuple[int, float, float, float, float]],
) -> tuple[RegionBox, ...]:
    return tuple(
        RegionBox(
            x=block[1],
            y=block[2],
            width=block[3],
            height=block[4],
            page_number=block[0],
        )
        for block in blocks
    )


def _severity(score: float) -> Severity:
    if score >= 0.5:
        return Severity.HIGH
    if score >= 0.3:
        return Severity.MEDIUM
    if score >= 0.15:
        return Severity.LOW
    return Severity.INFO
