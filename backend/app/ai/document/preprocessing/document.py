"""Document preprocessing helpers."""

from __future__ import annotations

import io
from dataclasses import dataclass

from pypdf import PdfReader


@dataclass(frozen=True, slots=True)
class DocumentPageInfo:
    """Lightweight page metadata for document analysis."""

    page_number: int
    width: float
    height: float
    text_length: int


def extract_document_text(data: bytes, filename: str) -> str:
    """Extract plain text from supported document formats."""

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if extension in {"txt", "csv"}:
        return data.decode("utf-8", errors="replace")
    return ""


def extract_page_info(data: bytes, filename: str) -> tuple[DocumentPageInfo, ...]:
    """Return page dimensions when available."""

    extension = filename.rsplit(".", 1)[-1].lower()
    if extension != "pdf":
        return ()
    reader = PdfReader(io.BytesIO(data))
    pages: list[DocumentPageInfo] = []
    for index, page in enumerate(reader.pages, start=1):
        box = page.mediabox
        text = page.extract_text() or ""
        pages.append(
            DocumentPageInfo(
                page_number=index,
                width=float(box.width),
                height=float(box.height),
                text_length=len(text),
            )
        )
    return tuple(pages)
