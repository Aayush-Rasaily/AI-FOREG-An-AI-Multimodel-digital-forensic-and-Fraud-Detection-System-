"""Model metadata contracts for the AI registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class InputType(StrEnum):
    """Supported model input categories."""

    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    TEXT = "TEXT"
    TENSOR = "TENSOR"
    ANY = "ANY"


class OutputType(StrEnum):
    """Supported model output categories."""

    CLASSIFICATION = "CLASSIFICATION"
    EMBEDDING = "EMBEDDING"
    DETECTION = "DETECTION"
    SEGMENTATION = "SEGMENTATION"
    GENERATION = "GENERATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    ANY = "ANY"


class ModelFramework(StrEnum):
    """Execution framework identifier."""

    PYTORCH = "PYTORCH"
    ONNX = "ONNX"
    TENSORFLOW = "TENSORFLOW"
    NATIVE = "NATIVE"


class DeviceRequirement(StrEnum):
    """Minimum device class required by a model."""

    CPU = "CPU"
    CUDA = "CUDA"
    MPS = "MPS"
    ROCM = "ROCM"
    ANY = "ANY"


@dataclass(frozen=True, slots=True)
class ModelMetadata:
    """Describes one registered AI model."""

    name: str
    version: str
    author: str
    framework: ModelFramework
    license: str
    input_type: InputType
    output_type: OutputType
    model_hash: str
    supported_tasks: tuple[str, ...]
    required_device: DeviceRequirement
    training_dataset: str | None = None
    description: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize metadata for API responses."""

        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "framework": self.framework.value,
            "license": self.license,
            "input_type": self.input_type.value,
            "output_type": self.output_type.value,
            "model_hash": self.model_hash,
            "training_dataset": self.training_dataset,
            "supported_tasks": list(self.supported_tasks),
            "required_device": self.required_device.value,
            "description": self.description,
            "tags": list(self.tags),
            "extra": self.extra,
        }
