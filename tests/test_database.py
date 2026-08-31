"""Tests for database dependency lifecycle behavior."""

from collections.abc import AsyncIterator
from typing import Any

import pytest

from backend.app.infrastructure.database import session as database_session


class _SessionContext:
    """Minimal async context manager used to isolate the dependency test."""

    def __init__(self, session: object) -> None:
        self.session = session
        self.closed = False

    async def __aenter__(self) -> object:
        return self.session

    async def __aexit__(
        self,
        _exc_type: Any,
        _exc_value: Any,
        _traceback: Any,
    ) -> None:
        self.closed = True


class _SessionFactory:
    """Callable fake matching the sessionmaker interface."""

    def __init__(self, session: object) -> None:
        self.context = _SessionContext(session)

    def __call__(self) -> _SessionContext:
        return self.context


@pytest.mark.asyncio
async def test_database_dependency_yields_and_closes_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Request-scoped sessions are closed when dependency scope ends."""

    expected_session = object()
    factory = _SessionFactory(expected_session)
    monkeypatch.setattr(database_session, "get_session_factory", lambda: factory)

    dependency: AsyncIterator[object] = database_session.get_db_session()
    assert await anext(dependency) is expected_session

    with pytest.raises(StopAsyncIteration):
        await anext(dependency)
    assert factory.context.closed is True
