"""Local noise variance detector."""

import asyncio

import numpy as np

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    Severity,
)
from backend.app.forensics.utils import (
    encode_png,
    grid_regions,
    load_image_from_storage,
)


class NoiseDetector:
    """Estimate local noise and flag abrupt variance changes."""

    name = "noise"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        return context.classification == EvidenceClassification.IMAGE

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        rgb, width, height = await load_image_from_storage(
            context.storage,
            context.storage_key,
            max_bytes=max_bytes,
        )
        noise_map, score = await asyncio.to_thread(_local_noise, rgb)
        regions = grid_regions(
            noise_map,
            threshold=0.65,
            source_width=width,
            source_height=height,
        )
        findings: tuple[FindingItem, ...] = ()
        if score >= 0.25:
            findings = (
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.NOISE,
                    severity=_severity(score),
                    confidence=min(0.92, score + 0.25),
                    description="Abrupt local noise variance detected.",
                    explanation=(
                        "Sliding-window noise estimates differ significantly "
                        "across adjacent regions of the image."
                    ),
                    regions=regions,
                    metadata={"noise_score": round(score, 4)},
                ),
            )
        heatmap = (noise_map * 255).astype(np.uint8)
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.FORENSIC_HEATMAP,
                mime_type="image/png",
                content=encode_png(heatmap),
                metadata={"detector": self.name, "kind": "noise"},
            ),
        )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=findings,
            artifacts=artifacts,
            metadata={"noise_score": round(score, 4)},
        )


def _local_noise(rgb: np.ndarray) -> tuple[np.ndarray, float]:
    gray = np.mean(rgb.astype(np.float32), axis=2)
    kernel = 5
    pad = kernel // 2
    padded = np.pad(gray, pad, mode="reflect")
    h, w = gray.shape
    noise = np.zeros((h, w), dtype=np.float32)
    for y in range(h):
        for x in range(w):
            window = padded[y : y + kernel, x : x + kernel]
            noise[y, x] = float(np.std(window))
    normalized = noise / max(float(np.max(noise)), 1.0)
    downsampled = normalized[:: max(1, h // 64), :: max(1, w // 64)]
    return downsampled, float(np.std(normalized))


def _severity(score: float) -> Severity:
    if score >= 0.7:
        return Severity.HIGH
    if score >= 0.5:
        return Severity.MEDIUM
    if score >= 0.35:
        return Severity.LOW
    return Severity.INFO
