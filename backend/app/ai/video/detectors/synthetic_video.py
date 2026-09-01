"""Synthetic / AI-generated video detector plugin."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from backend.app.ai.video.config import VideoAISettings
from backend.app.ai.video.detectors._utils import unavailable_finding, verify_model_hash
from backend.app.ai.video.detectors.base import VideoAIDetector
from backend.app.ai.video.models.base import (
    DetectionMethod,
    VideoAnalysisContext,
    VideoDetectorMetadata,
    VideoDetectorOutput,
    VideoFindingCategory,
)
from backend.app.domain.processing import EvidenceClassification


class SyntheticVideoDetector(VideoAIDetector):
    """Detect AI-generated video and synthetic motion artifacts."""

    name = "synthetic_video"
    version = "1.0.0"

    def __init__(self, settings: VideoAISettings | None = None) -> None:
        self._settings = settings or VideoAISettings()
        self._loaded = False
        self._device = "cpu"
        self._model_available = False

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = True
        self._model_available = False
        if not self._settings.synthetic_model_enabled:
            return
        path_value = self._settings.synthetic_model_path
        if not path_value:
            return
        path = Path(path_value)
        if not path.exists():
            return
        verify_model_hash(path, self._settings.synthetic_model_sha256)
        self._model_available = True

    def unload(self) -> None:
        self._loaded = False
        self._model_available = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> VideoDetectorMetadata:
        return VideoDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description="Detects AI-generated video and synthetic motion patterns.",
            supported_tasks=("synthetic_video_detection", "generative_video_detection"),
            model_name="video_synthetic",
            model_version=self._settings.synthetic_model_version,
            framework="PYTORCH",
            method=DetectionMethod.AI,
        )

    def supports(self, context: VideoAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.VIDEO

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "model_available": self._model_available,
            "status": "available" if self._model_available else "unavailable",
        }

    async def predict(self, context: VideoAnalysisContext) -> VideoDetectorOutput:
        started = time.perf_counter()
        if not self._model_available:
            finding = unavailable_finding(
                detector=self.name,
                category=VideoFindingCategory.SYNTHETIC_VIDEO,
                reason="model_not_configured",
                model_name="video_synthetic",
                model_version=self._settings.synthetic_model_version,
            )
            return VideoDetectorOutput(
                detector=self.name,
                version=self.version,
                findings=(finding,),
                metadata={"status": "unavailable", "reason": "model_not_configured"},
                latency_ms=(time.perf_counter() - started) * 1000.0,
                model_name="video_synthetic",
                model_version=self._settings.synthetic_model_version,
                method=DetectionMethod.AI,
            )
        return VideoDetectorOutput(
            detector=self.name,
            version=self.version,
            metadata={
                "status": "available",
                "frames_analyzed": len(context.sampled_frames),
            },
            latency_ms=(time.perf_counter() - started) * 1000.0,
            model_name="video_synthetic",
            model_version=self._settings.synthetic_model_version,
            method=DetectionMethod.AI,
        )
