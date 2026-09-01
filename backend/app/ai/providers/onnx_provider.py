"""ONNX Runtime provider initialization interface."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderStatus:
    """Runtime status for one framework provider."""

    name: str
    available: bool
    version: str | None
    message: str


class ONNXProvider:
    """Initialize and expose ONNX Runtime availability without inference."""

    NAME = "onnx"

    def initialize(self) -> ProviderStatus:
        try:
            import onnxruntime as ort

            return ProviderStatus(
                name=self.NAME,
                available=True,
                version=getattr(ort, "__version__", None),
                message="ONNX Runtime detected.",
            )
        except ImportError:
            return ProviderStatus(
                name=self.NAME,
                available=False,
                version=None,
                message="ONNX Runtime is not installed.",
            )

    def runtime_info(self) -> dict[str, Any]:
        status = self.initialize()
        return {
            "name": status.name,
            "available": status.available,
            "version": status.version,
            "message": status.message,
        }
