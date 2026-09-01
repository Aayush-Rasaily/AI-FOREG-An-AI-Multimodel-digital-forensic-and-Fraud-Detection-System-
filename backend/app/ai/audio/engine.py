"""Orchestrates enabled audio AI detectors."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import replace
from typing import Any

from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.exceptions import (
    AudioAnalysisTimeoutError,
    AudioDetectorError,
)
from backend.app.ai.audio.models import (
    AudioAIFindingItem,
    AudioAnalysisContext,
    AudioAnalysisResult,
    AudioAnalysisRunStatus,
    AudioDetectorOutput,
)
from backend.app.ai.audio.pipelines.audio_pipeline import prepare_audio_context
from backend.app.ai.audio.postprocessing.aggregation import (
    build_segments,
    build_timeline,
)
from backend.app.ai.audio.postprocessing.findings import normalize_detector_output
from backend.app.ai.audio.registry import AudioDetectorRegistry
from backend.app.ai.device.manager import DeviceManager
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification

logger = logging.getLogger(__name__)

ENGINE_VERSION = "1.0"


class AudioAnalysisEngine:
    """Run configured audio AI detectors and aggregate normalized findings."""

    def __init__(
        self,
        registry: AudioDetectorRegistry,
        device_manager: DeviceManager,
        settings: AudioAISettings | None = None,
    ) -> None:
        self.registry = registry
        self.device_manager = device_manager
        self.settings = settings or AudioAISettings()

    async def analyze(self, context: AudioAnalysisContext) -> AudioAnalysisResult:
        """Execute all enabled detectors compatible with the context."""

        if context.classification != EvidenceClassification.AUDIO:
            return AudioAnalysisResult(
                status=AudioAnalysisRunStatus.FAILED,
                error_code="UNSUPPORTED_EVIDENCE",
                error_message_safe="AI audio analysis requires audio evidence.",
            )
        started = time.perf_counter()
        device = self.device_manager.select_device(self.settings.default_device)
        prepared, pipeline_artifacts = await prepare_audio_context(
            replace(context, device=device)
        )
        findings: list[AudioAIFindingItem] = []
        artifacts: list[DerivedArtifactPayload] = list(pipeline_artifacts)
        outputs: list[AudioDetectorOutput] = []
        metadata: dict[str, Any] = {
            "engine_version": ENGINE_VERSION,
            "device": device,
            "detectors": [],
            "audio": {
                "duration_ms": prepared.duration_ms,
                "sample_rate": prepared.sample_rate,
                "channels": prepared.channels,
                "codec": prepared.codec,
            },
            "capabilities": prepared.capabilities,
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
                raise AudioAnalysisTimeoutError(
                    "ANALYSIS_TIMEOUT",
                    f"Detector '{name}' exceeded the configured timeout.",
                ) from exc
            except Exception as exc:
                raise AudioDetectorError(
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
                    "status": output.status.value,
                }
            )
        timeline = build_timeline(tuple(findings))
        segments = build_segments(tuple(findings))
        artifacts.append(
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_AUDIO_TIMELINE,
                mime_type="application/json",
                content=json.dumps(
                    {"timeline": list(timeline), "segments": list(segments)},
                    sort_keys=True,
                ).encode("utf-8"),
                metadata={
                    "timeline_entries": len(timeline),
                    "segment_count": len(segments),
                },
            )
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return AudioAnalysisResult(
            status=AudioAnalysisRunStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=tuple(artifacts),
            metadata=metadata,
            detector_outputs=tuple(outputs),
            timeline=timeline,
            segments=segments,
            feature_summary=prepared.feature_summary,
            latency_ms=latency_ms,
            device=device,
        )
