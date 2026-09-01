"""Safe comparison failures."""

from backend.app.core.exceptions import ProcessingError


class ComparisonError(ProcessingError):
    """Raised when reference comparison cannot safely complete."""


class MatcherExecutionError(ComparisonError):
    """Raised when an individual matcher fails."""
