"""Speaker consistency and reference comparison detector."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import numpy as np

from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.detectors._utils import unavailable_finding
from backend.app.ai.audio.detectors._windows import window_metrics
from backend.app.ai.audio.detectors.base import AudioAIDetector
from backend.app.ai.audio.features.waveform import simplified_mfcc
from backend.app.ai.audio.models import (
    AudioAIFindingItem,
    AudioAnalysisContext,
    AudioDetectorMetadata,
    AudioDetectorOutput,
    AudioFindingCategory,
    DetectionMethod,
    DetectorCapabilityStatus,
)
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class SpeakerConsistencyDetector(AudioAIDetector):
    name = "speaker_consistency"
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
            description=(
                "Analyzes speaker consistency and optional reference comparison."
            ),
            supported_tasks=("speaker_consistency", "reference_comparison"),
            model_name="speaker_classical",
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
        if context.samples is None or context.sample_rate is None:
            finding = unavailable_finding(
                detector=self.name,
                category=AudioFindingCategory.SPEAKER_INCONSISTENCY,
                reason="decoded_audio_unavailable",
            )
            return AudioDetectorOutput(
                detector=self.name,
                version=self.version,
                findings=(finding,),
                metadata={"status": "unavailable"},
                latency_ms=(time.perf_counter() - started) * 1000.0,
                model_name="speaker_classical",
                model_version=self.version,
                method=DetectionMethod.CLASSICAL,
                status=DetectorCapabilityStatus.UNAVAILABLE,
            )
        findings = await asyncio.to_thread(self._analyze, context)
        return AudioDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=findings,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            model_name="speaker_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: AudioAnalysisContext,
    ) -> tuple[AudioAIFindingItem, ...]:
        assert context.samples is not None and context.sample_rate is not None
        metrics = window_metrics(
            context.samples,
            sample_rate=context.sample_rate,
            window_seconds=self._settings.window_seconds,
            hop_seconds=self._settings.hop_seconds,
        )
        mfcc_values = [float(entry["mfcc0"]) for entry in metrics]
        findings: list[AudioAIFindingItem] = []
        if len(mfcc_values) >= 3:
            spread = max(mfcc_values) - min(mfcc_values)
            if spread > 1.0:
                findings.append(
                    AudioAIFindingItem(
                        detector=self.name,
                        category=AudioFindingCategory.SPEAKER_INCONSISTENCY,
                        severity=Severity.LOW,
                        description=(
                            "Acoustic speaker characteristics vary across segments."
                        ),
                        explanation=(
                            "MFCC-derived features differ across temporal windows. "
                            "This does not identify a specific speaker or fraud."
                        ),
                        method=DetectionMethod.CLASSICAL,
                        confidence=min(0.68, spread / 3.0),
                        metadata={"mfcc_spread": spread},
                        model_name="speaker_classical",
                        model_version=self.version,
                        model_framework="NATIVE",
                        limitations="Multiple speakers or scene changes are normal.",
                    )
                )
        if context.reference_samples is not None and context.reference_sample_rate:
            questioned = simplified_mfcc(context.samples, context.sample_rate)
            reference = simplified_mfcc(
                context.reference_samples,
                context.reference_sample_rate,
            )
            distance = float(np.linalg.norm(questioned - reference))
            similarity = max(0.0, 1.0 - min(distance / 10.0, 1.0))
            findings.append(
                AudioAIFindingItem(
                    detector=self.name,
                    category=AudioFindingCategory.REFERENCE_MISMATCH,
                    severity=Severity.INFO,
                    description="Reference voice comparison completed.",
                    explanation=(
                        "Deterministic MFCC comparison against reference audio. "
                        "This is not a validated identity model."
                    ),
                    method=DetectionMethod.REFERENCE,
                    confidence=similarity,
                    metadata={
                        "similarity": round(similarity, 4),
                        "mfcc_distance": round(distance, 4),
                        "reference_evidence_id": (
                            str(context.reference_evidence_id)
                            if context.reference_evidence_id
                            else None
                        ),
                    },
                    model_name="speaker_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                    limitations="Does not prove speaker identity.",
                )
            )
        return tuple(findings)
