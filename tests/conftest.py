"""Shared fixtures for foundation tests."""

from __future__ import annotations

import asyncio
import sys
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.security.ratelimit import _memory_buckets


@pytest.fixture(autouse=True)
def reset_rate_limiter_memory() -> Iterator[None]:
    """Keep in-memory rate-limit buckets isolated across tests."""

    _memory_buckets.clear()
    yield
    _memory_buckets.clear()


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """Create an isolated API client with deterministic test settings."""

    settings = Settings(
        debug=True,
        app_env="local",
        database_url="sqlite+aiosqlite://",
        log_config_path=Path("missing-test-logging.json"),
        rate_limit_enabled=False,
        rate_limit_use_redis=False,
    )
    application = create_app(settings)
    session = AsyncMock()

    async def fake_db_session() -> AsyncIterator[AsyncMock]:
        yield session

    application.dependency_overrides[get_db_session] = fake_db_session
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as test_client:
        yield test_client
    application.dependency_overrides.clear()
