"""Waveform discontinuity detector."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import numpy as np

from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.detectors._windows import temporal_from_ms, window_metrics
from backend.app.ai.audio.detectors.base import AudioAIDetector
from backend.app.ai.audio.localization.timeline import attach_temporal
from backend.app.ai.audio.models import (
    AudioAIFindingItem,
    AudioAnalysisContext,
    AudioDetectorMetadata,
    AudioDetectorOutput,
    AudioFindingCategory,
    DetectionMethod,
)
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class WaveformDetector(AudioAIDetector):
    name = "waveform"
    version = "1.0.0"

    def __init__(self, settings: AudioAISettings | None = None) -> None:
        self._settings = settings or AudioAISettings()
        self._loaded = False

    def load(self, *, device: str) -> None:
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> AudioDetectorMetadata:
        return AudioDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description="Detects amplitude discontinuities and abrupt transitions.",
            supported_tasks=("waveform_analysis",),
            model_name="waveform_classical",
            model_version=self.version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: AudioAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.AUDIO

    def health(self) -> dict[str, Any]:
        return {"loaded": self._loaded, "method": DetectionMethod.CLASSICAL.value}

    async def predict(self, context: AudioAnalysisContext) -> AudioDetectorOutput:
        started = time.perf_counter()
        findings = await asyncio.to_thread(self._analyze, context)
        return AudioDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=findings,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            model_name="waveform_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: AudioAnalysisContext,
    ) -> tuple[AudioAIFindingItem, ...]:
        if context.samples is None or context.sample_rate is None:
            return ()
        samples = context.samples
        diffs = np.abs(np.diff(samples.astype(np.float64)))
        if diffs.size == 0:
            return ()
        threshold = float(np.percentile(diffs, 99.5))
        if threshold <= 0:
            return ()
        indices = np.where(diffs >= threshold)[0]
        if indices.size == 0:
            return ()
        findings: list[AudioAIFindingItem] = []
        for index in indices[:5]:
            start_ms = int(index / context.sample_rate * 1000)
            end_ms = int((index + 1) / context.sample_rate * 1000)
            temporal = temporal_from_ms(start_ms, end_ms, "WAVEFORM_DISCONTINUITY")
            finding = AudioAIFindingItem(
                detector=self.name,
                category=AudioFindingCategory.WAVEFORM,
                severity=Severity.LOW,
                description="Amplitude discontinuity observed.",
                explanation=(
                    "A localized amplitude transition exceeds the surrounding "
                    "distribution. This may indicate an edit boundary or clipping."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=min(0.75, float(diffs[index] / threshold) * 0.5),
                temporal=temporal,
                metadata={"delta": float(diffs[index]), "threshold": threshold},
                model_name="waveform_classical",
                model_version=self.version,
                model_framework="NATIVE",
                limitations="Discontinuities alone do not prove manipulation.",
            )
            findings.append(attach_temporal(finding, temporal))
        _ = window_metrics(
            samples,
            sample_rate=context.sample_rate,
            window_seconds=self._settings.window_seconds,
            hop_seconds=self._settings.hop_seconds,
        )
        return tuple(findings)
