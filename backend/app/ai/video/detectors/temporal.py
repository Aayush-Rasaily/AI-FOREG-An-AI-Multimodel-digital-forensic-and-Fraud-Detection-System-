"""Temporal inconsistency detector."""

from __future__ import annotations

import asyncio
import time
from typing import Any

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


class TemporalDetector(VideoAIDetector):
    """Detect timestamp and frame-index discontinuities."""

    name = "temporal"
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
            description="Detects temporal discontinuities in sampled frame schedules.",
            supported_tasks=("temporal_analysis", "timestamp_continuity"),
            model_name="temporal_classical",
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
            model_name="temporal_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: VideoAnalysisContext,
    ) -> tuple[VideoAIFindingItem, ...]:
        frames = context.sampled_frames
        if len(frames) < 2:
            return ()
        findings: list[VideoAIFindingItem] = []
        fps = context.fps or 0.0
        for previous, current in zip(frames, frames[1:], strict=False):
            delta_ms = current.timestamp_ms - previous.timestamp_ms
            if delta_ms <= 0:
                temporal = TemporalEvidence(
                    start_frame=previous.frame_number,
                    end_frame=current.frame_number,
                    start_timestamp_ms=previous.timestamp_ms,
                    end_timestamp_ms=current.timestamp_ms,
                    evidence_type="TEMPORAL_INCONSISTENCY",
                )
                finding = VideoAIFindingItem(
                    detector=self.name,
                    category=VideoFindingCategory.TEMPORAL_INCONSISTENCY,
                    severity=Severity.MEDIUM,
                    description="Non-monotonic timestamp progression detected.",
                    explanation=(
                        "Sampled frame timestamps did not increase monotonically, "
                        "which may indicate reordering or index corruption."
                    ),
                    method=DetectionMethod.CLASSICAL,
                    confidence=min(0.85, 0.55 + abs(delta_ms) / 1000.0),
                    temporal=temporal,
                    metadata={"delta_ms": delta_ms},
                    model_name="temporal_classical",
                    model_version=self.version,
                    model_framework="NATIVE",
                    limitations=(
                        "Natural scene cuts are not classified as manipulation."
                    ),
                )
                findings.append(attach_temporal(finding, temporal))
            elif fps > 0:
                expected_ms = 1000.0 / fps
                if delta_ms > expected_ms * 3:
                    temporal = TemporalEvidence(
                        start_frame=previous.frame_number,
                        end_frame=current.frame_number,
                        start_timestamp_ms=previous.timestamp_ms,
                        end_timestamp_ms=current.timestamp_ms,
                        evidence_type="TEMPORAL_GAP",
                    )
                    finding = VideoAIFindingItem(
                        detector=self.name,
                        category=VideoFindingCategory.TEMPORAL_INCONSISTENCY,
                        severity=Severity.LOW,
                        description="Extended temporal gap between sampled frames.",
                        explanation=(
                            "The interval between consecutive sampled frames exceeds "
                            "three frame durations. This may reflect scene cuts or "
                            "sampling gaps rather than manipulation."
                        ),
                        method=DetectionMethod.CLASSICAL,
                        confidence=min(0.7, delta_ms / (expected_ms * 10)),
                        temporal=temporal,
                        metadata={
                            "delta_ms": delta_ms,
                            "expected_ms": round(expected_ms, 3),
                        },
                        model_name="temporal_classical",
                        model_version=self.version,
                        model_framework="NATIVE",
                        limitations="Scene cuts produce similar gaps and are expected.",
                    )
                    findings.append(attach_temporal(finding, temporal))
        return tuple(findings)
