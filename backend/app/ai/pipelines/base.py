"""Base pipeline contract for future modality-specific pipelines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.app.ai.inference.request import InferenceRequest
from backend.app.ai.inference.response import InferenceResponse


class BasePipeline(ABC):
    """Future pipelines for image, video, audio, document, and signature."""

    name: str

    @abstractmethod
    async def run(self, request: InferenceRequest) -> InferenceResponse:
        """Execute one end-to-end inference pipeline."""

    @abstractmethod
    def supports(self, request: InferenceRequest) -> bool:
        """Return whether this pipeline can handle the request."""

    @abstractmethod
    def preprocess(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply modality-specific preprocessing."""
