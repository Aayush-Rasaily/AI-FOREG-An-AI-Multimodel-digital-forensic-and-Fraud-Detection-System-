"""Bootstrap helpers for document AI forensic analysis."""

from __future__ import annotations

from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.document.config import DocumentAISettings
from backend.app.ai.document.engine import DocumentAnalysisEngine
from backend.app.ai.document.registry import DocumentDetectorRegistry


def build_document_detector_registry(
    settings: DocumentAISettings | None = None,
) -> DocumentDetectorRegistry:
    from backend.app.ai.document.detectors.font_consistency import (
        FontConsistencyDetector,
    )
    from backend.app.ai.document.detectors.layout_consistency import (
        LayoutConsistencyDetector,
    )
    from backend.app.ai.document.detectors.logo import LogoDetector
    from backend.app.ai.document.detectors.metadata import MetadataDetector
    from backend.app.ai.document.detectors.region_anomaly import RegionAnomalyDetector
    from backend.app.ai.document.detectors.tampering import TamperingDetector
    from backend.app.ai.document.detectors.text_consistency import (
        TextConsistencyDetector,
    )

    ai_settings = settings or DocumentAISettings()
    registry = DocumentDetectorRegistry(ai_settings)
    for factory in (
        TamperingDetector,
        TextConsistencyDetector,
        FontConsistencyDetector,
        LayoutConsistencyDetector,
        LogoDetector,
        MetadataDetector,
        RegionAnomalyDetector,
    ):
        registry.register(factory)
    return registry


def build_document_analysis_stack(
    settings: DocumentAISettings | None = None,
) -> tuple[DocumentDetectorRegistry, DeviceManager, DocumentAnalysisEngine]:
    ai_settings = settings or DocumentAISettings()
    registry = build_document_detector_registry(ai_settings)
    device_manager = DeviceManager(prefer_gpu=ai_settings.enable_gpu)
    engine = DocumentAnalysisEngine(
        registry=registry,
        device_manager=device_manager,
        settings=ai_settings,
    )
    return registry, device_manager, engine
