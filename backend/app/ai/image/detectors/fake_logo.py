"""Fake logo detector plugin."""

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
from backend.app.ai.image.utils import encode_grayscale_png
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import RegionBox, Severity
from backend.app.forensics.utils import region_from_pixels


class FakeLogoDetector(ImageAIDetector):
    """Detect logo replacement, missing logos, and fake logos."""

    name = "fake_logo"
    model_name = "fake_logo_heuristic"
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
            description="Detects logo placement anomalies and replacement artifacts.",
            supported_tasks=("logo_detection", "logo_validation"),
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
        score, regions, activation = await asyncio.to_thread(
            _analyze_logo_regions,
            rgb,
            width,
            height,
        )
        findings: tuple[ImageAIFindingItem, ...] = ()
        if score >= 0.33:
            findings = (
                ImageAIFindingItem(
                    detector=self.name,
                    category=ImageFindingCategory.LOGO,
                    severity=_severity(score),
                    confidence=min(0.9, score),
                    description="Logo region anomaly detected.",
                    explanation=(
                        "Corner and header logo zones show edge or contrast "
                        "patterns inconsistent with surrounding branding areas."
                    ),
                    regions=regions,
                    recommendation=(
                        "Compare logo geometry and palette with trusted references."
                    ),
                    metadata={"logo_score": round(score, 4)},
                    model_name=self.model_name,
                    model_version=self.model_version,
                    model_framework=self.framework,
                ),
            )
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_HEATMAP,
                mime_type="image/png",
                content=encode_grayscale_png(activation),
                metadata={"detector": self.name},
            ),
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return ImageDetectorOutput(
            detector=self.name,
            version="1.0",
            findings=findings,
            artifacts=artifacts,
            metadata={"logo_score": round(score, 4), "device": self._device},
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
        )


def _analyze_logo_regions(
    rgb: np.ndarray,
    width: int,
    height: int,
) -> tuple[float, tuple[RegionBox, ...], np.ndarray]:
    gray = rgb.mean(axis=2).astype(np.float32)
    activation = np.zeros((height, width), dtype=np.float32)
    candidate_zones = (
        (0.0, 0.0, width * 0.25, height * 0.2),
        (width * 0.75, 0.0, width * 0.25, height * 0.2),
        (0.0, height * 0.8, width * 0.25, height * 0.2),
    )
    regions: list[RegionBox] = []
    scores: list[float] = []
    for x, y, box_w, box_h in candidate_zones:
        x0, y0 = int(x), int(y)
        x1, y1 = int(min(width, x + box_w)), int(min(height, y + box_h))
        zone = gray[y0:y1, x0:x1]
        if zone.size == 0:
            continue
        edge = np.abs(np.diff(zone, axis=1)).mean() if zone.shape[1] > 1 else 0.0
        zone_mean = float(zone.mean())
        score = min(0.99, float(edge) / max(zone_mean, 1e-6))
        scores.append(score)
        activation[y0:y1, x0:x1] = score
        regions.append(region_from_pixels(x, y, box_w, box_h, width, height))
    overall = max(scores) if scores else 0.0
    return overall, tuple(regions), activation


def _severity(score: float) -> Severity:
    if score >= 0.65:
        return Severity.HIGH
    if score >= 0.45:
        return Severity.MEDIUM
    return Severity.LOW
