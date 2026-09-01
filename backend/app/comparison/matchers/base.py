"""Comparison matcher plugin contract."""

from typing import Protocol

from backend.app.comparison.models import ComparisonContext, MatcherResult


class ComparisonMatcher(Protocol):
    """Replaceable deterministic matcher for reference comparison."""

    @property
    def name(self) -> str:
        """Stable matcher identifier."""
        ...

    @property
    def version(self) -> str:
        """Matcher version for repeatability."""
        ...

    def can_compare(self, context: ComparisonContext) -> bool:
        """Return whether this matcher supports the current context."""
        ...

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        """Execute deterministic comparison and return differences."""
        ...
