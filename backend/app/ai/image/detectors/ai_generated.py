"""AI-generated image detector plugin."""

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
from backend.app.ai.image.utils import (
    encode_grayscale_png,
    encode_overlay_png,
    high_frequency_energy_map,
    peak_region,
    regions_from_map,
)
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import Severity


class AIGeneratedImageDetector(ImageAIDetector):
    """Detect diffusion/GAN generated imagery via spectral heuristics."""

    name = "ai_generated"
    model_name = "ai_generated_heuristic"
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
            description="Detects AI-generated imagery using spectral heuristics.",
            supported_tasks=("ai_generated_detection",),
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
        score, energy_map = await asyncio.to_thread(
            _score_generated_likelihood,
            rgb,
        )
        regions = regions_from_map(
            energy_map,
            source_width=width,
            source_height=height,
            threshold=0.62,
        )
        peak = peak_region(energy_map, source_width=width, source_height=height)
        if peak is not None:
            regions = (peak, *regions)
        findings: tuple[ImageAIFindingItem, ...] = ()
        if score >= 0.42:
            findings = (
                ImageAIFindingItem(
                    detector=self.name,
                    category=ImageFindingCategory.AI_GENERATED,
                    severity=_severity(score),
                    confidence=min(0.95, score),
                    description=(
                        "Spectral patterns consistent with synthetic generation."
                    ),
                    explanation=(
                        "High-frequency energy distribution differs from typical "
                        "camera-captured imagery, suggesting generative synthesis."
                    ),
                    regions=regions,
                    recommendation=(
                        "Verify provenance and compare with source capture metadata."
                    ),
                    metadata={"spectral_score": round(score, 4)},
                    model_name=self.model_name,
                    model_version=self.model_version,
                    model_framework=self.framework,
                ),
            )
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_HEATMAP,
                mime_type="image/png",
                content=encode_grayscale_png(energy_map),
                metadata={
                    "detector": self.name,
                    "score": round(score, 4),
                },
            ),
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_OVERLAY,
                mime_type="image/png",
                content=encode_overlay_png(rgb, energy_map),
                metadata={"detector": self.name},
            ),
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return ImageDetectorOutput(
            detector=self.name,
            version="1.0",
            findings=findings,
            artifacts=artifacts,
            metadata={"spectral_score": round(score, 4), "device": self._device},
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
        )


def _score_generated_likelihood(array: np.ndarray) -> tuple[float, np.ndarray]:
    if array.max() <= 1.0:
        rgb = (array * 255.0).astype(np.uint8)
    else:
        rgb = array.astype(np.uint8)
    energy = high_frequency_energy_map(rgb)
    smoothness = 1.0 - float(energy.std())
    hf_mean = float(energy.mean())
    score = min(0.99, max(0.0, (hf_mean * 0.65) + (smoothness * 0.35)))
    return score, energy


def _severity(score: float) -> Severity:
    if score >= 0.75:
        return Severity.HIGH
    if score >= 0.55:
        return Severity.MEDIUM
    if score >= 0.42:
        return Severity.LOW
    return Severity.INFO
