"""Audio splicing indicator detector."""

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


class SplicingDetector(AudioAIDetector):
    name = "splicing"
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
            description="Detects abrupt feature changes that may indicate splicing.",
            supported_tasks=("splicing_detection",),
            model_name="splicing_classical",
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
            model_name="splicing_classical",
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
        for previous, current in zip(metrics, metrics[1:], strict=False):
            rms_delta = abs(float(current["rms"]) - float(previous["rms"]))
            mfcc_delta = abs(float(current["mfcc0"]) - float(previous["mfcc0"]))
            if rms_delta < 0.08 and mfcc_delta < 0.5:
                continue
            temporal = temporal_from_ms(
                int(current["start_time_ms"]),
                int(current["end_time_ms"]),
                "SPLICING_BOUNDARY",
            )
            finding = AudioAIFindingItem(
                detector=self.name,
                category=AudioFindingCategory.SPLICING,
                severity=Severity.LOW,
                description="Potential splicing boundary indicator.",
                explanation=(
                    "Adjacent temporal windows show abrupt acoustic feature "
                    "changes that may indicate an edit boundary."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=min(0.72, rms_delta + mfcc_delta / 5.0),
                temporal=temporal,
                metadata={"rms_delta": rms_delta, "mfcc_delta": mfcc_delta},
                model_name="splicing_classical",
                model_version=self.version,
                model_framework="NATIVE",
                limitations="Natural speech pauses can resemble splicing boundaries.",
            )
            findings.append(attach_temporal(finding, temporal))
        return tuple(findings[:8])
