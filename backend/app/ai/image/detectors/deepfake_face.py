"""Deepfake and synthetic face detector plugin."""

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
from backend.app.ai.image.preprocessing.faces import HeuristicFaceDetector
from backend.app.ai.image.utils import encode_grayscale_png, patch_variance_map
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import RegionBox, Severity
from backend.app.forensics.utils import region_from_pixels


class DeepfakeFaceDetector(ImageAIDetector):
    """Detect face swaps, identity replacement, and synthetic faces."""

    name = "deepfake_face"
    model_name = "deepfake_face_heuristic"
    model_version = "1.0.0"
    framework = "NATIVE"

    def __init__(self) -> None:
        self._loaded = False
        self._device = "cpu"
        self._face_detector = HeuristicFaceDetector()

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
            description="Detects face swaps and synthetic facial regions.",
            supported_tasks=("deepfake_detection", "face_swap_detection"),
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
        faces = self._face_detector.detect_faces(rgb, width=width, height=height)
        score, mask, regions = await asyncio.to_thread(
            _analyze_faces,
            rgb,
            width,
            height,
            faces,
        )
        findings: tuple[ImageAIFindingItem, ...] = ()
        if score >= 0.35 and regions:
            findings = (
                ImageAIFindingItem(
                    detector=self.name,
                    category=ImageFindingCategory.DEEPFAKE,
                    severity=_severity(score),
                    confidence=min(0.94, score),
                    description="Facial region inconsistencies detected.",
                    explanation=(
                        "Detected face regions show boundary or texture variance "
                        "patterns associated with swap or synthesis artifacts."
                    ),
                    regions=regions,
                    recommendation=(
                        "Inspect facial boundaries and compare with "
                        "reference portraits."
                    ),
                    metadata={
                        "face_count": len(faces),
                        "face_score": round(score, 4),
                    },
                    model_name=self.model_name,
                    model_version=self.model_version,
                    model_framework=self.framework,
                ),
            )
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_MASK,
                mime_type="image/png",
                content=encode_grayscale_png(mask),
                metadata={"detector": self.name, "face_count": len(faces)},
            ),
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return ImageDetectorOutput(
            detector=self.name,
            version="1.0",
            findings=findings,
            artifacts=artifacts,
            metadata={"face_score": round(score, 4), "device": self._device},
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
        )


def _analyze_faces(
    rgb: np.ndarray,
    width: int,
    height: int,
    faces: tuple[tuple[float, float, float, float], ...],
) -> tuple[float, np.ndarray, tuple[RegionBox, ...]]:
    variance = patch_variance_map(rgb, patch_size=12)
    mask = np.zeros((height, width), dtype=np.float32)
    regions: list[RegionBox] = []
    scores: list[float] = []
    for x, y, box_w, box_h in faces:
        x0, y0 = int(x), int(y)
        x1, y1 = int(min(width, x + box_w)), int(min(height, y + box_h))
        region = variance[y0:y1, x0:x1]
        if region.size == 0:
            continue
        edge_score = float(region[: max(1, region.shape[0] // 8), :].mean())
        inner_score = float(region.mean())
        score = min(0.99, max(0.0, abs(edge_score - inner_score) * 2.5))
        scores.append(score)
        mask[y0:y1, x0:x1] = np.maximum(mask[y0:y1, x0:x1], score)
        regions.append(
            region_from_pixels(x, y, box_w, box_h, width, height),
        )
    overall = max(scores) if scores else 0.0
    return overall, mask, tuple(regions)


def _severity(score: float) -> Severity:
    if score >= 0.7:
        return Severity.HIGH
    if score >= 0.5:
        return Severity.MEDIUM
    return Severity.LOW
