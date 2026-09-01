"""Audio AI detector plugin contract."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.ai.audio.models import (
    AudioAnalysisContext,
    AudioDetectorMetadata,
    AudioDetectorOutput,
)


class AudioAIDetector(ABC):
    """Replaceable audio forensic AI detector."""

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
    async def predict(self, context: AudioAnalysisContext) -> AudioDetectorOutput:
        """Run inference and return normalized detector output."""

    @abstractmethod
    def metadata(self) -> AudioDetectorMetadata:
        """Return immutable detector metadata."""

    @abstractmethod
    def supports(self, context: AudioAnalysisContext) -> bool:
        """Return whether this detector supports the given context."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return runtime health information."""

    def can_analyze(self, context: AudioAnalysisContext) -> bool:
        """Compatibility alias for supports()."""

        return self.supports(context)

    @property
    def is_loaded(self) -> bool:
        return False
