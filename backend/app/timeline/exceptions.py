"""Timeline engine domain exceptions."""


class TimelineError(Exception):
    """Safe, client-facing timeline failure."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
