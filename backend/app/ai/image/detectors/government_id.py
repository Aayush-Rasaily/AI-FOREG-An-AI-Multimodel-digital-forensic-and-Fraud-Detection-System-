"""Government ID region localization detector plugin."""

from __future__ import annotations

import json
import time
from typing import Any

from backend.app.ai.image.detectors.base import ImageAIDetector
from backend.app.ai.image.models import (
    ImageAIFindingItem,
    ImageAnalysisContext,
    ImageDetectorMetadata,
    ImageDetectorOutput,
    ImageFindingCategory,
)
from backend.app.ai.image.utils import id_document_layout_regions
from backend.app.application.processors.base import DerivedArtifactPayload
from backend.app.domain.processing import ArtifactType, EvidenceClassification
from backend.app.forensics.models import RegionBox, Severity
from backend.app.forensics.utils import region_from_pixels


class GovernmentIDDetector(ImageAIDetector):
    """Localize passport, driver license, national ID, PAN, and Aadhaar regions."""

    name = "government_id"
    model_name = "government_id_layout"
    model_version = "1.0.0"
    framework = "NATIVE"

    SUPPORTED_TYPES = (
        "passport",
        "driver_license",
        "national_id",
        "pan",
        "aadhaar",
    )

    def __init__(self) -> None:
        self._loaded = False
        self._device = "cpu"

    def load(self, *, device: str) -> None:
        self._device = device
        self._loaded = True

    def unload(self) -> None:
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def metadata(self) -> ImageDetectorMetadata:
        return ImageDetectorMetadata(
            name=self.name,
            version="1.0",
            author="AI-FORGE Engineering",
            description="Localizes government ID document regions for validation.",
            supported_tasks=("id_localization", "id_validation"),
            model_name=self.model_name,
            model_version=self.model_version,
            framework=self.framework,
        )

    def supports(self, context: ImageAnalysisContext) -> bool:
        return context.classification == EvidenceClassification.IMAGE

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._loaded,
            "device": self._device,
            "status": "healthy" if self._loaded else "unloaded",
        }

    async def predict(self, context: ImageAnalysisContext) -> ImageDetectorOutput:
        started = time.perf_counter()
        width, height = context.width, context.height
        document_type = _infer_document_type(width, height)
        layout = id_document_layout_regions(width, height, document_type)
        regions: list[RegionBox] = []
        for _label, x, y, box_w, box_h in layout:
            regions.append(
                region_from_pixels(x, y, box_w, box_h, width, height),
            )
        findings = (
            ImageAIFindingItem(
                detector=self.name,
                category=ImageFindingCategory.ID_DOCUMENT,
                severity=Severity.INFO,
                confidence=0.75,
                description=f"Government ID layout localized ({document_type}).",
                explanation=(
                    "Expected document regions were mapped for downstream "
                    "validation. No authenticity verdict is issued at this stage."
                ),
                regions=tuple(regions),
                recommendation=(
                    "Validate localized regions against issuing authority templates."
                ),
                metadata={
                    "document_type": document_type,
                    "region_labels": [label for label, *_ in layout],
                },
                model_name=self.model_name,
                model_version=self.model_version,
                model_framework=self.framework,
            ),
        )
        artifacts = (
            DerivedArtifactPayload(
                artifact_type=ArtifactType.AI_IMAGE_PREDICTION,
                mime_type="application/json",
                content=_encode_layout_json(document_type, layout).encode("utf-8"),
                metadata={"detector": self.name, "document_type": document_type},
            ),
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        return ImageDetectorOutput(
            detector=self.name,
            version="1.0",
            findings=findings,
            artifacts=artifacts,
            metadata={"document_type": document_type, "device": self._device},
            latency_ms=latency_ms,
            model_name=self.model_name,
            model_version=self.model_version,
        )


def _infer_document_type(width: int, height: int) -> str:
    ratio = width / max(height, 1)
    if ratio > 1.35:
        return "passport"
    if ratio > 1.15:
        return "driver_license"
    if ratio < 0.75:
        return "aadhaar"
    if ratio < 0.95:
        return "pan"
    return "national_id"


def _encode_layout_json(
    document_type: str,
    layout: tuple[tuple[str, float, float, float, float], ...],
) -> str:
    return json.dumps(
        {
            "document_type": document_type,
            "regions": [
                {
                    "label": label,
                    "x": x,
                    "y": y,
                    "width": box_w,
                    "height": box_h,
                }
                for label, x, y, box_w, box_h in layout
            ],
        }
    )
