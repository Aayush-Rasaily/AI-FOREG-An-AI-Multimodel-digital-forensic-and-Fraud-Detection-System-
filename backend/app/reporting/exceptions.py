"""Reporting domain exceptions."""


class ReportingError(Exception):
    """Base reporting error with a safe client message."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
