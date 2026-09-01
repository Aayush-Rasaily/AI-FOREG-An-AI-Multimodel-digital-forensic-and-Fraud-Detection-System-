"""Postprocessing helpers."""

from backend.app.ai.audio.models import AudioAIFindingItem, AudioDetectorOutput


def normalize_detector_output(
    output: AudioDetectorOutput,
) -> tuple[AudioAIFindingItem, ...]:
    return output.findings
