"""Video AI detector plugin contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.ai.video.models.base import (
    VideoDetectorMetadata,
    VideoDetectorOutput,
)
from backend.app.ai.video.models.context import VideoAnalysisContext


class VideoAIDetector(ABC):
    """Replaceable video forensic AI detector."""

    @abstractmethod
    def load(self, *, device: str) -> None:
        """Load detector backend and prepare for inference."""

    @abstractmethod
    def unload(self) -> None:
        """Release detector resources."""

    def warmup(self) -> None:
        """Optional warmup hook for cached models."""

        return

    @abstractmethod
    async def predict(self, context: VideoAnalysisContext) -> VideoDetectorOutput:
        """Run inference and return normalized detector output."""

    @abstractmethod
    def metadata(self) -> VideoDetectorMetadata:
        """Return immutable detector metadata."""

    @abstractmethod
    def supports(self, context: VideoAnalysisContext) -> bool:
        """Return whether this detector supports the given context."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return runtime health information."""

    @property
    def is_loaded(self) -> bool:
        """Return whether the detector backend is loaded."""

        return False
