"""PyTorch provider initialization interface."""

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


class PyTorchProvider:
    """Initialize and expose PyTorch availability without performing inference."""

    NAME = "pytorch"

    def initialize(self) -> ProviderStatus:
        try:
            import torch

            return ProviderStatus(
                name=self.NAME,
                available=True,
                version=torch.__version__,
                message="PyTorch runtime detected.",
            )
        except ImportError:
            return ProviderStatus(
                name=self.NAME,
                available=False,
                version=None,
                message="PyTorch is not installed.",
            )

    def runtime_info(self) -> dict[str, Any]:
        status = self.initialize()
        return {
            "name": status.name,
            "available": status.available,
            "version": status.version,
            "message": status.message,
        }
