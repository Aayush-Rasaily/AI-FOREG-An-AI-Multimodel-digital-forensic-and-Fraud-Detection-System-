"""Silence manipulation detector."""

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


class SilenceDetector(AudioAIDetector):
    name = "silence"
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
            description="Detects abrupt or repeated silence patterns.",
            supported_tasks=("silence_analysis",),
            model_name="silence_classical",
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
            model_name="silence_classical",
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
        findings: list[AudioAIFindingItem] = []
        silent_runs = 0
        for entry in metrics:
            if float(entry["rms"]) >= 0.005:
                silent_runs = 0
                continue
            silent_runs += 1
            if silent_runs < 2:
                continue
            temporal = temporal_from_ms(
                int(entry["start_time_ms"]),
                int(entry["end_time_ms"]),
                "SILENCE_SEGMENT",
            )
            finding = attach_temporal(
                AudioAIFindingItem(
                    detector=self.name,
                    category=AudioFindingCategory.SILENCE,
                    severity=Severity.INFO,
                    description="Extended low-energy silence segment detected.",
                    explanation=(
                        "A sequence of low-energy windows was observed. This may "
                        "reflect natural pauses or inserted silence."
                    ),
                    method=DetectionMethod.CLASSICAL,
                    confidence=0.55,
                    temporal=temporal,
                    model_name="silence_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                    limitations="Natural pauses are common in speech recordings.",
                ),
                temporal,
            )
            findings.append(finding)
        return tuple(findings[:5])
