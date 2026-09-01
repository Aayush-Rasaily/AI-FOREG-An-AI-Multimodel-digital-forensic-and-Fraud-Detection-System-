"""Plugin registry and orchestration for deterministic forensic detectors."""

import json
import logging
from typing import Any

from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType
from backend.app.forensics.detectors.document.consistency import ConsistencyDetector
from backend.app.forensics.detectors.document.fonts import FontsDetector
from backend.app.forensics.detectors.document.layout import LayoutDetector
from backend.app.forensics.detectors.document.metadata import DocumentMetadataDetector
from backend.app.forensics.detectors.document.overlays import OverlaysDetector
from backend.app.forensics.detectors.image.copy_move import CopyMoveDetector
from backend.app.forensics.detectors.image.edges import EdgeConsistencyDetector
from backend.app.forensics.detectors.image.ela import ElaDetector
from backend.app.forensics.detectors.image.jpeg import JpegQuantizationDetector
from backend.app.forensics.detectors.image.metadata import ImageMetadataDetector
from backend.app.forensics.detectors.image.noise import NoiseDetector
from backend.app.forensics.detectors.image.resampling import ResamplingDetector
from backend.app.forensics.exceptions import DetectorExecutionError
from backend.app.forensics.models import (
    AnalysisContext,
    AnalysisResult,
    AnalysisRunStatus,
    DetectorResult,
    FindingItem,
)

logger = logging.getLogger(__name__)
ENGINE_VERSION = "1.0"


class ForensicAnalysisEngine:
    """Run all compatible detector plugins without switch-based dispatch."""

    def __init__(self, detectors: tuple[Any, ...] | None = None) -> None:
        self.detectors = detectors or default_detectors()

    async def analyze(self, context: AnalysisContext) -> AnalysisResult:
        """Execute every compatible detector and aggregate findings."""

        findings: list[FindingItem] = []
        artifacts: list[DerivedArtifactPayload] = []
        detector_metadata: dict[str, Any] = {}
        for detector in self.detectors:
            if not detector.can_analyze(context):
                continue
            try:
                result = await detector.analyze(context)
            except Exception as exc:
                logger.exception(
                    "Detector failed",
                    extra={
                        "detector": detector.name,
                        "evidence_id": str(context.evidence_id),
                    },
                )
                raise DetectorExecutionError(
                    "DETECTOR_FAILED",
                    f"Detector {detector.name} failed during analysis.",
                ) from exc
            findings.extend(result.findings)
            artifacts.extend(result.artifacts)
            artifacts.append(_json_artifact(detector.name, result))
            detector_metadata[detector.name] = {
                "version": result.version,
                **result.metadata,
            }
        return AnalysisResult(
            status=AnalysisRunStatus.SUCCEEDED,
            findings=tuple(findings),
            artifacts=tuple(artifacts),
            metadata={"detectors": detector_metadata, "engine_version": ENGINE_VERSION},
        )


def default_detectors() -> tuple[Any, ...]:
    """Return the built-in deterministic detector plugins."""

    return (
        ElaDetector(),
        JpegQuantizationDetector(),
        ImageMetadataDetector(),
        NoiseDetector(),
        EdgeConsistencyDetector(),
        ResamplingDetector(),
        CopyMoveDetector(),
        DocumentMetadataDetector(),
        LayoutDetector(),
        FontsDetector(),
        OverlaysDetector(),
        ConsistencyDetector(),
    )


def _json_artifact(
    detector_name: str, result: DetectorResult
) -> DerivedArtifactPayload:
    payload = {
        "detector": detector_name,
        "version": result.version,
        "findings_count": len(result.findings),
        "metadata": result.metadata,
    }
    return DerivedArtifactPayload(
        artifact_type=ArtifactType.DETECTOR_OUTPUT,
        mime_type="application/json",
        content=json.dumps(payload, sort_keys=True).encode("utf-8"),
        metadata={"detector": detector_name},
    )
