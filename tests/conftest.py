"""Shared fixtures for foundation tests."""

from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest_asyncio

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.main import create_app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    """Create an isolated API client with deterministic test settings."""

    settings = Settings(
        debug=True,
        log_config_path=Path("missing-test-logging.json"),
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
