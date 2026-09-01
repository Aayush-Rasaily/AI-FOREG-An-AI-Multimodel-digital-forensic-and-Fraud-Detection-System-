"""Resampling frequency indicator detector."""

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
from backend.app.forensics.utils import load_image_from_storage


class ResamplingDetector:
    """Use frequency-domain peaks to indicate resampling artifacts."""

    name = "resampling"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        return context.classification == EvidenceClassification.IMAGE

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        rgb, _width, _height = await load_image_from_storage(
            context.storage,
            context.storage_key,
            max_bytes=max_bytes,
        )
        score, peak_ratio = await asyncio.to_thread(_frequency_score, rgb)
        findings: tuple[FindingItem, ...] = ()
        if score >= 0.35:
            findings = (
                FindingItem(
                    detector=self.name,
                    category=FindingCategory.SPLICING,
                    severity=_severity(score),
                    confidence=min(0.88, score + 0.2),
                    description="Periodic frequency peaks suggest resampling.",
                    explanation=(
                        "The 2D FFT spectrum shows elevated energy at "
                        f"periodic intervals (peak ratio {peak_ratio:.3f})."
                    ),
                    metadata={
                        "resampling_score": round(score, 4),
                        "peak_ratio": round(peak_ratio, 4),
                    },
                ),
            )
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=findings,
            metadata={"resampling_score": round(score, 4)},
        )


def _frequency_score(rgb: np.ndarray) -> tuple[float, float]:
    gray = np.mean(rgb.astype(np.float32), axis=2)
    resized = gray[:: max(1, gray.shape[0] // 256), :: max(1, gray.shape[1] // 256)]
    spectrum = np.abs(np.fft.fftshift(np.fft.fft2(resized)))
    spectrum = spectrum / max(float(np.max(spectrum)), 1.0)
    h, w = spectrum.shape
    center_y, center_x = h // 2, w // 2
    ring = spectrum.copy()
    ring[center_y - 2 : center_y + 3, center_x - 2 : center_x + 3] = 0
    peak = float(np.max(ring))
    mean = float(np.mean(ring))
    ratio = peak / max(mean, 1e-6)
    score = min(1.0, ratio / 8.0)
    return score, ratio


def _severity(score: float) -> Severity:
    if score >= 0.75:
        return Severity.HIGH
    if score >= 0.55:
        return Severity.MEDIUM
    if score >= 0.35:
        return Severity.LOW
    return Severity.INFO
