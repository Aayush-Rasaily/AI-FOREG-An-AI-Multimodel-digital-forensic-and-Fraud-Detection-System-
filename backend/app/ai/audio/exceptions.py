"""Audio AI analysis exceptions."""


class AudioAnalysisError(Exception):
    """Base error for audio AI analysis."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class AudioAnalysisTimeoutError(AudioAnalysisError):
    """Raised when a detector exceeds the configured timeout."""


class AudioDetectorError(AudioAnalysisError):
    """Raised when an individual detector fails."""


class ModelIntegrityError(AudioAnalysisError):
    """Raised when model weight hash verification fails."""
