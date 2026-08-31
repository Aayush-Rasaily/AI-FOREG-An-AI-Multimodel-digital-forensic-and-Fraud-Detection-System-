"""Request correlation context shared by HTTP handlers and log records."""

from contextvars import ContextVar
from uuid import UUID

_request_id: ContextVar[UUID | None] = ContextVar("request_id", default=None)


def set_request_id(request_id: UUID) -> None:
    """Set the correlation identifier for the current execution context."""

    _request_id.set(request_id)


def get_request_id() -> UUID | None:
    """Return the current request correlation identifier, if present."""

    return _request_id.get()


def clear_request_id() -> None:
    """Clear request correlation state after a request completes."""

    _request_id.set(None)
