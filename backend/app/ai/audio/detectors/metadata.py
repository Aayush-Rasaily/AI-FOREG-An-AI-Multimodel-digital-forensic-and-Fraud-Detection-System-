"""Audio metadata inconsistency detector."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.app.ai.audio.detectors.base import AudioAIDetector
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


class MetadataDetector(AudioAIDetector):
    name = "metadata"
    version = "1.0.0"

    def __init__(self) -> None:
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
            description="Inspects audio container and stream metadata.",
            supported_tasks=("metadata_analysis",),
            model_name="metadata_classical",
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
            model_name="metadata_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: AudioAnalysisContext,
    ) -> tuple[AudioAIFindingItem, ...]:
        meta = context.extraction_metadata
        if not meta:
            return ()
        observations = {
            key: meta.get(key)
            for key in ("codec", "format", "duration", "sample_rate", "channels")
            if meta.get(key) is not None
        }
        if context.duration_ms is not None:
            observations["duration_ms"] = context.duration_ms
        if not observations:
            return ()
        inconsistent = False
        extracted_duration = meta.get("duration")
        if (
            isinstance(extracted_duration, (int, float))
            and context.duration_ms is not None
        ):
            delta = abs(context.duration_ms - int(float(extracted_duration) * 1000))
            inconsistent = delta > 250
            observations["duration_delta_ms"] = delta
        return (
            AudioAIFindingItem(
                detector=self.name,
                category=AudioFindingCategory.METADATA,
                severity=Severity.MEDIUM if inconsistent else Severity.INFO,
                description=(
                    "Metadata inconsistency detected."
                    if inconsistent
                    else "Audio metadata captured from extraction."
                ),
                explanation=(
                    "Duration metadata differs from decoded sample duration."
                    if inconsistent
                    else "Container metadata recorded for review."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=0.6 if inconsistent else None,
                metadata=observations,
                model_name="metadata_classical",
                model_version=self.version,
                model_framework="NATIVE",
                limitations="Metadata alone does not prove fraud.",
            ),
        )
