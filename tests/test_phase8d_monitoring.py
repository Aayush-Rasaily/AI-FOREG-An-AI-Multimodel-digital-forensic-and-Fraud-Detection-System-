"""Tests for Phase 8D operational monitoring."""

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

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.monitoring.metrics import average, percentile_95, rate
from backend.app.monitoring.models import PlatformHealthStatus
from backend.app.monitoring.policy import ENGINE_VERSION, POLICY_VERSION
from tests.test_phase3_api import create_case
from tests.test_phase4_processing import make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260904_0023_add_monitoring.py"
)


@pytest_asyncio.fixture
async def phase8d_client(
    tmp_path: Path,
) -> AsyncIterator[httpx.AsyncClient]:
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
        transport=transport, base_url="http://test",
    ) as client:
        yield client
    await engine.dispose()


class TestEmptyDatabase:
    @pytest.mark.asyncio
    async def test_empty_dashboard_and_health(
        self, phase8d_client: httpx.AsyncClient,
    ) -> None:
        response = await phase8d_client.get("/api/v1/monitoring/dashboard")
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["system_health"]["status"] in {
            item.value for item in PlatformHealthStatus
        }
        assert data["processing"]["jobs_created"] == 0
        assert data["ai"]["model_executions"] == 0
        assert data["cases"]["cases_created"] == 0
        assert data["engine_version"] == ENGINE_VERSION
        assert data["policy_version"] == POLICY_VERSION

        health = await phase8d_client.get("/api/v1/monitoring/system-health")
        assert health.status_code == 200
        assert health.json()["data"]["status"] == "HEALTHY"


class TestAggregationAndRefresh:
    @pytest.mark.asyncio
    async def test_metrics_refresh_and_sections(
        self, phase8d_client: httpx.AsyncClient,
    ) -> None:
        case = await create_case(phase8d_client)
        await process_and_extract(
            phase8d_client,
            case["id"],
            "monitor.pdf",
            make_text_pdf(),
            "application/pdf",
        )

        dashboard = await phase8d_client.get("/api/v1/monitoring/dashboard")
        assert dashboard.status_code == 200
        body = dashboard.json()["data"]
        assert body["cases"]["cases_created"] >= 1
        assert body["cases"]["evidence_uploaded"] >= 1
        assert body["processing"]["jobs_created"] >= 1
        assert "kpis" in body
        assert "bottlenecks" in body

        refresh = await phase8d_client.post("/api/v1/monitoring/refresh")
        assert refresh.status_code == 201, refresh.text
        snapshot_id = refresh.json()["data"]["snapshot_id"]
        assert snapshot_id

        again = await phase8d_client.get("/api/v1/monitoring/dashboard")
        assert again.json()["data"]["snapshot_id"] == snapshot_id

        for path in (
            "/processing",
            "/ai",
            "/api",
            "/activity",
            "/bottlenecks",
            "/audit-summary",
        ):
            section = await phase8d_client.get(f"/api/v1/monitoring{path}")
            assert section.status_code == 200, path
            assert "data" in section.json()["data"]


class TestKpiHelpers:
    def test_kpi_helpers_deterministic(self) -> None:
        assert average([]) is None
        assert average([10.0, 20.0, 30.0]) == 20.0
        assert percentile_95([1.0, 2.0, 3.0, 4.0, 100.0]) == 100.0
        assert rate(1, 4) == 0.25
        assert rate(0, 0) == 0.0


class TestMigration:
    def test_migration_file_loads(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase8d_migration", MIGRATION_PATH,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260904_0023"
        assert module.down_revision == "20260903_0022"
