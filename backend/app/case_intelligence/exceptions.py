"""Case intelligence exceptions."""


class CaseIntelligenceError(Exception):
    """Base error for case intelligence synthesis."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
