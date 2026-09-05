"""Tests for Phase 9G investigation analytics."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.analytics.metrics import build_metrics
from backend.app.analytics.policy import (
    AN_ENGINE_VERSION,
    METRIC_KEYS,
)
from backend.app.analytics.service import AnalyticsService
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260913_0032_add_investigation_analytics.py"
)


@pytest_asyncio.fixture
async def phase9g_client(
    tmp_path: Path,
) -> AsyncIterator[tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]]]:
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
        yield client, session_factory
    await engine.dispose()


class TestMigration:
    def test_migration_file_and_chain(self) -> None:
        assert MIGRATION_PATH.is_file()
        spec = importlib.util.spec_from_file_location("an_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260913_0032"
        assert module.down_revision == "20260912_0031"


class TestMetrics:
    def test_build_metrics_deterministic(self) -> None:
        raw = {key: float(i) for i, key in enumerate(METRIC_KEYS)}
        raw.update(
            {
                "ai_breakdown": {},
                "knowledge_graph_runs": 0,
                "integrity_runs": 0,
                "queue_active": 0,
                "queue_total": 0,
                "user_count": 0,
            }
        )
        a = build_metrics(raw)
        b = build_metrics(raw)
        assert [m.key for m in a] == list(METRIC_KEYS)
        assert [m.key for m in a] == [m.key for m in b]
        assert a[0].provenance.get("derived") is True


class TestApiAndService:
    @pytest.mark.asyncio
    async def test_live_get_then_refresh(
        self,
        phase9g_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9g_client
        live = await client.get("/api/v1/analytics")
        assert live.status_code == 200
        body = live.json()["data"]
        assert body["persisted"] is False
        assert body["engine_version"] == AN_ENGINE_VERSION
        assert body["metric_count"] == len(METRIC_KEYS)

        refreshed = await client.post("/api/v1/analytics/refresh")
        assert refreshed.status_code == 200
        run = refreshed.json()["data"]
        assert run["persisted"] is True
        assert run["id"] is not None

        latest = await client.get("/api/v1/analytics")
        assert latest.json()["data"]["id"] == run["id"]

    @pytest.mark.asyncio
    async def test_sections_and_export(
        self,
        phase9g_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9g_client
        await create_case(client)
        await client.post("/api/v1/analytics/refresh")

        dashboard = await client.get("/api/v1/analytics/dashboard")
        assert dashboard.status_code == 200
        assert "sections" in dashboard.json()["data"]

        for path in (
            "cases",
            "evidence",
            "ai",
            "workflow",
            "integrity",
        ):
            resp = await client.get(f"/api/v1/analytics/{path}")
            assert resp.status_code == 200
            assert resp.json()["data"]["section"] == path

        export = await client.get("/api/v1/analytics/export")
        assert export.status_code == 200
        assert export.json()["data"]["format"] == "json"
        assert "metrics" in export.json()["data"]["payload"]

    @pytest.mark.asyncio
    async def test_service_aggregation_with_case(
        self,
        phase9g_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, session_factory = phase9g_client
        await create_case(client)
        async with session_factory() as session:
            service = AnalyticsService(session)
            run = await service.refresh()
            assert run.sections["cases"]["opened"] >= 1
            assert any(m.key == "cases_opened" for m in run.metrics)

    @pytest.mark.asyncio
    async def test_trends_grow_after_second_refresh(
        self,
        phase9g_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9g_client
        first = await client.post("/api/v1/analytics/refresh")
        second = await client.post("/api/v1/analytics/refresh")
        assert first.status_code == 200
        trends = second.json()["data"]["trends"]
        assert "cases_opened" in trends
        assert len(trends["cases_opened"]) >= 2
