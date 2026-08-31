"""Phase 5A multimodal evidence extraction foundation."""

from backend.app.extraction.base import EvidenceExtractor, OCRProvider
from backend.app.extraction.models import BoundingBox, ExtractionType

__all__ = ["BoundingBox", "EvidenceExtractor", "ExtractionType", "OCRProvider"]
