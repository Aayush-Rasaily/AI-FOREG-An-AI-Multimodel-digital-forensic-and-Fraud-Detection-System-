"""Bootstrap helpers for video AI forensic analysis."""

from __future__ import annotations

from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.video.config import VideoAISettings
from backend.app.ai.video.engine import VideoAnalysisEngine
from backend.app.ai.video.registry import VideoDetectorRegistry


def build_video_detector_registry(
    settings: VideoAISettings | None = None,
) -> VideoDetectorRegistry:
    from backend.app.ai.video.detectors.compression import CompressionDetector
    from backend.app.ai.video.detectors.deepfake import DeepfakeVideoDetector
    from backend.app.ai.video.detectors.face_consistency import FaceConsistencyDetector
    from backend.app.ai.video.detectors.frame_manipulation import (
        FrameManipulationDetector,
    )
    from backend.app.ai.video.detectors.metadata import MetadataDetector
    from backend.app.ai.video.detectors.synthetic_video import SyntheticVideoDetector
    from backend.app.ai.video.detectors.temporal import TemporalDetector

    ai_settings = settings or VideoAISettings()
    registry = VideoDetectorRegistry(ai_settings)
    for factory in (
        lambda: DeepfakeVideoDetector(ai_settings),
        lambda: SyntheticVideoDetector(ai_settings),
        TemporalDetector,
        FrameManipulationDetector,
        FaceConsistencyDetector,
        CompressionDetector,
        MetadataDetector,
    ):
        registry.register(factory)
    return registry


def build_video_analysis_stack(
    settings: VideoAISettings | None = None,
) -> tuple[VideoDetectorRegistry, DeviceManager, VideoAnalysisEngine]:
    ai_settings = settings or VideoAISettings()
    registry = build_video_detector_registry(ai_settings)
    device_manager = DeviceManager(prefer_gpu=ai_settings.enable_gpu)
    engine = VideoAnalysisEngine(
        registry=registry,
        device_manager=device_manager,
        settings=ai_settings,
    )
    return registry, device_manager, engine
