"""Abstract base class for all AI-FORGE models."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.ai.registry.metadata import ModelMetadata


class AIModel(ABC):
    """Contract every pluggable AI model must implement."""

    @abstractmethod
    def load(self, *, device: str) -> None:
        """Load model weights and prepare for inference."""

    @abstractmethod
    def unload(self) -> None:
        """Release model resources."""

    @abstractmethod
    def warmup(self, *, batch_size: int = 1) -> float:
        """Run a warmup pass and return elapsed seconds."""

    @abstractmethod
    async def predict(
        self,
        inputs: Any,
        *,
        batch_size: int = 1,
    ) -> Any:
        """Execute deterministic inference on preprocessed inputs."""

    @abstractmethod
    def metadata(self) -> ModelMetadata:
        """Return immutable model metadata."""

    @abstractmethod
    def supports(self, task: str) -> bool:
        """Return whether this model supports the given task."""

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return runtime health information."""

    @abstractmethod
    def version(self) -> str:
        """Return the model version string."""

    @property
    def is_loaded(self) -> bool:
        """Return whether the model is currently loaded."""

        return False
