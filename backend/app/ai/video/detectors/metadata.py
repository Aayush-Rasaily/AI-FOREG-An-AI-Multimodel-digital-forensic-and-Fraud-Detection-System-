"""Video metadata anomaly detector."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.app.ai.video.detectors.base import VideoAIDetector
from backend.app.ai.video.models.base import (
    DetectionMethod,
    VideoAIFindingItem,
    VideoAnalysisContext,
    VideoDetectorMetadata,
    VideoDetectorOutput,
    VideoFindingCategory,
)
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class MetadataDetector(VideoAIDetector):
    """Inspect container and encoder metadata from Phase 5 extraction."""

    name = "metadata"
    version = "1.0.0"

    SUSPICIOUS_KEYS = ("encoder", "creation_time", "handler_name", "major_brand")

    def __init__(self) -> None:
        self._loaded = False

    def load(self, *, device: str) -> None:
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> VideoDetectorMetadata:
        return VideoDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description="Reports video container and encoder metadata observations.",
            supported_tasks=("metadata_analysis",),
            model_name="metadata_classical",
            model_version=self.version,
            framework="NATIVE",
            method=DetectionMethod.CLASSICAL,
        )

    def supports(self, context: VideoAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.VIDEO

    def health(self) -> dict[str, Any]:
        return {"loaded": self._loaded, "method": DetectionMethod.CLASSICAL.value}

    async def predict(self, context: VideoAnalysisContext) -> VideoDetectorOutput:
        started = time.perf_counter()
        findings = await asyncio.to_thread(self._analyze, context)
        return VideoDetectorOutput(
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
        context: VideoAnalysisContext,
    ) -> tuple[VideoAIFindingItem, ...]:
        meta = context.extraction_metadata
        if not meta:
            return ()
        observations = {
            key: meta.get(key)
            for key in self.SUSPICIOUS_KEYS
            if meta.get(key) is not None
        }
        if context.duration_ms is not None:
            observations["duration_ms"] = context.duration_ms
        if context.fps is not None:
            observations["fps"] = context.fps
        if not observations:
            return ()
        finding = VideoAIFindingItem(
            detector=self.name,
            category=VideoFindingCategory.METADATA,
            severity=Severity.INFO,
            description="Video metadata captured from extraction.",
            explanation=(
                "Container metadata was recorded for review. Metadata alone does "
                "not indicate fraud."
            ),
            method=DetectionMethod.CLASSICAL,
            confidence=None,
            metadata=observations,
            model_name="metadata_classical",
            model_version=self.version,
            model_framework="NATIVE",
            limitations="Metadata observations require corroborating evidence.",
        )
        return (finding,)
