"""Edge consistency detector."""

import asyncio

import numpy as np

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    Severity,
)
from backend.app.forensics.utils import grid_regions, load_image_from_storage


class EdgeConsistencyDetector:
    """Measure edge density and gradient discontinuities."""

    name = "edge_consistency"
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
        edge_map, score = await asyncio.to_thread(_edge_density, rgb)
        regions = grid_regions(
            edge_map,
            threshold=0.6,
            source_width=width,
            source_height=height,
        )
        findings: tuple[FindingItem, ...] = ()
        if score >= 0.2:
            findings = (
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.EDGE,
                    severity=_severity(score),
                    confidence=min(0.9, score + 0.3),
                    description="Edge density variance across image regions.",
                    explanation=(
                        "Gradient magnitude differs between adjacent blocks, "
                        "which may indicate compositing boundaries."
                    ),
                    regions=regions,
                    metadata={"edge_score": round(score, 4)},
                ),
            )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=findings,
            metadata={"edge_score": round(score, 4)},
        )


def _edge_density(rgb: np.ndarray) -> tuple[np.ndarray, float]:
    gray = np.mean(rgb.astype(np.float32), axis=2)
    gx = np.abs(np.diff(gray, axis=1, prepend=gray[:, :1]))
    gy = np.abs(np.diff(gray, axis=0, prepend=gray[:1, :]))
    magnitude = gx + gy
    block = 16
    h, w = magnitude.shape
    rows = h // block
    cols = w // block
    density = np.zeros((rows, cols), dtype=np.float32)
    for r in range(rows):
        for c in range(cols):
            patch = magnitude[r * block : (r + 1) * block, c * block : (c + 1) * block]
            density[r, c] = float(np.mean(patch))
    normalized = density / max(float(np.max(density)), 1.0)
    return normalized, float(np.std(normalized))


def _severity(score: float) -> Severity:
    if score >= 0.65:
        return Severity.HIGH
    if score >= 0.45:
        return Severity.MEDIUM
    if score >= 0.25:
        return Severity.LOW
    return Severity.INFO
