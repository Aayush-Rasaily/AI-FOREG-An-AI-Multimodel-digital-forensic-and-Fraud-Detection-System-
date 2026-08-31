"""Common extractor and OCR provider interfaces."""

from typing import Protocol

from backend.app.extraction.models import ExtractionContext, ExtractionResult


class EvidenceExtractor(Protocol):
    """Replaceable extractor contract for one broad evidence category."""

    def can_extract(self, context: ExtractionContext) -> bool:
        """Return whether this extractor supports the verified source."""
        ...

    async def extract(self, context: ExtractionContext) -> ExtractionResult:
        """Return source-linked structured evidence."""
        ...


class OCRProvider(Protocol):
    """Provider contract kept outside API routes and extractors."""

    @property
    def enabled(self) -> bool:
        """Return whether OCR was explicitly enabled."""
        ...

    @property
    def available(self) -> bool:
        """Return whether the provider can execute locally."""
        ...

    async def extract_text(self, image: object) -> str:
        """Extract raw text without silently normalizing it."""
        ...

    async def extract_words(self, image: object) -> list[dict[str, object]]:
        """Extract words with confidence and pixel bounding boxes."""
        ...

    async def extract_lines(self, image: object) -> list[dict[str, object]]:
        """Extract lines with confidence and pixel bounding boxes."""
        ...
