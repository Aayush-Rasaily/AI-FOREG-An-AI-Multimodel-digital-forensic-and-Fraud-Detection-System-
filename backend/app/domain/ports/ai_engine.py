"""Stable domain contract for pluggable analysis engines."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class EngineRequest:
    """Transport-neutral input envelope supplied to an analysis engine."""

    analysis_id: str
    payload: object


@dataclass(frozen=True, slots=True)
class EngineResult:
    """Transport-neutral result envelope returned by an analysis engine."""

    engine_name: str
    payload: object


class AIEngine(Protocol):
    """Protocol implemented by future engines without coupling the platform."""

    @property
    def name(self) -> str:
        """Return the stable engine identifier."""
        ...

    async def analyze(self, request: EngineRequest) -> EngineResult:
        """Analyze one request according to the engine's capabilities."""
        ...
