"""Fusion analysis exceptions."""


class FusionAnalysisError(Exception):
    """Base error for multimodal fusion."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
