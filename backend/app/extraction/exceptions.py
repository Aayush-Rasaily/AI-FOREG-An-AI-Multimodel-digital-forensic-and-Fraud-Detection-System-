"""Safe extraction-specific failures."""

from backend.app.core.exceptions import ProcessingError


class ExtractionError(ProcessingError):
    """Raised when an extractor cannot safely complete."""


class ExtractionCapabilityUnavailableError(ExtractionError):
    """Raised when an optional parser or executable is unavailable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message)
