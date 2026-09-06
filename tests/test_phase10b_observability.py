"""Tests for Phase 10B observability instrumentation."""

from __future__ import annotations

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
from backend.app.monitoring.logging import extract_ids_from_path
from backend.app.monitoring.metrics import duration_ms, observe_domain_duration
from backend.app.monitoring.prometheus import (
    normalize_path,
    render_prometheus_metrics,
)


@pytest_asyncio.fixture
async def phase10b_client(
    tmp_path: Path,
) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(
        debug=True,
        app_env="local",
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        temp_storage_path=tmp_path / "data" / "tmp",
        ai_model_root=tmp_path / "models",
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
        yield client
    await engine.dispose()


class TestPrometheus:
    def test_render_contains_core_series(self) -> None:
        observe_domain_duration("ocr", 0.01)
        payload, content_type = render_prometheus_metrics()
        text = payload.decode("utf-8")
        assert "text/plain" in content_type or "openmetrics" in content_type
        assert "ai_forge_http_requests_total" in text or "ai_forge_" in text
        assert "ai_forge_ocr_duration_seconds" in text

    def test_normalize_path_collapses_ids(self) -> None:
        path = normalize_path(
            "/api/v1/cases/11111111-1111-1111-1111-111111111111/evidence"
        )
        assert "{id}" in path

    def test_kpi_helpers_unchanged(self) -> None:
        assert duration_ms(None, None) is None


class TestLoggingHelpers:
    def test_extract_ids(self) -> None:
        found = extract_ids_from_path("/api/v1/cases/abc-case/evidence/ev-1")
        assert found["case_id"] == "abc-case"
        assert found["evidence_id"] == "ev-1"


class TestEndpoints:
    @pytest.mark.asyncio
    async def test_metrics_endpoints(
        self,
        phase10b_client: httpx.AsyncClient,
    ) -> None:
        root = await phase10b_client.get("/metrics")
        assert root.status_code == 200
        assert "ai_forge_" in root.text

        versioned = await phase10b_client.get("/api/v1/metrics")
        assert versioned.status_code == 200
        assert "ai_forge_" in versioned.text

    @pytest.mark.asyncio
    async def test_health_live_and_ready(
        self,
        phase10b_client: httpx.AsyncClient,
    ) -> None:
        live = await phase10b_client.get("/api/v1/health/live")
        assert live.status_code == 200
        assert live.json()["data"]["status"] == "ok"

        ready = await phase10b_client.get("/api/v1/health/ready")
        assert ready.status_code == 200
        body = ready.json()["data"]
        assert body["status"] in {"ready", "not_ready"}
        assert "checks" in body
        assert isinstance(body["checks"], list)

    @pytest.mark.asyncio
    async def test_existing_health_unchanged(
        self,
        phase10b_client: httpx.AsyncClient,
    ) -> None:
        health = await phase10b_client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["data"]["status"] in {"healthy", "degraded"}


class TestArtifacts:
    def test_monitoring_stack_files_exist(self) -> None:
        root = Path(__file__).resolve().parents[1]
        required = [
            root / "docs" / "monitoring.md",
            root / "deployment" / "compose" / "docker-compose.monitoring.yml",
            root / "deployment" / "compose" / "prometheus.yml",
            root / "deployment" / "compose" / "loki-config.yml",
            root / "deployment" / "compose" / "promtail-config.yml",
            root / "deployment" / "monitoring" / "grafana" / "dashboards" / "api.json",
            root / "deployment" / "monitoring" / "grafana" / "dashboards" / "ai.json",
            root
            / "deployment"
            / "monitoring"
            / "grafana"
            / "dashboards"
            / "processing.json",
            root
            / "deployment"
            / "monitoring"
            / "grafana"
            / "dashboards"
            / "database.json",
            root
            / "deployment"
            / "monitoring"
            / "grafana"
            / "dashboards"
            / "system.json",
            root / "backend" / "app" / "monitoring" / "prometheus.py",
            root / "backend" / "app" / "monitoring" / "tracing.py",
            root / "backend" / "app" / "monitoring" / "health.py",
            root / "backend" / "app" / "monitoring" / "logging.py",
            root / "backend" / "app" / "monitoring" / "telemetry.py",
        ]
        missing = [str(path) for path in required if not path.is_file()]
        assert missing == []
