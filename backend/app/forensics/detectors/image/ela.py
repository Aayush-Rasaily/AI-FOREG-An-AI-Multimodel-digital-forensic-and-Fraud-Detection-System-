"""Error Level Analysis detector."""

import asyncio
import io

import numpy as np
from PIL import Image

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
    region_from_pixels,
)


class ElaDetector:
    """Detect recompression inconsistencies via Error Level Analysis."""

    name = "ela"
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
        ela_map, score, peak = await asyncio.to_thread(
            _compute_ela,
            rgb,
            width,
            height,
        )
        regions = grid_regions(
            ela_map, threshold=0.55, source_width=width, source_height=height
        )
        if peak is not None:
            px, py, pw, ph = peak
            regions = (
                region_from_pixels(px, py, pw, ph, width, height),
                *regions,
            )
        severity = _severity(score)
        findings: tuple[FindingItem, ...] = ()
        if score >= 0.35:
            findings = (
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.COMPRESSION,
                    severity=severity,
                    confidence=min(0.99, score),
                    description="Localized recompression variance detected.",
                    explanation=(
                        "The Error Level Analysis map shows regions whose "
                        "recompression residuals differ from surrounding pixels."
                    ),
                    regions=regions,
                    metadata={"ela_score": round(score, 4)},
                    recommendation="Manual review of highlighted regions recommended.",
                ),
            )
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.ELA_RESULT,
                mime_type="image/png",
                content=encode_png(ela_map),
                metadata={"detector": self.name, "width": width, "height": height},
            ),
        )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=findings,
            artifacts=artifacts,
            metadata={"ela_score": round(score, 4)},
        )


def _compute_ela(
    rgb: np.ndarray,
    width: int,
    height: int,
) -> tuple[np.ndarray, float, tuple[float, float, float, float] | None]:
    image = Image.fromarray(rgb, mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    resaved = np.asarray(Image.open(buffer).convert("RGB"), dtype=np.int16)
    original = rgb.astype(np.int16)
    diff = np.abs(original - resaved)
    ela = np.mean(diff, axis=2)
    normalized = ela / max(float(np.max(ela)), 1.0)
    score = float(np.std(normalized))
    peak = None
    if score >= 0.35:
        threshold = float(np.mean(normalized) + np.std(normalized))
        mask = normalized >= threshold
        if np.any(mask):
            ys, xs = np.where(mask)
            x0, x1 = int(xs.min()), int(xs.max())
            y0, y1 = int(ys.min()), int(ys.max())
            peak = (
                float(x0),
                float(y0),
                float(x1 - x0 + 1),
                float(y1 - y0 + 1),
            )
    heatmap = (normalized * 255).astype(np.uint8)
    return heatmap, score, peak


def _severity(score: float) -> Severity:
    if score >= 0.9:
        return Severity.CRITICAL
    if score >= 0.75:
        return Severity.HIGH
    if score >= 0.55:
        return Severity.MEDIUM
    if score >= 0.35:
        return Severity.LOW
    return Severity.INFO
