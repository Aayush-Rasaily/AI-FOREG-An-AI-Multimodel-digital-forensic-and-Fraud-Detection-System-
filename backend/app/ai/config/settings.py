"""AI infrastructure runtime settings."""

from dataclasses import dataclass, field
from enum import StrEnum


class ModelFormat(StrEnum):
    """Supported model artifact formats for future loading."""

    PYTORCH_PT = "pt"
    PYTORCH_PTH = "pth"
    ONNX = "onnx"
    SAFETENSORS = "safetensors"
    TENSORFLOW_SAVEDMODEL = "savedmodel"


@dataclass(frozen=True, slots=True)
class AISettings:
    """Configuration for the AI inference framework."""

    cache_max_models: int = 8
    cache_ttl_seconds: int = 3600
    default_device: str = "cpu"
    enable_gpu: bool = True
    warmup_on_load: bool = True
    default_batch_size: int = 1
    max_batch_size: int = 32
    inference_timeout_seconds: float = 120.0
    supported_formats: tuple[ModelFormat, ...] = field(
        default_factory=lambda: (
            ModelFormat.PYTORCH_PT,
            ModelFormat.PYTORCH_PTH,
            ModelFormat.ONNX,
            ModelFormat.SAFETENSORS,
            ModelFormat.TENSORFLOW_SAVEDMODEL,
        )
    )
