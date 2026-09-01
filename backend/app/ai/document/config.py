"""Configuration for document AI forensic analysis."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DocumentAISettings:
    """Runtime settings for the document AI forensic engine."""

    engine_version: str = "1.0"
    inference_timeout_seconds: float = 180.0
    max_document_bytes: int = 64 * 1024 * 1024
    default_device: str = "cpu"
    enable_gpu: bool = True
    max_pages: int = 50
    enabled_detectors: tuple[str, ...] = (
        "tampering",
        "text_consistency",
        "font_consistency",
        "layout_consistency",
        "logo",
        "metadata",
        "region_anomaly",
    )
    detector_overrides: dict[str, dict[str, object]] = field(default_factory=dict)
