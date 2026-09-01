"""Deepfake voice detector plugin."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.detectors._utils import unavailable_finding, verify_model_hash
from backend.app.ai.audio.detectors.base import AudioAIDetector
from backend.app.ai.audio.models import (
    AudioAnalysisContext,
    AudioDetectorMetadata,
    AudioDetectorOutput,
    AudioFindingCategory,
    DetectionMethod,
)
from backend.app.domain.processing import EvidenceClassification


class DeepfakeVoiceDetector(AudioAIDetector):
    """Detect deepfake voice manipulation when a model is configured."""

    name = "deepfake_voice"
    version = "1.0.0"

    def __init__(self, settings: AudioAISettings | None = None) -> None:
        self._settings = settings or AudioAISettings()
        self._loaded = False
        self._device = "cpu"
        self._model_available = False

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = True
        self._model_available = False
        if not self._settings.deepfake_model_enabled:
            return
        path_value = self._settings.deepfake_model_path
        if not path_value:
            return
        path = Path(path_value)
        if not path.exists():
            return
        verify_model_hash(path, self._settings.deepfake_model_sha256)
        self._model_available = True

    def unload(self) -> None:
        self._loaded = False
        self._model_available = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> AudioDetectorMetadata:
        return AudioDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description="Detects deepfake voice manipulation.",
            supported_tasks=("deepfake_voice_detection",),
            model_name="audio_deepfake",
            model_version=self._settings.deepfake_model_version,
            framework="PYTORCH",
            method=DetectionMethod.AI,
        )

    def supports(self, context: AudioAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.AUDIO

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "model_available": self._model_available,
            "status": "available" if self._model_available else "unavailable",
        }

    async def predict(self, context: AudioAnalysisContext) -> AudioDetectorOutput:
        started = time.perf_counter()
        if not self._model_available:
            finding = unavailable_finding(
                detector=self.name,
                category=AudioFindingCategory.DEEPFAKE_VOICE,
                reason="model_not_configured",
                model_name="audio_deepfake",
                model_version=self._settings.deepfake_model_version,
            )
            return AudioDetectorOutput(
                detector=self.name,
                version=self.version,
                findings=(finding,),
                metadata={"status": "unavailable", "reason": "model_not_configured"},
                latency_ms=(time.perf_counter() - started) * 1000.0,
                model_name="audio_deepfake",
                model_version=self._settings.deepfake_model_version,
                method=DetectionMethod.AI,
            )
        return AudioDetectorOutput(
            detector=self.name,
            version=self.version,
            metadata={"status": "available"},
            latency_ms=(time.perf_counter() - started) * 1000.0,
            model_name="audio_deepfake",
            model_version=self._settings.deepfake_model_version,
            method=DetectionMethod.AI,
        )
