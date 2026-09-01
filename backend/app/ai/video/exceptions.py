"""Video AI analysis exceptions."""


class VideoAnalysisError(Exception):
    """Base error for video AI analysis."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class VideoAnalysisTimeoutError(VideoAnalysisError):
    """Raised when a detector exceeds the configured timeout."""


class VideoDetectorError(VideoAnalysisError):
    """Raised when an individual detector fails."""


class ModelIntegrityError(VideoAnalysisError):
    """Raised when model weight hash verification fails."""
