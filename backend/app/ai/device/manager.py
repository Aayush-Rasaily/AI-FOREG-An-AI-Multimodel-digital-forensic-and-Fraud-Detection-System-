"""Execution device discovery and selection."""

from __future__ import annotations

import logging
import platform
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class DeviceType(StrEnum):
    """Supported execution device classes."""

    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"
    ROCM = "rocm"
    TENSORRT = "tensorrt"


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Describes one available execution device."""

    device_type: DeviceType
    name: str
    available: bool
    total_memory_mb: float | None = None
    free_memory_mb: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class DeviceManager:
    """Detect devices and select the best available backend."""

    def __init__(self, *, prefer_gpu: bool = True) -> None:
        self.prefer_gpu = prefer_gpu
        self._cuda_available = self._probe_cuda()
        self._mps_available = self._probe_mps()
        self._rocm_available = self._probe_rocm()
        self._tensorrt_available = self._probe_tensorrt()

    def list_devices(self) -> tuple[DeviceInfo, ...]:
        """Return all known device classes and availability."""

        devices: list[DeviceInfo] = [
            DeviceInfo(
                device_type=DeviceType.CPU,
                name=platform.processor() or "cpu",
                available=True,
            ),
            DeviceInfo(
                device_type=DeviceType.CUDA,
                name="CUDA",
                available=self._cuda_available,
                total_memory_mb=self._cuda_total_memory_mb(),
                free_memory_mb=self._cuda_free_memory_mb(),
            ),
            DeviceInfo(
                device_type=DeviceType.MPS,
                name="Apple MPS",
                available=self._mps_available,
                metadata={"status": "placeholder"},
            ),
            DeviceInfo(
                device_type=DeviceType.ROCM,
                name="ROCm",
                available=self._rocm_available,
                metadata={"status": "placeholder"},
            ),
            DeviceInfo(
                device_type=DeviceType.TENSORRT,
                name="TensorRT",
                available=self._tensorrt_available,
                metadata={"status": "placeholder"},
            ),
        ]
        return tuple(devices)

    def select_device(self, required: str = "any") -> str:
        """Select the best device for inference."""

        normalized = required.lower()
        if normalized in {"cuda", "gpu"} and self._cuda_available:
            return "cuda"
        if normalized == "mps" and self._mps_available:
            return "mps"
        if normalized == "rocm" and self._rocm_available:
            return "rocm"
        if normalized == "cpu":
            return "cpu"
        if self.prefer_gpu and self._cuda_available:
            return "cuda"
        if self.prefer_gpu and self._mps_available:
            return "mps"
        return "cpu"

    def gpu_memory_summary(self) -> dict[str, float | None]:
        """Return GPU memory statistics when CUDA is available."""

        return {
            "total_mb": self._cuda_total_memory_mb(),
            "free_mb": self._cuda_free_memory_mb(),
        }

    @staticmethod
    def _probe_cuda() -> bool:
        try:
            import torch

            return bool(torch.cuda.is_available())
        except ImportError:
            return False

    @staticmethod
    def _probe_mps() -> bool:
        try:
            import torch

            mps_backend = getattr(torch.backends, "mps", None)
            return bool(mps_backend and torch.backends.mps.is_available())
        except (ImportError, AttributeError):
            return False

    @staticmethod
    def _probe_rocm() -> bool:
        return False

    @staticmethod
    def _probe_tensorrt() -> bool:
        return False

    @staticmethod
    def _cuda_total_memory_mb() -> float | None:
        try:
            import torch

            if not torch.cuda.is_available():
                return None
            props = torch.cuda.get_device_properties(0)
            return round(props.total_memory / (1024 * 1024), 2)
        except (ImportError, RuntimeError):
            return None

    @staticmethod
    def _cuda_free_memory_mb() -> float | None:
        try:
            import torch

            if not torch.cuda.is_available():
                return None
            free_bytes, _ = torch.cuda.mem_get_info()
            return round(free_bytes / (1024 * 1024), 2)
        except (ImportError, RuntimeError, AttributeError):
            return None
