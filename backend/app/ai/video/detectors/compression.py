"""Compression inconsistency detector."""

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


class CompressionDetector(VideoAIDetector):
    """Report codec and container compression metadata observations."""

    name = "compression"
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

    def metadata(self) -> VideoDetectorMetadata:
        return VideoDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description="Reports compression and codec metadata observations.",
            supported_tasks=("compression_analysis",),
            model_name="compression_classical",
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
            model_name="compression_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: VideoAnalysisContext,
    ) -> tuple[VideoAIFindingItem, ...]:
        codec = context.codec
        if not codec:
            return ()
        meta = context.extraction_metadata
        bitrate = meta.get("bit_rate") or meta.get("bitrate")
        finding = VideoAIFindingItem(
            detector=self.name,
            category=VideoFindingCategory.COMPRESSION,
            severity=Severity.INFO,
            description="Video compression metadata recorded.",
            explanation=(
                f"Container reports codec '{codec}'. Compression characteristics "
                "alone do not indicate manipulation."
            ),
            method=DetectionMethod.CLASSICAL,
            confidence=None,
            metadata={
                "codec": codec,
                "container": context.container,
                "bitrate": bitrate,
            },
            model_name="compression_classical",
            model_version=self.version,
            model_framework="NATIVE",
            limitations="Compression metadata is informational only.",
        )
        return (finding,)
