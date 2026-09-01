"""PDF page and structure comparison matcher."""

import asyncio
import io

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


class PdfMatcher:
    """Compare PDF page counts and document-level structure."""

    name = "pdf"
    version = "1.0"

    def can_compare(self, context: ComparisonContext) -> bool:
        return (
            context.questioned_classification == EvidenceClassification.DOCUMENT
            and context.reference_classification == EvidenceClassification.DOCUMENT
            and context.questioned_mime_type == "application/pdf"
            and context.reference_mime_type == "application/pdf"
        )

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        ref_bytes = await load_bytes_from_storage(
            context.storage,
            context.reference_storage_key,
            max_bytes=max_bytes,
        )
        q_bytes = await load_bytes_from_storage(
            context.storage,
            context.questioned_storage_key,
            max_bytes=max_bytes,
        )
        differences = await asyncio.to_thread(_compare_pdfs, ref_bytes, q_bytes)
        return MatcherResult(
            matcher=self.name,
            version=self.version,
            differences=tuple(differences),
            metadata={"difference_count": len(differences)},
        )


def _compare_pdfs(reference: bytes, questioned: bytes) -> list[DifferenceItem]:
    ref_reader = PdfReader(io.BytesIO(reference))
    q_reader = PdfReader(io.BytesIO(questioned))
    ref_pages = len(ref_reader.pages)
    q_pages = len(q_reader.pages)
    differences: list[DifferenceItem] = []
    if q_pages > ref_pages:
        differences.append(
            DifferenceItem(
                matcher="pdf",
                difference_type=DifferenceType.PAGE_INSERTED,
                severity=DifferenceSeverity.HIGH,
                confidence=0.95,
                description="Submitted PDF contains extra pages compared to reference.",
                explanation=(
                    f"Reference has {ref_pages} page(s); submitted has {q_pages}."
                ),
                original_value=str(ref_pages),
                submitted_value=str(q_pages),
                metadata={"reference_pages": ref_pages, "submitted_pages": q_pages},
                regions=(RegionBox(x=0, y=0, width=1, height=1, page_number=q_pages),),
            )
        )
    if q_pages < ref_pages:
        differences.append(
            DifferenceItem(
                matcher="pdf",
                difference_type=DifferenceType.PAGE_REMOVED,
                severity=DifferenceSeverity.HIGH,
                confidence=0.95,
                description="Submitted PDF is missing pages present in reference.",
                explanation=(
                    f"Reference has {ref_pages} page(s); submitted has {q_pages}."
                ),
                original_value=str(ref_pages),
                submitted_value=str(q_pages),
                metadata={"reference_pages": ref_pages, "submitted_pages": q_pages},
            )
        )
    ref_meta: dict[str, object] = dict(ref_reader.metadata or {})
    q_meta: dict[str, object] = dict(q_reader.metadata or {})
    for field in ("/Producer", "/Creator", "/ModDate", "/CreationDate"):
        ref_value = str(ref_meta.get(field, ""))
        q_value = str(q_meta.get(field, ""))
        if ref_value != q_value and (ref_value or q_value):
            differences.append(
                DifferenceItem(
                    matcher="pdf",
                    difference_type=DifferenceType.METADATA_CHANGED,
                    severity=DifferenceSeverity.MEDIUM,
                    confidence=0.85,
                    description=f"PDF metadata field '{field}' differs from reference.",
                    explanation=(
                        f"Reference {field}={ref_value!s}; submitted {q_value!s}."
                    ),
                    original_value=ref_value or None,
                    submitted_value=q_value or None,
                    metadata={"field": field},
                )
            )
    return differences
