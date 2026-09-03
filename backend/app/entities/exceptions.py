"""Domain exceptions for entity resolution."""


class EntityResolutionError(Exception):
    """Raised when entity resolution fails with a stable error code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
