"""Production validation, benchmarks, security, and DR for AI-Forge v1.0."""

from __future__ import annotations

import time
import tracemalloc
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.ai.models.dummy import DummyModel
from backend.app.api.dependencies import get_db_session
from backend.app.auth.permissions import required_permission
from backend.app.auth.service import AuthService
from backend.app.cicd.gates import (
    parse_semver,
    read_project_version,
    validate_alembic_heads,
    validate_openapi_schema,
)
from backend.app.core.config import Settings
from backend.app.deployment.release import EXPECTED_MIGRATION_HEAD
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.models.case import Case
from backend.app.recovery.backup import create_backup_bundle
from backend.app.recovery.restore import plan_restore, validate_restore_bundle
from backend.app.recovery.verification import verify_backup_bundle
from backend.app.reporting.builder import build_report_content
from backend.app.security.headers import build_security_headers
from backend.app.security.secrets import redact_secrets, validate_runtime_secrets
from backend.app.security.uploads import normalize_upload_filename
from backend.app.security.validation import reject_path_traversal
from tests.test_phase8a_authentication import JWT_SECRET, login

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_VERSION = "1.0.0"


@pytest_asyncio.fixture
async def validation_client(
    tmp_path: Path,
) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(
        debug=True,
        app_env="test",
        app_version=RELEASE_VERSION,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        temp_storage_path=tmp_path / "data" / "tmp",
        ai_model_root=tmp_path / "models",
        log_config_path=tmp_path / "missing-logging.json",
        rate_limit_enabled=False,
        rate_limit_use_redis=False,
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

    async def database_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application = create_app(settings)
    application.dependency_overrides[get_db_session] = database_session
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    application.dependency_overrides.clear()
    await engine.dispose()


class TestReleaseMetadata:
    def test_semver_files_agree(self) -> None:
        parsed = parse_semver(RELEASE_VERSION)
        assert parsed["major"] == "1"
        assert parsed["minor"] == "0"
        assert parsed["patch"] == "0"
        assert read_project_version(REPO_ROOT) == RELEASE_VERSION
        assert (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip() == (
            RELEASE_VERSION
        )
        assert RELEASE_VERSION in (REPO_ROOT / "CHANGELOG.md").read_text(
            encoding="utf-8"
        )
        notes = (REPO_ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        assert "1.0.0" in notes
        assert EXPECTED_MIGRATION_HEAD in notes

    def test_alembic_and_openapi(self) -> None:
        alembic = validate_alembic_heads(repo_root=REPO_ROOT)
        assert alembic["status"] == "PASSED"
        tmp = Path("data")
        settings = Settings(
            debug=True,
            app_env="test",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp / "unused-release-val",
            temp_storage_path=tmp / "unused-release-val" / "tmp",
            ai_model_root=tmp / "unused-models",
            log_config_path=tmp / "missing-logging.json",
            rate_limit_enabled=False,
        )
        app = create_app(settings)
        result = validate_openapi_schema(app.openapi())
        assert result["status"] == "PASSED"
        assert result["path_count"] >= 200

    def test_release_artifacts_exist(self) -> None:
        assert (REPO_ROOT / "docs" / "release-checklist.md").is_file()
        assert (REPO_ROOT / "docs" / "benchmark-summary.md").is_file()
        assert (REPO_ROOT / "docs" / "security-validation.md").is_file()
        assert (REPO_ROOT / "docs" / "disaster-recovery-validation.md").is_file()
        assert (REPO_ROOT / "deployment" / "docker" / "backend.Dockerfile").is_file()
        assert (REPO_ROOT / "deployment" / "docker" / "frontend.Dockerfile").is_file()
        assert (REPO_ROOT / ".github" / "workflows" / "ci.yml").is_file()


class TestAuthenticationAndAuthorization:
    @pytest.mark.asyncio
    async def test_jwt_login_and_permission_map(
        self,
        tmp_path: Path,
    ) -> None:
        settings = Settings(
            debug=True,
            app_env="test",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "data",
            log_config_path=tmp_path / "missing-logging.json",
            jwt_secret=SecretStr(JWT_SECRET),
            auth_bootstrap_username="admin",
            auth_bootstrap_password=SecretStr("AdminPassw0rd!"),
            rate_limit_enabled=False,
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
        async with session_factory() as session:
            await AuthService(session, settings).ensure_seeded()
        app = create_app(settings)

        async def database_session() -> AsyncIterator[AsyncSession]:
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db_session] = database_session
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            denied = await client.get("/api/v1/cases")
            assert denied.status_code == 401
            live = await client.get("/api/v1/health/live")
            assert live.status_code == 200
            tokens = await login(client)
            authed = await client.get(
                "/api/v1/cases",
                headers={"Authorization": f"Bearer {tokens['access_token']}"},
            )
            assert authed.status_code == 200
        await engine.dispose()

        assert required_permission("POST", "/cases") == "case.create"
        assert required_permission("POST", "/auth/login") is None


class TestSecurityValidation:
    def test_headers_tls_uploads_secrets(self) -> None:
        tls = (REPO_ROOT / "deployment" / "nginx" / "nginx-tls.conf.example").read_text(
            encoding="utf-8"
        )
        assert "ssl_protocols       TLSv1.2 TLSv1.3" in tls
        assert "Strict-Transport-Security" in tls

        headers = build_security_headers(enable_hsts=True)
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert "max-age=" in headers["Strict-Transport-Security"]

        production = Settings(
            app_env="production",
            jwt_secret=SecretStr("a" * 32),
            database_url="postgresql+psycopg://user:x@db:5432/ai_forge",
            redis_url="redis://redis:6379/0",
            debug=False,
        )
        findings = validate_runtime_secrets(production)
        assert all(item["status"] != "FAIL" for item in findings)

        assert normalize_upload_filename("invoice.PDF") == "invoice.PDF"
        with pytest.raises(ValueError):
            reject_path_traversal("../etc/passwd")
        assert "[REDACTED]" in redact_secrets("password=super-secret-value")


class TestDisasterRecoveryValidation:
    def test_backup_verify_restore_rollback_simulation(
        self,
        tmp_path: Path,
    ) -> None:
        storage = tmp_path / "data"
        (storage / "reports").mkdir(parents=True)
        (storage / "exports").mkdir(parents=True)
        (storage / "reports" / "sample.txt").write_text("ok", encoding="utf-8")
        settings = Settings(
            app_env="local",
            storage_root=storage,
            temp_storage_path=storage / "tmp",
            ai_model_root=tmp_path / "models",
        )
        manifest = create_backup_bundle(settings, stamp="V1VAL20260907T000000Z")
        bundle = Path(manifest["bundle_dir"])
        verified = verify_backup_bundle(bundle)
        assert verified["valid"] is True
        validation = validate_restore_bundle(bundle, settings)
        assert validation["restore_allowed"] is True
        plan = plan_restore(bundle)
        assert plan["destructive"] is True
        assert any("maintenance" in step.lower() for step in plan["steps"])

        tampered = bundle / "configuration.json"
        tampered.write_text('{"tampered": true}', encoding="utf-8")
        blocked = validate_restore_bundle(bundle, settings)
        assert blocked["restore_allowed"] is False
        assert blocked["status"] == "FAILED"


class TestPerformanceValidation:
    def test_startup_ai_report_and_memory_bounds(self, tmp_path: Path) -> None:
        settings = Settings(
            debug=True,
            app_env="test",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "data",
            temp_storage_path=tmp_path / "data" / "tmp",
            ai_model_root=tmp_path / "models",
            log_config_path=tmp_path / "missing-logging.json",
            rate_limit_enabled=False,
        )
        started = time.perf_counter()
        create_app(settings)
        startup_s = time.perf_counter() - started
        assert startup_s < 20.0

        model = DummyModel()
        model.load(device="cpu")
        cpu_before = time.process_time()
        tracemalloc.start()
        import asyncio

        result = asyncio.run(model.predict({"probe": True}))
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cpu_s = time.process_time() - cpu_before
        assert result["infrastructure_check"] == "passed"
        assert cpu_s < 2.0
        assert peak < 50 * 1024 * 1024

        report_started = time.perf_counter()
        content = build_report_content(
            report_id=str(uuid4()),
            generated_at="2026-09-07T00:00:00+00:00",
            snapshot={
                "case": {
                    "case_id": str(uuid4()),
                    "case_number": "CASE-BENCH",
                    "title": "Benchmark",
                    "status": "OPEN",
                },
                "evidence": [],
                "evidence_hashes": [],
                "analysis_summaries": [],
                "fusion_snapshots": [],
                "case_intelligence": None,
            },
        )
        report_s = time.perf_counter() - report_started
        assert content
        assert report_s < 5.0

    @pytest.mark.asyncio
    async def test_api_latency_and_database_throughput(
        self,
        validation_client: httpx.AsyncClient,
    ) -> None:
        started = time.perf_counter()
        response = await validation_client.get("/api/v1/health/live")
        latency_s = time.perf_counter() - started
        assert response.status_code == 200
        assert latency_s < 2.0

        engine = create_async_engine(
            "sqlite+aiosqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        session_factory = async_sessionmaker(bind=engine, class_=AsyncSession)
        bulk_started = time.perf_counter()
        async with session_factory() as session:
            for index in range(50):
                session.add(
                    Case(
                        title=f"Throughput {index}",
                        case_number=f"CASE-{index:06d}",
                    )
                )
            await session.commit()
        bulk_s = time.perf_counter() - bulk_started
        await engine.dispose()
        assert bulk_s < 5.0
