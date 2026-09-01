"""Compression and codec metadata detector."""

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


class CompressionDetector(AudioAIDetector):
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

    def metadata(self) -> AudioDetectorMetadata:
        return AudioDetectorMetadata(
            name=self.name,
            version=self.version,
            author="AI-FORGE Engineering",
            description="Reports codec and compression metadata observations.",
            supported_tasks=("compression_analysis",),
            model_name="compression_classical",
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
            model_name="compression_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: AudioAnalysisContext,
    ) -> tuple[AudioAIFindingItem, ...]:
        codec = context.codec
        if not codec:
            return ()
        meta = context.extraction_metadata
        return (
            AudioAIFindingItem(
                detector=self.name,
                category=AudioFindingCategory.COMPRESSION,
                severity=Severity.INFO,
                description="Audio compression metadata recorded.",
                explanation=(
                    f"Container reports codec '{codec}'. Compression metadata "
                    "alone does not indicate manipulation."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=None,
                metadata={
                    "codec": codec,
                    "sample_rate": context.sample_rate,
                    "bitrate": meta.get("bit_rate") or meta.get("bitrate"),
                },
                model_name="compression_classical",
                model_version=self.version,
                model_framework="NATIVE",
                limitations="Informational only.",
            ),
        )
