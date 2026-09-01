"""Exceptions for AI image forensic analysis."""


class ImageAnalysisError(Exception):
    """Base error for image AI analysis."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class ImageDetectorError(ImageAnalysisError):
    """Raised when one detector fails during analysis."""


class ImageAnalysisTimeoutError(ImageAnalysisError):
    """Raised when analysis exceeds the configured timeout."""
