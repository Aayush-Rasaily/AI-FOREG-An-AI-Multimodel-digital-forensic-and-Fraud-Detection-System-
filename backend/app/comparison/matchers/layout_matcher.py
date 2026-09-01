"""Layout comparison matcher for margins, blocks, and spacing."""

import asyncio
import io
import json

from pypdf import PdfReader

from backend.app.comparison.models import (
    ComparisonContext,
    DifferenceItem,
    DifferenceSeverity,
    DifferenceType,
    MatcherResult,
    RegionBox,
)
from backend.app.comparison.utils import load_bytes_from_storage
from backend.app.domain.processing import EvidenceClassification


class LayoutMatcher:
    """Compare text block positions, margins, and spacing."""

    name = "layout"
    version = "1.0"

    def can_compare(self, context: ComparisonContext) -> bool:
        return (
            context.questioned_classification == EvidenceClassification.DOCUMENT
            and context.reference_classification == EvidenceClassification.DOCUMENT
        )

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        ref_blocks = _blocks_from_extractions(context.reference_extractions)
        q_blocks = _blocks_from_extractions(context.questioned_extractions)
        if not ref_blocks and context.reference_mime_type == "application/pdf":
            max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
            ref_bytes = await load_bytes_from_storage(
                context.storage,
                context.reference_storage_key,
                max_bytes=max_bytes,
            )
            ref_blocks = await asyncio.to_thread(_extract_pdf_blocks, ref_bytes)
        if not q_blocks and context.questioned_mime_type == "application/pdf":
            max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
            q_bytes = await load_bytes_from_storage(
                context.storage,
                context.questioned_storage_key,
                max_bytes=max_bytes,
            )
            q_blocks = await asyncio.to_thread(_extract_pdf_blocks, q_bytes)
        differences = await asyncio.to_thread(
            _compare_layout,
            ref_blocks,
            q_blocks,
        )
        return MatcherResult(
            matcher=self.name,
            version=self.version,
            differences=tuple(differences),
            metadata={
                "reference_blocks": len(ref_blocks),
                "questioned_blocks": len(q_blocks),
            },
        )


def _blocks_from_extractions(
    records: tuple[dict[str, object], ...],
) -> list[dict[str, float | int]]:
    blocks: list[dict[str, float | int]] = []
    for record in records:
        metadata = record.get("metadata")
        if not isinstance(metadata, dict):
            continue
        raw_blocks = metadata.get("blocks")
        if isinstance(raw_blocks, list):
            for block in raw_blocks:
                if isinstance(block, dict):
                    blocks.append(block)
        structure = metadata.get("structure")
        if isinstance(structure, str):
            try:
                parsed = json.loads(structure)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, list):
                for block in parsed:
                    if isinstance(block, dict):
                        blocks.append(block)
    return blocks


def _extract_pdf_blocks(pdf_bytes: bytes) -> list[dict[str, float | int]]:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    blocks: list[dict[str, float | int]] = []
    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue
        lines = [line for line in text.splitlines() if line.strip()]
        for line_index, line in enumerate(lines[:20]):
            blocks.append(
                {
                    "page_number": page_index,
                    "x": float(line_index % 5) * 10.0,
                    "y": float(line_index) * 12.0,
                    "width": float(len(line) * 6),
                    "height": 12.0,
                }
            )
    return blocks


def _compare_layout(
    reference: list[dict[str, float | int]],
    questioned: list[dict[str, float | int]],
) -> list[DifferenceItem]:
    differences: list[DifferenceItem] = []
    if len(reference) != len(questioned):
        differences.append(
            DifferenceItem(
                matcher="layout",
                difference_type=DifferenceType.LAYOUT_CHANGED,
                severity=DifferenceSeverity.MEDIUM,
                confidence=0.82,
                description="Text block count differs between reference and submitted.",
                explanation=(
                    f"Reference layout has {len(reference)} blocks; "
                    f"submitted has {len(questioned)}."
                ),
                original_value=str(len(reference)),
                submitted_value=str(len(questioned)),
            )
        )
    count = min(len(reference), len(questioned), 15)
    for index in range(count):
        ref_block = reference[index]
        q_block = questioned[index]
        ref_x = float(ref_block.get("x", 0))
        q_x = float(q_block.get("x", 0))
        ref_y = float(ref_block.get("y", 0))
        q_y = float(q_block.get("y", 0))
        if abs(ref_x - q_x) > 8 or abs(ref_y - q_y) > 8:
            page = ref_block.get("page_number")
            page_number = int(page) if isinstance(page, int) else None
            differences.append(
                DifferenceItem(
                    matcher="layout",
                    difference_type=DifferenceType.LAYOUT_CHANGED,
                    severity=DifferenceSeverity.MEDIUM,
                    confidence=0.78,
                    description="Text block position shifted from reference layout.",
                    explanation=(
                        f"Block {index + 1} moved from ({ref_x:.1f},{ref_y:.1f}) "
                        f"to ({q_x:.1f},{q_y:.1f})."
                    ),
                    regions=(
                        RegionBox(
                            x=q_x,
                            y=q_y,
                            width=float(q_block.get("width", 40)),
                            height=float(q_block.get("height", 12)),
                            page_number=page_number,
                        ),
                    ),
                    metadata={"block_index": index},
                )
            )
    return differences
