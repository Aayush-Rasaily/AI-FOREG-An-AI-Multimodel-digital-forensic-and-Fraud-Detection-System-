"""Inference request contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class InferenceRequest:
    """Validated inference request envelope."""

    model_name: str
    task: str
    payload: dict[str, Any]
    batch_size: int = 1
    device: str | None = None
    request_id: UUID = field(default_factory=uuid4)

    def validate(self) -> None:
        if not self.model_name.strip():
            raise ValueError("model_name is required.")
        if not self.task.strip():
            raise ValueError("task is required.")
        if self.batch_size < 1:
            raise ValueError("batch_size must be at least 1.")
