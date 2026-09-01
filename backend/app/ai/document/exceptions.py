"""Document AI analysis exceptions."""


class DocumentAnalysisError(Exception):
    """Base error for document AI analysis."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class DocumentDetectorError(DocumentAnalysisError):
    """Raised when one document detector fails."""


class DocumentAnalysisTimeoutError(DocumentAnalysisError):
    """Raised when analysis exceeds the configured timeout."""
