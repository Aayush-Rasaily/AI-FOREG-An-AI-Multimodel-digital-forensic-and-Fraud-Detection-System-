"""Background noise consistency detector."""

from __future__ import annotations

import asyncio
import time
from typing import Any

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


class NoiseConsistencyDetector(AudioAIDetector):
    name = "noise_consistency"
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
            description="Compares background/noise characteristics across windows.",
            supported_tasks=("noise_consistency",),
            model_name="noise_classical",
            model_version=self.version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: AudioAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.AUDIO

    def health(self) -> dict[str, Any]:
        return {"loaded": self._loaded}

    async def predict(self, context: AudioAnalysisContext) -> AudioDetectorOutput:
        started = time.perf_counter()
        findings = await asyncio.to_thread(self._analyze, context)
        return AudioDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=findings,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            model_name="noise_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: AudioAnalysisContext,
    ) -> tuple[AudioAIFindingItem, ...]:
        if context.samples is None or context.sample_rate is None:
            return ()
        metrics = window_metrics(
            context.samples,
            sample_rate=context.sample_rate,
            window_seconds=self._settings.window_seconds,
            hop_seconds=self._settings.hop_seconds,
        )
        quiet = [entry for entry in metrics if float(entry["rms"]) < 0.02]
        if len(quiet) < 2:
            return ()
        floors = [float(entry["rms"]) for entry in quiet]
        spread = max(floors) - min(floors)
        if spread < 0.01:
            return ()
        start_ms = int(quiet[0]["start_time_ms"])
        end_ms = int(quiet[-1]["end_time_ms"])
        temporal = temporal_from_ms(start_ms, end_ms, "NOISE_FLOOR_CHANGE")
        finding = attach_temporal(
            AudioAIFindingItem(
                detector=self.name,
                category=AudioFindingCategory.NOISE,
                severity=Severity.LOW,
                description="Background noise-floor variation observed.",
                explanation=(
                    "Quiet segments show differing noise-floor levels, which may "
                    "indicate environmental acoustic changes."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=min(0.65, spread * 10.0),
                temporal=temporal,
                metadata={"noise_floor_spread": spread},
                model_name="noise_classical",
                model_version=self.version,
                model_framework="NATIVE",
                limitations=(
                    "Recording environment changes are not inherently fraudulent."
                ),
            ),
            temporal,
        )
        return (finding,)
