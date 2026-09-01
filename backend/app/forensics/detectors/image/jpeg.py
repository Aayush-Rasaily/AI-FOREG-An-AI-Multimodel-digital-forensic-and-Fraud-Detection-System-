"""JPEG quantization inconsistency detector."""

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


class JpegQuantizationDetector:
    """Detect block-level compression inconsistencies in JPEG evidence."""

    name = "jpeg_quantization"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return context.classification == EvidenceClassification.IMAGE and extension in {
            "jpg",
            "jpeg",
        }

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        rgb, width, height = await load_image_from_storage(
            context.storage,
            context.storage_key,
            max_bytes=max_bytes,
        )
        block_map, score = await asyncio.to_thread(_block_variance, rgb)
        regions = grid_regions(
            block_map,
            threshold=0.6,
            source_width=width,
            source_height=height,
            grid=16,
        )
        findings: tuple[FindingItem, ...] = ()
        if score >= 0.3:
            findings = (
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.COMPRESSION,
                    severity=_severity(score),
                    confidence=min(0.95, score + 0.2),
                    description="JPEG block quantization variance observed.",
                    explanation=(
                        "8x8 block residual variance differs across the image, "
                        "which can indicate heterogeneous recompression."
                    ),
                    regions=regions,
                    metadata={"quantization_score": round(score, 4)},
                    recommendation="Compare block artifacts against surrounding areas.",
                ),
            )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=findings,
            metadata={"quantization_score": round(score, 4)},
        )


def _block_variance(rgb: np.ndarray) -> tuple[np.ndarray, float]:
    gray = np.mean(rgb.astype(np.float32), axis=2)
    h, w = gray.shape
    bh, bw = 8, 8
    rows = h // bh
    cols = w // bw
    variances = np.zeros((rows, cols), dtype=np.float32)
    for row in range(rows):
        for col in range(cols):
            block = gray[row * bh : (row + 1) * bh, col * bw : (col + 1) * bw]
            variances[row, col] = float(np.var(block))
    normalized = variances / max(float(np.max(variances)), 1.0)
    score = float(np.std(normalized))
    return normalized, score


def _severity(score: float) -> Severity:
    if score >= 0.75:
        return Severity.HIGH
    if score >= 0.55:
        return Severity.MEDIUM
    if score >= 0.35:
        return Severity.LOW
    return Severity.INFO
