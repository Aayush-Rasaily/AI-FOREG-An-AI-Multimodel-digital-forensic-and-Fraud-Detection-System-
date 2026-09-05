"""Tests for Phase 9H platform validation."""

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

import backend.app.models  # noqa: F401 — register ORM metadata
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.platform_validation.engine import score_readiness
from backend.app.platform_validation.models import (
    CheckOutcome,
    CheckStatus,
    ReadinessLevel,
)
from backend.app.platform_validation.policy import (
    CHECK_CATALOG,
    PV_ENGINE_VERSION,
    REQUIRED_API_PATHS,
)

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260914_0033_add_platform_validation.py"
)


@pytest_asyncio.fixture
async def phase9h_client(
    tmp_path: Path,
) -> AsyncIterator[tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]]]:
    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
    )
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
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
        spec = importlib.util.spec_from_file_location("pv_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260914_0033"
        assert module.down_revision == "20260913_0032"
        assert EXPECTED_MIGRATION_HEAD == "20260914_0033"


class TestScoring:
    def test_readiness_scoring_deterministic(self) -> None:
        outcomes = [
            CheckOutcome(
                key="a",
                category="x",
                label="A",
                status=CheckStatus.PASS,
                message="ok",
            ),
            CheckOutcome(
                key="b",
                category="x",
                label="B",
                status=CheckStatus.WARN,
                message="warn",
            ),
            CheckOutcome(
                key="c",
                category="x",
                label="C",
                status=CheckStatus.FAIL,
                message="fail",
            ),
        ]
        score_a, level_a = score_readiness(outcomes)
        score_b, level_b = score_readiness(outcomes)
        assert score_a == score_b == 50.0
        assert level_a == level_b == ReadinessLevel.NOT_READY


class TestApiAndService:
    @pytest.mark.asyncio
    async def test_live_latest_then_validate(
        self,
        phase9h_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
        ],
    ) -> None:
        client, _ = phase9h_client
        live = await client.get("/api/v1/platform/validation/latest")
        assert live.status_code == 200
        body = live.json()["data"]
        assert body["persisted"] is False
        assert body["engine_version"] == PV_ENGINE_VERSION
        assert body["check_count"] == len(CHECK_CATALOG)

        validated = await client.post("/api/v1/platform/validate")
        assert validated.status_code == 200
        run = validated.json()["data"]
        assert run["persisted"] is True
        assert run["id"] is not None
        assert run["readiness_level"] in {"READY", "DEGRADED", "NOT_READY"}

        latest = await client.get("/api/v1/platform/validation/latest")
        assert latest.json()["data"]["id"] == run["id"]

        by_id = await client.get(f"/api/v1/platform/validation/{run['id']}")
        assert by_id.status_code == 200
        assert by_id.json()["data"]["id"] == run["id"]

    @pytest.mark.asyncio
    async def test_readiness_health_list_and_openapi(
        self,
        phase9h_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
        ],
    ) -> None:
        client, _ = phase9h_client
        await client.post("/api/v1/platform/validate")

        readiness = await client.get("/api/v1/platform/readiness")
        assert readiness.status_code == 200
        assert readiness.json()["data"]["persisted"] is True

        health = await client.get("/api/v1/platform/health/report")
        assert health.status_code == 200
        report = health.json()["data"]["report"]
        assert report["ai_rerun"] is False
        assert report["data_mutation"] is False
        assert "counts" in report

        listed = await client.get("/api/v1/platform/validation")
        assert listed.status_code == 200
        assert len(listed.json()["data"]["runs"]) >= 1

        openapi = await client.get("/openapi.json")
        assert openapi.status_code == 200
        paths = openapi.json()["paths"]
        for suffix in REQUIRED_API_PATHS:
            assert any(suffix in path for path in paths), suffix

    @pytest.mark.asyncio
    async def test_deterministic_repeat(
        self,
        phase9h_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
        ],
    ) -> None:
        client, _ = phase9h_client
        first = (await client.post("/api/v1/platform/validate")).json()["data"]
        second = (await client.post("/api/v1/platform/validate")).json()["data"]
        assert [r["check_key"] for r in first["results"]] == [
            r["check_key"] for r in second["results"]
        ]
        assert [r["status"] for r in first["results"]] == [
            r["status"] for r in second["results"]
        ]
        assert first["readiness_score"] == second["readiness_score"]

    @pytest.mark.asyncio
    async def test_missing_run_404(
        self,
        phase9h_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
        ],
    ) -> None:
        client, _ = phase9h_client
        response = await client.get(
            "/api/v1/platform/validation/00000000-0000-0000-0000-000000000099"
        )
        assert response.status_code == 404
