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
from backend.app.core.config import (
    DevelopmentSettings,
    ProductionSettings,
    Settings,
    TestingSettings,
    get_settings,
)
from backend.app.main import create_app
from backend.app.security.ratelimit import _memory_buckets


@pytest.fixture(autouse=True)
def isolate_developer_dotenv(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Keep a developer ``.env`` from enabling auth or live DB hosts in unit tests.

    Native local development uses ``.env`` with ``JWT_SECRET`` and PostgreSQL.
    Settings() would otherwise inherit those and break unauthenticated fixtures.
    Explicit ``monkeypatch.setenv`` / constructor kwargs in individual tests still win.
    """

    for cls in (Settings, DevelopmentSettings, TestingSettings, ProductionSettings):
        monkeypatch.setitem(cls.model_config, "env_file", None)

    for key in (
        "JWT_SECRET",
        "DATABASE_URL",
        "DATABASE_READ_URL",
        "REDIS_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
        "CORS_ORIGINS",
        "JOB_QUEUE_MODE",
        "RATE_LIMIT_USE_REDIS",
        "APP_ENV",
        "ENVIRONMENT",
    ):
        monkeypatch.delenv(key, raising=False)

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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
        jwt_secret=None,
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
