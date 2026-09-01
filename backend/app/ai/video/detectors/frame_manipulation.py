"""Frame manipulation detector."""

from __future__ import annotations

import asyncio
import hashlib
import time
from typing import Any

import numpy as np

from backend.app.ai.video.detectors.base import VideoAIDetector
from backend.app.ai.video.localization.temporal import attach_temporal
from backend.app.ai.video.models.base import (
    DetectionMethod,
    TemporalEvidence,
    VideoAIFindingItem,
    VideoAnalysisContext,
    VideoDetectorMetadata,
    VideoDetectorOutput,
    VideoFindingCategory,
)
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class FrameManipulationDetector(VideoAIDetector):
    """Detect duplicated frames and abrupt perceptual discontinuities."""

    name = "frame_manipulation"
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
            description=(
                "Detects repeated frames and abrupt perceptual changes using "
                "classical frame similarity."
            ),
            supported_tasks=(
                "frame_duplication",
                "frame_insertion",
                "frame_deletion",
            ),
            model_name="frame_manipulation_classical",
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
            model_name="frame_manipulation_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: VideoAnalysisContext,
    ) -> tuple[VideoAIFindingItem, ...]:
        decoded = [
            frame
            for frame in context.sampled_frames
            if frame.image_array is not None
        ]
        if len(decoded) < 2:
            return ()
        findings: list[VideoAIFindingItem] = []
        previous_hash: str | None = None
        previous_frame = decoded[0]
        for frame in decoded[1:]:
            image_array = frame.image_array
            assert image_array is not None
            current_hash = _perceptual_hash(image_array)
            if previous_hash is not None and current_hash == previous_hash:
                temporal = TemporalEvidence(
                    start_frame=previous_frame.frame_number,
                    end_frame=frame.frame_number,
                    start_timestamp_ms=previous_frame.timestamp_ms,
                    end_timestamp_ms=frame.timestamp_ms,
                    evidence_type="FRAME_DUPLICATION",
                )
                finding = VideoAIFindingItem(
                    detector=self.name,
                    category=VideoFindingCategory.FRAME_MANIPULATION,
                    severity=Severity.LOW,
                    description="Repeated consecutive sampled frames detected.",
                    explanation=(
                        "Two consecutive sampled frames share an identical perceptual "
                        "hash. This may indicate duplication or a static segment."
                    ),
                    method=DetectionMethod.CLASSICAL,
                    confidence=0.72,
                    temporal=temporal,
                    metadata={"perceptual_hash": current_hash},
                    model_name="frame_manipulation_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                    limitations=(
                        "Static camera segments and paused video "
                        "can produce duplicates."
                    ),
                )
                findings.append(attach_temporal(finding, temporal))
            previous_hash = current_hash
            previous_frame = frame
        return tuple(findings)


def _perceptual_hash(array: np.ndarray) -> str:
    """Compute a simple average-hash for frame comparison."""

    from PIL import Image

    image = Image.fromarray(array.astype(np.uint8), mode="RGB")
    thumbnail = image.resize((8, 8)).convert("L")
    pixels = np.asarray(thumbnail, dtype=np.float32)
    average = pixels.mean()
    bits = (pixels >= average).astype(np.uint8).flatten()
    digest = hashlib.sha256(bits.tobytes()).hexdigest()
    return digest
