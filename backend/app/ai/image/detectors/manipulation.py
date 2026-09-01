"""Image manipulation detector plugin."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import numpy as np

from backend.app.ai.image.detectors.base import ImageAIDetector
from backend.app.ai.image.models import (
    ImageAIFindingItem,
    ImageAnalysisContext,
    ImageDetectorMetadata,
    ImageDetectorOutput,
    ImageFindingCategory,
)
from backend.app.ai.image.preprocessing.pipeline import preprocess_for_analysis
from backend.app.ai.image.utils import (
    encode_grayscale_png,
    encode_overlay_png,
    patch_variance_map,
    peak_region,
    regions_from_map,
)
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import Severity


class ManipulationDetector(ImageAIDetector):
    """Detect edited regions, retouching, inpainting, and removal."""

    name = "manipulation"
    model_name = "manipulation_heuristic"
    model_version = "1.0.0"
    framework = "NATIVE"

    def __init__(self) -> None:
        self._loaded = False
        self._device = "cpu"

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> ImageDetectorMetadata:
        return ImageDetectorMetadata(
            name=self.name,
            version="1.0",
            author="AI-FORGE Engineering",
            description="Detects localized manipulation and inpainting artifacts.",
            supported_tasks=("manipulation_detection", "inpainting_detection"),
            model_name=self.model_name,
            model_version=self.model_version,
            framework=self.framework,
        )

    def supports(self, context: ImageAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.IMAGE

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "status": "healthy" if self._loaded else "unloaded",
        }

    async def predict(self, context: ImageAnalysisContext) -> ImageDetectorOutput:
        started = time.perf_counter()
        rgb = context.image_array
        width, height = context.width, context.height
        preprocess_for_analysis(rgb, width=width, height=height)
        score, variance_map = await asyncio.to_thread(
            _score_manipulation,
            rgb,
        )
        regions = regions_from_map(
            variance_map,
            source_width=width,
            source_height=height,
            threshold=0.58,
        )
        peak = peak_region(variance_map, source_width=width, source_height=height)
        if peak is not None:
            regions = (peak, *regions)
        findings: tuple[ImageAIFindingItem, ...] = ()
        if score >= 0.38:
            findings = (
                ImageAIFindingItem(
                    detector=self.name,
                    category=ImageFindingCategory.MANIPULATION,
                    severity=_severity(score),
                    confidence=min(0.93, score),
                    description="Localized manipulation variance detected.",
                    explanation=(
                        "Patch-level variance indicates regions that differ "
                        "from surrounding texture continuity."
                    ),
                    regions=regions,
                    recommendation=(
                        "Review highlighted regions for inpainting or retouching."
                    ),
                    metadata={"variance_score": round(score, 4)},
                    model_name=self.model_name,
                    model_version=self.model_version,
                    model_framework=self.framework,
                ),
            )
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_HEATMAP,
                mime_type="image/png",
                content=encode_grayscale_png(variance_map),
                metadata={"detector": self.name},
            ),
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_OVERLAY,
                mime_type="image/png",
                content=encode_overlay_png(rgb, variance_map),
                metadata={"detector": self.name},
            ),
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return ImageDetectorOutput(
            detector=self.name,
            version="1.0",
            findings=findings,
            artifacts=artifacts,
            metadata={"variance_score": round(score, 4), "device": self._device},
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
        )


def _score_manipulation(rgb: np.ndarray) -> tuple[float, np.ndarray]:
    variance = patch_variance_map(rgb, patch_size=16)
    score = min(0.99, float(variance.mean() + variance.std()))
    return score, variance


def _severity(score: float) -> Severity:
    if score >= 0.72:
        return Severity.HIGH
    if score >= 0.52:
        return Severity.MEDIUM
    return Severity.LOW
