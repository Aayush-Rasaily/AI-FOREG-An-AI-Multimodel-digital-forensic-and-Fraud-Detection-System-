"""Native PDF text and page-structure extraction."""

import asyncio
import json
from typing import Any

from pypdf import PdfReader

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType
from backend.app.extraction.exceptions import ExtractionError
from backend.app.extraction.models import (
    ExtractionContext,
    ExtractionItem,
    ExtractionResult,
    ExtractionSourceType,
    ExtractionStatus,
    ExtractionType,
)
from backend.app.extraction.patterns import structured_value_items


class DocumentExtractor:
    """Extract native PDF text and truthful page metadata."""

    extensions = frozenset({"pdf"})

    def can_extract(self, context: ExtractionContext) -> bool:
        """Support PDF only; image documents use ImageExtractor."""

        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return extension in self.extensions or context.mime_type == "application/pdf"

    async def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Parse a PDF through a read-only storage stream with output bounds."""

        try:
            async with context.storage.open(context.storage_key) as stream:
                pages, text_by_page = await asyncio.to_thread(
                    _extract_pdf,
                    stream,
                    context.settings.extraction_max_pages,
                    context.settings.extraction_max_text_chars,
                )
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(
                "PDF_EXTRACTION_FAILED",
                "The PDF could not be safely extracted.",
            ) from exc

        items: list[ExtractionItem] = []
        page_manifest: list[dict[str, object]] = []
        for page_number, page_data in enumerate(pages, start=1):
            page_manifest.append(page_data)
            items.append(
                ExtractionItem(
                    evidence_id=context.evidence_id,
                    source_type=ExtractionSourceType.ORIGINAL,
                    source_identifier=context.original_filename,
                    extraction_type=ExtractionType.PAGE,
                    page_number=page_number,
                    content=None,
                    method="pdf_page_structure",
                    version="1.0",
                    metadata=page_data,
                )
            )
            text = text_by_page[page_number - 1]
            if text:
                items.append(
                    ExtractionItem(
                        evidence_id=context.evidence_id,
                        source_type=ExtractionSourceType.ORIGINAL,
                        source_identifier=context.original_filename,
                        extraction_type=ExtractionType.TEXT,
                        page_number=page_number,
                        content=text,
                        method="pdf_text",
                        version="1.0",
                        metadata={"coordinates_available": False},
                    )
                )
                items.extend(
                    structured_value_items(
                        text,
                        context,
                        page_number=page_number,
                    )
                )
        if len(items) > context.settings.extraction_max_items:
            raise ExtractionError(
                "EXTRACTION_ITEM_LIMIT_EXCEEDED",
                "The document produced too many extraction records.",
            )

        structure = {
            "page_count": len(pages),
            "pages": page_manifest,
            "method": "pypdf",
            "version": "1.0",
        }
        all_text = "\n".join(text for text in text_by_page if text)
        artifacts = [
            DerivedArtifactPayload(
                artifact_type=ArtifactType.DOCUMENT_STRUCTURE,
                mime_type="application/json",
                content=json.dumps(structure, sort_keys=True).encode("utf-8"),
                metadata={"page_count": len(pages)},
            )
        ]
        if all_text:
            artifacts.append(
                DerivedArtifactPayload(
                    artifact_type=ArtifactType.TEXT_RESULT,
                    mime_type="application/json",
                    content=json.dumps(
                        {
                            "pages": [
                                {"page_number": index + 1, "text": text}
                                for index, text in enumerate(text_by_page)
                                if text
                            ],
                            "method": "pdf_text",
                            "version": "1.0",
                        },
                        sort_keys=True,
                    ).encode("utf-8"),
                    metadata={"page_count": len(pages)},
                )
            )
        return ExtractionResult(
            status=ExtractionStatus.SUCCEEDED,
            items=tuple(items),
            artifacts=tuple(artifacts),
            metadata={
                "page_count": len(pages),
                "text_pages": sum(bool(text) for text in text_by_page),
            },
        )


def _extract_pdf(
    stream: Any,
    max_pages: int,
    max_text_chars: int,
) -> tuple[list[dict[str, object]], list[str]]:
    """Perform synchronous bounded pypdf work in a worker thread."""

    reader = PdfReader(stream, strict=False)
    if len(reader.pages) > max_pages:
        raise ExtractionError(
            "PDF_PAGE_LIMIT_EXCEEDED",
            "The PDF exceeds the configured extraction page limit.",
        )
    pages: list[dict[str, object]] = []
    text_by_page: list[str] = []
    total_chars = 0
    for page in reader.pages:
        box = page.mediabox
        width = _safe_float(box.width)
        height = _safe_float(box.height)
        text = page.extract_text() or ""
        total_chars += len(text)
        if total_chars > max_text_chars:
            raise ExtractionError(
                "PDF_TEXT_LIMIT_EXCEEDED",
                "The PDF exceeds the configured extraction text limit.",
            )
        pages.append(
            {
                "width": width,
                "height": height,
                "unit": "pdf_points",
                "text_available": bool(text),
                "coordinates_available": False,
            }
        )
        text_by_page.append(text)
    return pages, text_by_page


def _safe_float(value: object) -> float | None:
    try:
        return float(str(value)) if value is not None else None
    except (TypeError, ValueError):
        return None
