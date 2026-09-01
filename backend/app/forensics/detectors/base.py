"""Forensic detector plugin contract."""

from typing import Protocol

from backend.app.forensics.models import AnalysisContext, DetectorResult


class ForensicDetector(Protocol):
    """Replaceable deterministic detector for one evidence category."""

    @property
    def name(self) -> str:
        """Stable detector identifier."""
        ...

    @property
    def version(self) -> str:
        """Detector version for repeatability."""
        ...

    def can_analyze(self, context: AnalysisContext) -> bool:
        """Return whether this detector supports the current context."""
        ...

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        """Execute deterministic analysis and return findings."""
        ...
