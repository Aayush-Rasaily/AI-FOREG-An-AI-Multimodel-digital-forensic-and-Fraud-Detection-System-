"""Normalized AI output structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class NormalizedOutputItem:
    """One structured output item from an AI model."""

    name: str
    value: str | float | int | bool
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class NormalizedInferenceOutput:
    """Standard AI-FORGE inference response envelope."""

    model_name: str
    model_version: str
    framework: str
    task: str
    items: tuple[NormalizedOutputItem, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "framework": self.framework,
            "task": self.task,
            "items": [
                {
                    "name": item.name,
                    "value": item.value,
                    "confidence": item.confidence,
                    "metadata": item.metadata,
                }
                for item in self.items
            ],
            "metadata": self.metadata,
        }
