"""Orchestrates enabled video AI detectors."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import replace
from typing import Any

from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.video.config import VideoAISettings
from backend.app.ai.video.exceptions import (
    VideoAnalysisTimeoutError,
    VideoDetectorError,
)
from backend.app.ai.video.models.base import (
    VideoAIFindingItem,
    VideoAnalysisResult,
    VideoAnalysisRunStatus,
    VideoDetectorOutput,
)
from backend.app.ai.video.models.context import VideoAnalysisContext
from backend.app.ai.video.pipelines.video_pipeline import prepare_video_context
from backend.app.ai.video.postprocessing.aggregation import build_timeline
from backend.app.ai.video.postprocessing.findings import normalize_detector_output
from backend.app.ai.video.registry import VideoDetectorRegistry
from backend.app.domain.processing import EvidenceClassification

logger = logging.getLogger(__name__)

ENGINE_VERSION = "1.0"


class VideoAnalysisEngine:
    """Run configured video AI detectors and aggregate normalized findings."""

    def __init__(
        self,
        registry: VideoDetectorRegistry,
        device_manager: DeviceManager,
        settings: VideoAISettings | None = None,
    ) -> None:
        self.registry = registry
        self.device_manager = device_manager
        self.settings = settings or VideoAISettings()

    async def analyze(self, context: VideoAnalysisContext) -> VideoAnalysisResult:
        """Execute all enabled detectors compatible with the context."""

        if context.classification != EvidenceClassification.VIDEO:
            return VideoAnalysisResult(
                status=VideoAnalysisRunStatus.FAILED,
                error_code="UNSUPPORTED_EVIDENCE",
                error_message_safe="AI video analysis requires video evidence.",
            )
        started = time.perf_counter()
        device = self.device_manager.select_device(self.settings.default_device)
        prepared, pipeline_artifacts = await prepare_video_context(
            replace(context, device=device)
        )
        findings: list[VideoAIFindingItem] = []
        artifacts = list(pipeline_artifacts)
        outputs: list[VideoDetectorOutput] = []
        metadata: dict[str, Any] = {
            "engine_version": ENGINE_VERSION,
            "device": device,
            "detectors": [],
            "video": {
                "duration_ms": prepared.duration_ms,
                "fps": prepared.fps,
                "frame_count": prepared.frame_count,
                "codec": prepared.codec,
                "container": prepared.container,
            },
            "frames_sampled": len(prepared.sampled_frames),
        }
        for name in self.registry.enabled_names():
            detector = self.registry.lookup(name, device=device)
            if not detector.supports(prepared):
                continue
            try:
                output = await asyncio.wait_for(
                    detector.predict(prepared),
                    timeout=self.settings.inference_timeout_seconds,
                )
            except TimeoutError as exc:
                raise VideoAnalysisTimeoutError(
                    "ANALYSIS_TIMEOUT",
                    f"Detector '{name}' exceeded the configured timeout.",
                ) from exc
            except Exception as exc:
                raise VideoDetectorError(
                    "DETECTOR_FAILED",
                    f"Detector '{name}' failed during inference.",
                ) from exc
            normalized = normalize_detector_output(output)
            findings.extend(normalized)
            artifacts.extend(output.artifacts)
            outputs.append(output)
            metadata["detectors"].append(
                {
                    "name": name,
                    "latency_ms": output.latency_ms,
                    "findings_count": len(output.findings),
                    "model_name": output.model_name,
                    "model_version": output.model_version,
                    "method": output.method.value,
                }
            )
        timeline = build_timeline(tuple(findings))
        latency_ms = (time.perf_counter() - started) * 1000.0
        return VideoAnalysisResult(
            status=VideoAnalysisRunStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=tuple(artifacts),
            metadata=metadata,
            detector_outputs=tuple(outputs),
            timeline=timeline,
            sampled_frames=prepared.sampled_frames,
            latency_ms=latency_ms,
            device=device,
        )
