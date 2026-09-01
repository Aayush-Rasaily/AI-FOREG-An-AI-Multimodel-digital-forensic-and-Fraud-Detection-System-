"""Bootstrap helpers for audio AI forensic analysis."""

from __future__ import annotations

from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.engine import AudioAnalysisEngine
from backend.app.ai.audio.registry import AudioDetectorRegistry
from backend.app.ai.device.manager import DeviceManager


def build_audio_detector_registry(
    settings: AudioAISettings | None = None,
) -> AudioDetectorRegistry:
    from backend.app.ai.audio.detectors.compression import CompressionDetector
    from backend.app.ai.audio.detectors.deepfake_voice import DeepfakeVoiceDetector
    from backend.app.ai.audio.detectors.metadata import MetadataDetector
    from backend.app.ai.audio.detectors.noise_consistency import (
        NoiseConsistencyDetector,
    )
    from backend.app.ai.audio.detectors.silence import SilenceDetector
    from backend.app.ai.audio.detectors.speaker_consistency import (
        SpeakerConsistencyDetector,
    )
    from backend.app.ai.audio.detectors.spectral import SpectralDetector
    from backend.app.ai.audio.detectors.splicing import SplicingDetector
    from backend.app.ai.audio.detectors.synthetic_audio import SyntheticAudioDetector
    from backend.app.ai.audio.detectors.voice_clone import VoiceCloneDetector
    from backend.app.ai.audio.detectors.waveform import WaveformDetector

    ai_settings = settings or AudioAISettings()
    registry = AudioDetectorRegistry(ai_settings)
    for factory in (
        lambda: SyntheticAudioDetector(ai_settings),
        lambda: VoiceCloneDetector(ai_settings),
        lambda: DeepfakeVoiceDetector(ai_settings),
        lambda: SpeakerConsistencyDetector(ai_settings),
        lambda: SplicingDetector(ai_settings),
        lambda: WaveformDetector(ai_settings),
        lambda: SpectralDetector(ai_settings),
        CompressionDetector,
        lambda: NoiseConsistencyDetector(ai_settings),
        lambda: SilenceDetector(ai_settings),
        MetadataDetector,
    ):
        registry.register(factory)
    return registry


def build_audio_analysis_stack(
    settings: AudioAISettings | None = None,
) -> tuple[AudioDetectorRegistry, DeviceManager, AudioAnalysisEngine]:
    ai_settings = settings or AudioAISettings()
    registry = build_audio_detector_registry(ai_settings)
    device_manager = DeviceManager(prefer_gpu=ai_settings.enable_gpu)
    engine = AudioAnalysisEngine(
        registry=registry,
        device_manager=device_manager,
        settings=ai_settings,
    )
    return registry, device_manager, engine
