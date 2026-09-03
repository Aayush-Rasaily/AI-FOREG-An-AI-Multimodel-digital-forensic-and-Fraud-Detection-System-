"""Tests for Phase 7F system administration and monitoring."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.system.policy import DIAGNOSTIC_CHECKS, JOB_CATEGORIES
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260901_0019_add_system_monitoring.py"
)


@pytest_asyncio.fixture
async def phase7f_client(
    tmp_path: Path,
) -> AsyncIterator[
    tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ]
]:
    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
    )
    engine = create_async_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    app = create_app(settings)

    async def _override_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client, session_factory, engine, app


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health(
        self,
        phase7f_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7f_client
        resp = await client.get("/api/v1/system/health")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] in ("healthy", "degraded")
        assert "uptime_seconds" in data
        assert "database" in data


class TestMetricsEndpoint:
    @pytest.mark.asyncio
    async def test_metrics(
        self,
        phase7f_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7f_client
        case = await create_case(client)
        case_id = str(case["id"])
        await process_and_extract(
            client,
            case_id,
            "doc.pdf",
            make_text_pdf(),
            "application/pdf",
        )
        resp = await client.get("/api/v1/system/metrics")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["case_count"] >= 1
        assert data["evidence_count"] >= 1


class TestJobsEndpoint:
    @pytest.mark.asyncio
    async def test_jobs(
        self,
        phase7f_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7f_client
        resp = await client.get("/api/v1/system/jobs")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "categories" in data
        assert "totals" in data
        assert data["category_list"] == list(JOB_CATEGORIES)


class TestStorageEndpoint:
    @pytest.mark.asyncio
    async def test_storage(
        self,
        phase7f_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7f_client
        resp = await client.get("/api/v1/system/storage")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["backend"] == "local"
        assert data["root_configured"] is True


class TestDiagnostics:
    @pytest.mark.asyncio
    async def test_get_diagnostics(
        self,
        phase7f_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7f_client
        resp = await client.get("/api/v1/system/diagnostics")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["checks"]) == len(DIAGNOSTIC_CHECKS)

    @pytest.mark.asyncio
    async def test_run_diagnostics(
        self,
        phase7f_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7f_client
        resp = await client.post("/api/v1/system/diagnostics/run")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "id" in data
        assert data["overall_status"] in (
            "healthy", "degraded", "unhealthy",
        )


class TestMigration:
    def test_migration_exists(self) -> None:
        assert MIGRATION_PATH.exists()

    def test_migration_chain(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "m0019", MIGRATION_PATH,
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        assert mod.revision == "20260901_0019"
        assert mod.down_revision == "20260901_0018"
