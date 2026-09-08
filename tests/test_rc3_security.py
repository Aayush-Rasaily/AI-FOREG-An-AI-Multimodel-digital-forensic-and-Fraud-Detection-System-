"""RC3 production security validation (no forensic or API redesign)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from pydantic import SecretStr, ValidationError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.api.schemas.case import CaseCreateRequest
from backend.app.auth.schemas import LoginRequest
from backend.app.auth.service import AuthService
from backend.app.core.config import Settings
from backend.app.core.exceptions import InvalidFileError, UnsupportedFileError
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.security.uploads import normalize_upload_filename
from tests.test_phase8a_authentication import JWT_SECRET, login

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest_asyncio.fixture
async def rc3_client(
    tmp_path: Path,
) -> AsyncIterator[httpx.AsyncClient]:
    settings = Settings(
        debug=False,
        app_env="local",
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        temp_storage_path=tmp_path / "data" / "tmp",
        ai_model_root=tmp_path / "models",
        log_config_path=tmp_path / "missing-logging.json",
        jwt_secret=SecretStr(JWT_SECRET),
        auth_bootstrap_username="admin",
        auth_bootstrap_password=SecretStr("AdminPassw0rd!"),
        cors_origins=[],
        rate_limit_enabled=False,
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
    async with session_factory() as session:
        await AuthService(session, settings).ensure_seeded()

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


class TestOpenApiAndCors:
    def test_openapi_disabled_when_debug_false(self, tmp_path: Path) -> None:
        settings = Settings(
            debug=False,
            app_env="local",
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "data",
            temp_storage_path=tmp_path / "data" / "tmp",
            ai_model_root=tmp_path / "models",
            log_config_path=tmp_path / "missing-logging.json",
        )
        app = create_app(settings)
        assert app.docs_url is None
        assert app.redoc_url is None
        assert app.openapi_url is None

    @pytest.mark.asyncio
    async def test_docs_and_openapi_are_not_served(
        self,
        rc3_client: httpx.AsyncClient,
    ) -> None:
        docs = await rc3_client.get("/docs")
        openapi = await rc3_client.get("/openapi.json")
        assert docs.status_code == 404
        assert openapi.status_code == 404

    @pytest.mark.asyncio
    async def test_cors_does_not_reflect_unlisted_origins(
        self,
        rc3_client: httpx.AsyncClient,
    ) -> None:
        response = await rc3_client.options(
            "/api/v1/cases",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert "access-control-allow-origin" not in {
            key.lower() for key in response.headers
        }


class TestAuthorizationConsistency:
    @pytest.mark.asyncio
    async def test_unauthenticated_is_401_not_403(
        self,
        rc3_client: httpx.AsyncClient,
    ) -> None:
        response = await rc3_client.get("/api/v1/cases")
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "UNAUTHENTICATED"
        assert "traceback" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_viewer_cannot_create_cases(
        self,
        rc3_client: httpx.AsyncClient,
    ) -> None:
        admin = await login(rc3_client)
        created = await rc3_client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin['access_token']}"},
            json={
                "username": "viewer_rc3",
                "password": "ViewerPassw0rd!",
                "display_name": "Viewer RC3",
                "role_names": ["Viewer"],
            },
        )
        assert created.status_code == 201
        viewer = await login(rc3_client, "viewer_rc3", "ViewerPassw0rd!")
        forbidden = await rc3_client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {viewer['access_token']}"},
            json={"title": "Should not create"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_missing_case_is_404(
        self,
        rc3_client: httpx.AsyncClient,
    ) -> None:
        tokens = await login(rc3_client)
        missing = await rc3_client.get(
            "/api/v1/cases/00000000-0000-0000-0000-000000000404",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert missing.status_code == 404


class TestInputAndUploads:
    def test_login_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            LoginRequest.model_validate(
                {
                    "username": "admin",
                    "password": "x",
                    "is_admin": True,
                }
            )

    def test_case_create_rejects_unknown_fields(self) -> None:
        with pytest.raises(ValidationError):
            CaseCreateRequest.model_validate(
                {"title": "Case", "owner_id": "00000000-0000-0000-0000-000000000001"}
            )

    def test_upload_filename_hardening(self) -> None:
        with pytest.raises((InvalidFileError, UnsupportedFileError)):
            normalize_upload_filename("..\\windows\\system32\\cmd.exe")


class TestContainerAndEdge:
    def test_backend_runs_as_non_root(self) -> None:
        dockerfile = (
            REPO_ROOT / "deployment" / "docker" / "backend.Dockerfile"
        ).read_text(encoding="utf-8")
        assert "USER appuser" in dockerfile
        assert "DEBUG=false" in dockerfile
        assert "--forwarded-allow-ips=*" not in dockerfile

    def test_edge_hides_metrics_from_public_proxy(self) -> None:
        for relative in (
            Path("deployment") / "nginx" / "frontend.conf",
            Path("deployment") / "nginx" / "nginx.conf",
            Path("deployment") / "nginx" / "nginx-tls.conf.example",
            Path("frontend") / "nginx.prod.conf",
        ):
            text = (REPO_ROOT / relative).read_text(encoding="utf-8")
            assert "location = /api/v1/metrics" in text
            assert "return 404" in text

    def test_rc3_documentation_exists(self) -> None:
        assert (REPO_ROOT / "docs" / "security-rc3.md").is_file()
        assert (REPO_ROOT / "docs" / "user-guide.md").is_file()
        assert (REPO_ROOT / "docs" / "developer-guide.md").is_file()
        assert (REPO_ROOT / "docs" / "forensic-methodology.md").is_file()
        assert (REPO_ROOT / "docs" / "known-limitations.md").is_file()
