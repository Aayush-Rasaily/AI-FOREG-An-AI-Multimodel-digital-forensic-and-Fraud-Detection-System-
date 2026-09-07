"""Tests for Phase 10D enterprise security hardening."""

from __future__ import annotations

import io
import zipfile
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
from backend.app.application.services.file_validation import FileValidationService
from backend.app.core.config import Settings
from backend.app.core.exceptions import InvalidFileError, UnsupportedFileError
from backend.app.core.logging import JsonFormatter
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.security.csp import api_content_security_policy
from backend.app.security.dependency_scan import run_dependency_security_scan
from backend.app.security.headers import build_security_headers
from backend.app.security.ratelimit import (
    RateLimitRule,
    allow_request,
    classify_request,
)
from backend.app.security.secrets import redact_secrets, validate_runtime_secrets
from backend.app.security.uploads import (
    normalize_upload_filename,
    scan_archive_for_traversal,
)
from backend.app.security.validation import clamp_pagination, reject_path_traversal

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest_asyncio.fixture
async def phase10d_client(
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
        rate_limit_enabled=True,
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


class TestHeadersAndCsp:
    def test_build_security_headers_includes_enterprise_set(self) -> None:
        headers = build_security_headers(enable_hsts=True)
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert "Permissions-Policy" in headers
        assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
        assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
        assert headers["Cross-Origin-Embedder-Policy"] == "require-corp"
        assert "Strict-Transport-Security" in headers
        assert "default-src" in api_content_security_policy()

    @pytest.mark.asyncio
    async def test_api_responses_include_security_headers(
        self,
        phase10d_client: httpx.AsyncClient,
    ) -> None:
        response = await phase10d_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.headers.get("x-content-type-options") == "nosniff"
        assert response.headers.get("x-frame-options") == "DENY"
        assert "content-security-policy" in response.headers
        assert "permissions-policy" in response.headers


class TestRateLimit:
    def test_classify_auth_and_upload(self) -> None:
        assert classify_request("POST", "/api/v1/auth/login") == "auth"
        assert classify_request("POST", "/api/v1/cases/1/evidence") == "upload"
        assert classify_request("GET", "/api/v1/health") is None

    @pytest.mark.asyncio
    async def test_memory_rate_limit_blocks_burst(self) -> None:
        rule = RateLimitRule(
            burst_limit=2,
            burst_window_seconds=60,
            sustained_limit=10,
            sustained_window_seconds=3600,
        )
        assert await allow_request(
            category="search",
            ip="203.0.113.10",
            user_key=None,
            rule=rule,
            use_redis=False,
        )
        assert await allow_request(
            category="search",
            ip="203.0.113.10",
            user_key=None,
            rule=rule,
            use_redis=False,
        )
        assert not await allow_request(
            category="search",
            ip="203.0.113.10",
            user_key=None,
            rule=rule,
            use_redis=False,
        )


class TestUploadsAndValidation:
    def test_rejects_dangerous_filenames(self) -> None:
        with pytest.raises(InvalidFileError):
            normalize_upload_filename("../etc/passwd")
        with pytest.raises(UnsupportedFileError):
            normalize_upload_filename("invoice.pdf.exe")
        with pytest.raises(InvalidFileError):
            normalize_upload_filename("bad\x00name.png")
        assert normalize_upload_filename("photo.PNG") == "photo.PNG"

    def test_archive_traversal_rejected(self) -> None:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../evil.txt", "x")
        with pytest.raises(InvalidFileError):
            scan_archive_for_traversal(buffer.getvalue())

    def test_file_validation_uses_hardening(self) -> None:
        service = FileValidationService(Settings())
        with pytest.raises(InvalidFileError):
            service.validate_metadata("../x.png", "image/png")

    def test_path_and_pagination_helpers(self) -> None:
        with pytest.raises(ValueError):
            reject_path_traversal("../../secret")
        assert clamp_pagination(limit=999, offset=-3) == (100, 0)


class TestSecretsAndLogging:
    def test_redact_secrets(self) -> None:
        text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aaa.bbb"
        redacted = redact_secrets(text)
        assert "Bearer eyJ" not in redacted
        assert "[REDACTED]" in redacted

    def test_json_formatter_redacts_message(self) -> None:
        formatter = JsonFormatter()
        record = logging_record("password=super-secret-value")
        line = formatter.format(record)
        assert "super-secret-value" not in line
        assert "[REDACTED]" in line

    def test_validate_runtime_secrets_local(self) -> None:
        findings = validate_runtime_secrets(Settings(app_env="local"))
        assert findings
        assert all("check" in item for item in findings)


class TestDependencyScan:
    def test_scan_writes_report(self, tmp_path: Path) -> None:
        reports = tmp_path / "reports" / "security"
        result = run_dependency_security_scan(
            repo_root=REPO_ROOT,
            reports_dir=reports,
        )
        assert result["manifests"]["requirements.txt"] is True
        assert (reports / "dependency-scan-latest.json").is_file()
        assert result["status"] in {"PASSED", "FAILED"}


class TestArtifacts:
    def test_docs_and_script_exist(self) -> None:
        assert (REPO_ROOT / "docs" / "security-hardening.md").is_file()
        assert (REPO_ROOT / "scripts" / "security_scan.sh").is_file()
        assert (REPO_ROOT / "reports" / "security" / ".gitkeep").is_file()


def logging_record(message: str):
    import logging

    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg=message,
        args=(),
        exc_info=None,
    )
    return record
