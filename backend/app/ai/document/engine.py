"""Orchestrates enabled document AI detectors."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.document.config import DocumentAISettings
from backend.app.ai.document.exceptions import (
    DocumentAnalysisTimeoutError,
    DocumentDetectorError,
)
from backend.app.ai.document.models.base import (
    DocumentAIFindingItem,
    DocumentAnalysisResult,
    DocumentAnalysisRunStatus,
    DocumentDetectorOutput,
)
from backend.app.ai.document.models.context import DocumentAnalysisContext
from backend.app.ai.document.postprocessing.findings import normalize_detector_output
from backend.app.ai.document.registry import DocumentDetectorRegistry
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import EvidenceClassification

logger = logging.getLogger(__name__)

ENGINE_VERSION = "1.0"


class DocumentAnalysisEngine:
    """Run configured document AI detectors and aggregate normalized findings."""

    def __init__(
        self,
        registry: DocumentDetectorRegistry,
        device_manager: DeviceManager,
        settings: DocumentAISettings | None = None,
    ) -> None:
        self.registry = registry
        self.device_manager = device_manager
        self.settings = settings or DocumentAISettings()

    async def analyze(self, context: DocumentAnalysisContext) -> DocumentAnalysisResult:
        if context.classification not in {
            EvidenceClassification.DOCUMENT,
            EvidenceClassification.IMAGE,
        }:
            return DocumentAnalysisResult(
                status=DocumentAnalysisRunStatus.FAILED,
                error_code="UNSUPPORTED_EVIDENCE",
                error_message_safe=(
                    "Document AI analysis requires document or page image evidence."
                ),
            )
        started = time.perf_counter()
        device = self.device_manager.select_device(self.settings.default_device)
        findings: list[DocumentAIFindingItem] = []
        artifacts: list[DerivedArtifactPayload] = []
        outputs: list[DocumentDetectorOutput] = []
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
                raise DocumentAnalysisTimeoutError(
                    "ANALYSIS_TIMEOUT",
                    f"Detector '{name}' exceeded the configured timeout.",
                ) from exc
            except Exception as exc:
                raise DocumentDetectorError(
                    "DETECTOR_FAILED",
                    f"Detector '{name}' failed during analysis.",
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
        latency_ms = (time.perf_counter() - started) * 1000.0
        return DocumentAnalysisResult(
            status=DocumentAnalysisRunStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=tuple(artifacts),
            metadata=metadata,
            detector_outputs=tuple(outputs),
            latency_ms=latency_ms,
            device=device,
        )
