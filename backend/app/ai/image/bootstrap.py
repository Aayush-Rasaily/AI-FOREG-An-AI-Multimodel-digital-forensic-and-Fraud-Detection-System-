"""Bootstrap helpers for image AI forensic analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING

from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.image.config import ImageAISettings
from backend.app.ai.image.engine import ImageAnalysisEngine
from backend.app.ai.image.registry import ImageDetectorRegistry

if TYPE_CHECKING:
    pass


def build_image_detector_registry(
    settings: ImageAISettings | None = None,
) -> ImageDetectorRegistry:
    """Create a registry with all built-in image AI detectors."""

    from backend.app.ai.image.detectors.ai_generated import AIGeneratedImageDetector
    from backend.app.ai.image.detectors.deepfake_face import DeepfakeFaceDetector
    from backend.app.ai.image.detectors.fake_logo import FakeLogoDetector
    from backend.app.ai.image.detectors.government_id import GovernmentIDDetector
    from backend.app.ai.image.detectors.manipulation import ManipulationDetector

    ai_settings = settings or ImageAISettings()
    registry = ImageDetectorRegistry(ai_settings)
    for factory in (
        AIGeneratedImageDetector,
        DeepfakeFaceDetector,
        ManipulationDetector,
        FakeLogoDetector,
        GovernmentIDDetector,
    ):
        registry.register(factory)
    return registry


def build_image_analysis_stack(
    settings: ImageAISettings | None = None,
) -> tuple[ImageDetectorRegistry, DeviceManager, ImageAnalysisEngine]:
    """Compose the image AI analysis stack."""

    ai_settings = settings or ImageAISettings()
    registry = build_image_detector_registry(ai_settings)
    device_manager = DeviceManager(prefer_gpu=ai_settings.enable_gpu)
    engine = ImageAnalysisEngine(
        registry=registry,
        device_manager=device_manager,
        settings=ai_settings,
    )
    return registry, device_manager, engine
