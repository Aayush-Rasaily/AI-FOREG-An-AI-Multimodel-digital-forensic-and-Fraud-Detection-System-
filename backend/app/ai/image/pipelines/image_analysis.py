"""Image analysis pipeline for Phase 6B image forensics."""

from __future__ import annotations

from typing import Any

from backend.app.ai.image.engine import ImageAnalysisEngine
from backend.app.ai.image.models import ImageAnalysisContext, ImageAnalysisResult


class ImageAnalysisPipeline:
    """End-to-end image AI forensic pipeline."""

    name = "image_analysis"

    def __init__(self, engine: ImageAnalysisEngine) -> None:
        self.engine = engine

    def supports(self, request: dict[str, Any]) -> bool:
        return request.get("modality") == "image"

    def preprocess(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload

    async def run(self, request: dict[str, Any]) -> ImageAnalysisResult:
        context = request["context"]
        if not isinstance(context, ImageAnalysisContext):
            raise TypeError("ImageAnalysisPipeline requires ImageAnalysisContext.")
        return await self.engine.analyze(context)
