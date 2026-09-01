"""TensorFlow provider initialization interface."""

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


class TensorFlowProvider:
    """Initialize and expose TensorFlow availability without inference."""

    NAME = "tensorflow"

    def initialize(self) -> ProviderStatus:
        try:
            import tensorflow as tf

            return ProviderStatus(
                name=self.NAME,
                available=True,
                version=tf.__version__,
                message="TensorFlow runtime detected.",
            )
        except ImportError:
            return ProviderStatus(
                name=self.NAME,
                available=False,
                version=None,
                message="TensorFlow is not installed.",
            )

    def runtime_info(self) -> dict[str, Any]:
        status = self.initialize()
        return {
            "name": status.name,
            "available": status.available,
            "version": status.version,
            "message": status.message,
        }
