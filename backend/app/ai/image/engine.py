"""Orchestrates enabled image AI detectors."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.image.config import ImageAISettings
from backend.app.ai.image.exceptions import (
    ImageAnalysisTimeoutError,
    ImageDetectorError,
)
from backend.app.ai.image.models import (
    ImageAIFindingItem,
    ImageAnalysisContext,
    ImageAnalysisResult,
    ImageAnalysisRunStatus,
    ImageDetectorOutput,
)
from backend.app.ai.image.postprocessing.findings import normalize_detector_output
from backend.app.ai.image.registry import ImageDetectorRegistry
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import EvidenceClassification

logger = logging.getLogger(__name__)

ENGINE_VERSION = "1.0"


class ImageAnalysisEngine:
    """Run configured image AI detectors and aggregate normalized findings."""

    def __init__(
        self,
        registry: ImageDetectorRegistry,
        device_manager: DeviceManager,
        settings: ImageAISettings | None = None,
    ) -> None:
        self.registry = registry
        self.device_manager = device_manager
        self.settings = settings or ImageAISettings()

    async def analyze(self, context: ImageAnalysisContext) -> ImageAnalysisResult:
        """Execute all enabled detectors compatible with the context."""

        if context.classification != EvidenceClassification.IMAGE:
            return ImageAnalysisResult(
                status=ImageAnalysisRunStatus.FAILED,
                error_code="UNSUPPORTED_EVIDENCE",
                error_message_safe="AI image analysis requires image evidence.",
            )
        started = time.perf_counter()
        device = self.device_manager.select_device(self.settings.default_device)
        findings: list[ImageAIFindingItem] = []
        artifacts: list[DerivedArtifactPayload] = []
        outputs: list[ImageDetectorOutput] = []
        metadata: dict[str, Any] = {
            "engine_version": ENGINE_VERSION,
            "device": device,
            "detectors": [],
        }
        for name in self.registry.enabled_names():
            detector = self.registry.lookup(name, device=device)
            if not detector.supports(context):
                continue
            try:
                output = await asyncio.wait_for(
                    detector.predict(context),
                    timeout=self.settings.inference_timeout_seconds,
                )
            except TimeoutError as exc:
                raise ImageAnalysisTimeoutError(
                    "ANALYSIS_TIMEOUT",
                    f"Detector '{name}' exceeded the configured timeout.",
                ) from exc
            except Exception as exc:
                raise ImageDetectorError(
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
                }
            )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return ImageAnalysisResult(
            status=ImageAnalysisRunStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=tuple(artifacts),
            metadata=metadata,
            detector_outputs=tuple(outputs),
            latency_ms=latency_ms,
            device=device,
        )
