"""Audit framework domain exceptions."""


class AuditError(Exception):
    """Base exception for audit operations."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
