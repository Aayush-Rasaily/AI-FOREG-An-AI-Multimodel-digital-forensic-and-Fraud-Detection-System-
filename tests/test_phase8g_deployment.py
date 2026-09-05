"""Tests for Phase 8G production readiness, deployment, and release."""

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
from backend.app.deployment.backup import (
    create_configuration_export,
    create_database_backup_metadata,
    create_report_archive_metadata,
    list_backup_metadata,
)
from backend.app.deployment.configuration import (
    configuration_profile,
    verify_configuration,
)
from backend.app.deployment.recovery import (
    validate_restore_readiness,
    verify_disaster_recovery,
)
from backend.app.deployment.release import (
    DEPLOYMENT_ENGINE_VERSION,
    DEPLOYMENT_POLICY_VERSION,
    EXPECTED_MIGRATION_HEAD,
    build_release_metadata,
)
from backend.app.deployment.startup import (
    get_startup_validation,
    is_shutdown_requested,
    mark_shutdown_requested,
    run_startup_validation,
)
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app


@pytest_asyncio.fixture
async def phase8g_client(
    tmp_path: Path,
) -> AsyncIterator[tuple[httpx.AsyncClient, Settings]]:
    settings = Settings(
        debug=True,
        app_env="local",
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
        yield client, settings
    await engine.dispose()


class TestReleaseMetadata:
    def test_build_release_metadata(self) -> None:
        meta = build_release_metadata(
            app_version="0.1.0",
            environment="local",
        )
        assert meta["application_version"] == "0.1.0"
        assert meta["schema_version"] == EXPECTED_MIGRATION_HEAD
        assert meta["migration_version"] == EXPECTED_MIGRATION_HEAD
        assert meta["policy_versions"]["deployment_policy"] == (
            DEPLOYMENT_POLICY_VERSION
        )
        assert meta["policy_versions"]["deployment_engine"] == (
            DEPLOYMENT_ENGINE_VERSION
        )
        assert "build_metadata" in meta


class TestConfigurationAndStartup:
    def test_configuration_profile_and_verify(self, tmp_path: Path) -> None:
        settings = Settings(
            debug=True,
            app_env="local",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "store",
        )
        profile = configuration_profile(settings)
        assert profile["profile"] == "local"
        assert profile["engine_version"] == DEPLOYMENT_ENGINE_VERSION
        findings = verify_configuration(settings)
        assert findings
        assert [item["check"] for item in findings] == sorted(
            item["check"] for item in findings
        )
        assert all(item["status"] == "PASS" for item in findings)

    def test_startup_and_shutdown(self, tmp_path: Path) -> None:
        settings = Settings(
            debug=True,
            app_env="local",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "store",
        )
        result = run_startup_validation(settings)
        assert result["status"] == "PASSED"
        assert get_startup_validation() is not None
        assert result["graceful_shutdown_supported"] is True
        mark_shutdown_requested()
        assert is_shutdown_requested() is True


class TestBackupRecovery:
    def test_backup_metadata_and_dr(self, tmp_path: Path) -> None:
        settings = Settings(
            debug=True,
            app_env="local",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "store",
        )
        create_database_backup_metadata(settings)
        create_report_archive_metadata(settings)
        create_configuration_export(settings)
        records = list_backup_metadata(settings)
        assert len(records) == 3
        kinds = {item["kind"] for item in records}
        assert kinds == {"database", "report_archive", "configuration_export"}
        dr = verify_disaster_recovery(settings)
        assert dr["status"] == "READY"
        restore = validate_restore_readiness(settings)
        assert restore["restore_validated"] is True


class TestSystemReleaseApi:
    @pytest.mark.asyncio
    async def test_version_release_liveness(
        self,
        phase8g_client: tuple[httpx.AsyncClient, Settings],
    ) -> None:
        client, _ = phase8g_client
        version = await client.get("/api/v1/system/version")
        assert version.status_code == 200, version.text
        data = version.json()["data"]
        assert data["engine_version"] == DEPLOYMENT_ENGINE_VERSION
        assert data["policy_version"] == DEPLOYMENT_POLICY_VERSION

        release = await client.get("/api/v1/system/release")
        assert release.status_code == 200, release.text
        body = release.json()["data"]
        assert body["migration_version"] == EXPECTED_MIGRATION_HEAD
        assert EXPECTED_MIGRATION_HEAD == "20260914_0033"
        assert "policy_versions" in body
        assert "ai" in body["ai_engine_versions"]

        live = await client.get("/api/v1/system/liveness")
        assert live.status_code == 200
        assert live.json()["data"]["status"] == "alive"

    @pytest.mark.asyncio
    async def test_readiness_startup_configuration(
        self,
        phase8g_client: tuple[httpx.AsyncClient, Settings],
    ) -> None:
        client, _ = phase8g_client
        ready = await client.get("/api/v1/system/readiness")
        assert ready.status_code == 200, ready.text
        payload = ready.json()["data"]
        assert "ready" in payload
        assert "checks" in payload
        checks = [item["check"] for item in payload["checks"]]
        assert checks == sorted(checks)

        startup = await client.get("/api/v1/system/startup-validation")
        assert startup.status_code == 200
        assert startup.json()["data"]["status"] in {"PASSED", "FAILED"}

        config = await client.get("/api/v1/system/configuration")
        assert config.status_code == 200
        data = config.json()["data"]
        assert "profile" in data
        assert "export" in data
        assert "findings" in data

    @pytest.mark.asyncio
    async def test_validate_and_release_check(
        self,
        phase8g_client: tuple[httpx.AsyncClient, Settings],
    ) -> None:
        client, settings = phase8g_client
        validation = await client.post("/api/v1/system/validate")
        assert validation.status_code == 200, validation.text
        body = validation.json()["data"]
        assert body["status"] in {"PASSED", "DEGRADED", "FAILED"}
        assert body["fail_count"] + body["warn_count"] + body[
            "pass_count"
        ] == len(body["checks"])
        names = [item["check"] for item in body["checks"]]
        assert names == sorted(names)
        assert "database" in names
        assert "storage" in names

        release_check = await client.post("/api/v1/system/release-check")
        assert release_check.status_code == 200, release_check.text
        result = release_check.json()["data"]
        assert result["status"] in {"PASSED", "DEGRADED", "FAILED"}
        assert result["release"]["application_version"]
        assert "validation" in result
        assert "disaster_recovery" in result
        assert "restore" in result
        assert len(result["backup_records"]) >= 3
        assert (settings.storage_root / "deployment" / "backups").exists()
