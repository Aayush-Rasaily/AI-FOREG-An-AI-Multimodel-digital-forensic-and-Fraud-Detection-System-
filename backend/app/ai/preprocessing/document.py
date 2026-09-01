"""Document preprocessing interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class DocumentPage:
    """One rendered document page."""

    page_number: int
    width: float
    height: float
    content_type: str


@dataclass(frozen=True, slots=True)
class DocumentRegion:
    """One extracted document region."""

    page_number: int
    x: float
    y: float
    width: float
    height: float
    text: str | None = None


class PageRenderer(Protocol):
    """Interface for future document page rendering."""

    def render_pages(self, document_bytes: bytes) -> tuple[DocumentPage, ...]:
        """Render document pages without forensic interpretation."""
        ...


class RegionExtractor(Protocol):
    """Interface for future document region extraction."""

    def extract_regions(
        self,
        pages: tuple[DocumentPage, ...],
    ) -> tuple[DocumentRegion, ...]:
        """Extract layout regions without forensic interpretation."""
        ...


def preprocess_document(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize document preprocessing input for the inference engine."""

    return {
        "mime_type": payload.get("mime_type", "application/octet-stream"),
        "page_count": int(payload.get("page_count", 1)),
        "regions": payload.get("regions", []),
    }
