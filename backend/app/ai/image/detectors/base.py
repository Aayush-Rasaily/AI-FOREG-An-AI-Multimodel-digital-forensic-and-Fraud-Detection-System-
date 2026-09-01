"""Image AI detector plugin contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.ai.image.models import (
    ImageAnalysisContext,
    ImageDetectorMetadata,
    ImageDetectorOutput,
)


class ImageAIDetector(ABC):
    """Replaceable image forensic AI detector."""

    @abstractmethod
    def load(self, *, device: str) -> None:
        """Load detector backend and prepare for inference."""

    @abstractmethod
    def unload(self) -> None:
        """Release detector resources."""

    @abstractmethod
    async def predict(self, context: ImageAnalysisContext) -> ImageDetectorOutput:
        """Run inference and return normalized detector output."""

    @abstractmethod
    def metadata(self) -> ImageDetectorMetadata:
        """Return immutable detector metadata."""

    @abstractmethod
    def supports(self, context: ImageAnalysisContext) -> bool:
        """Return whether this detector supports the given context."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return runtime health information."""

    @property
    def is_loaded(self) -> bool:
        """Return whether the detector backend is loaded."""

        return False
