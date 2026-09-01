"""Safe forensic analysis failures."""

from backend.app.core.exceptions import ProcessingError


class ForensicAnalysisError(ProcessingError):
    """Raised when forensic analysis cannot safely complete."""


class DetectorExecutionError(ForensicAnalysisError):
    """Raised when an individual detector fails."""
