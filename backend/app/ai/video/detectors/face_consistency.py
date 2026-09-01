"""Face consistency detector across sampled frames."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.app.ai.video.detectors.base import VideoAIDetector
from backend.app.ai.video.localization.frame import localize_on_frame
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
from backend.app.ai.video.preprocessing.faces import HeuristicFaceTracker
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import Severity


class FaceConsistencyDetector(VideoAIDetector):
    """Track faces across frames and report identity inconsistencies."""

    name = "face_consistency"
    version = "1.0.0"

    def __init__(self) -> None:
        self._loaded = False
        self._tracker = HeuristicFaceTracker()

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
                "Tracks faces across sampled frames and reports spatial or "
                "identity inconsistencies without fraud classification."
            ),
            supported_tasks=("face_tracking", "face_consistency", "face_swap_support"),
            model_name="face_consistency_classical",
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
        findings, metadata = await asyncio.to_thread(self._analyze, context)
        return VideoDetectorOutput(
            detector=self.name,
            version=self.version,
            findings=findings,
            metadata=metadata,
            latency_ms=(time.perf_counter() - started) * 1000.0,
            model_name="face_consistency_classical",
            model_version=self.version,
            method=DetectionMethod.CLASSICAL,
        )

    def _analyze(
        self,
        context: VideoAnalysisContext,
    ) -> tuple[tuple[VideoAIFindingItem, ...], dict[str, Any]]:
        decoded = [
            (
                frame.frame_number,
                frame.timestamp_ms,
                frame.image_array,
                frame.width or 0,
                frame.height or 0,
            )
            for frame in context.sampled_frames
            if frame.image_array is not None and frame.width and frame.height
        ]
        if not decoded:
            return (), {"face_count": 0, "status": "no_decoded_frames"}
        tracked = self._tracker.track(
            tuple(
                (frame_number, timestamp_ms, rgb, width, height)
                for frame_number, timestamp_ms, rgb, width, height in decoded
            )
        )
        if not tracked:
            return (), {"face_count": 0, "status": "no_faces_detected"}
        findings: list[VideoAIFindingItem] = []
        by_frame: dict[int, list[Any]] = {}
        for face in tracked:
            by_frame.setdefault(face.frame_number, []).append(face)
        for frame_number, faces in by_frame.items():
            if len(faces) <= 1:
                continue
            frame_ref = next(
                frame
                for frame in context.sampled_frames
                if frame.frame_number == frame_number
            )
            regions = tuple(
                localize_on_frame(
                    frame=frame_ref,
                    x=face.x,
                    y=face.y,
                    width=face.width,
                    height=face.height,
                )
                for face in faces
            )
            temporal = TemporalEvidence(
                start_frame=frame_number,
                end_frame=frame_number,
                start_timestamp_ms=faces[0].timestamp_ms,
                end_timestamp_ms=faces[0].timestamp_ms,
                evidence_type="MULTIPLE_FACES",
            )
            finding = VideoAIFindingItem(
                detector=self.name,
                category=VideoFindingCategory.FACE_INCONSISTENCY,
                severity=Severity.INFO,
                description="Multiple faces detected in one sampled frame.",
                explanation=(
                    "Multiple distinct face regions were detected in the same frame. "
                    "This is expected when multiple people appear and is not fraud."
                ),
                method=DetectionMethod.CLASSICAL,
                confidence=0.6,
                regions=regions,
                temporal=temporal,
                metadata={"face_count": len(faces), "frame_number": frame_number},
                model_name="face_consistency_classical",
                model_version=self.version,
                model_framework="NATIVE",
                limitations="Does not classify different people as fraudulent.",
            )
            findings.append(attach_temporal(finding, temporal))
        return tuple(findings), {"face_count": len(tracked), "status": "tracked"}
