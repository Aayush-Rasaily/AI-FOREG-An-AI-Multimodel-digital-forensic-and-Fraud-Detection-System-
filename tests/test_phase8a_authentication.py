"""Tests for Phase 8A authentication and RBAC."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path

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

from backend.app.api.dependencies import get_db_session
from backend.app.auth.hashing import hash_password, verify_password
from backend.app.auth.jwt import decode_token, encode_token
from backend.app.auth.permissions import required_permission
from backend.app.auth.service import AuthService
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260902_0020_add_authentication.py"
)

JWT_SECRET = "phase8a-test-secret-key-value-32b+"


@pytest_asyncio.fixture
async def auth_client(
    tmp_path: Path,
) -> AsyncIterator[
    tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings]
]:
    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
        jwt_secret=SecretStr(JWT_SECRET),
        auth_bootstrap_username="admin",
        auth_bootstrap_password=SecretStr("AdminPassw0rd!"),
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

    async def _override_db() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = _override_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client, session_factory, settings
    await engine.dispose()


async def login(
    client: httpx.AsyncClient,
    username: str = "admin",
    password: str = "AdminPassw0rd!",
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password, "remember_me": False},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


class TestPasswordHashing:
    def test_argon2_round_trip(self) -> None:
        digest = hash_password("AdminPassw0rd!")
        assert digest != "AdminPassw0rd!"
        assert verify_password("AdminPassw0rd!", digest)
        assert not verify_password("wrong-password", digest)


class TestJwt:
    def test_encode_and_decode(self) -> None:
        from datetime import timedelta
        from uuid import uuid4

        user_id = uuid4()
        session_id = uuid4()
        token = encode_token(
            secret=JWT_SECRET,
            algorithm="HS256",
            subject=user_id,
            session_id=session_id,
            token_type="access",
            expires_delta=timedelta(minutes=5),
        )
        payload = decode_token(token=token, secret=JWT_SECRET, algorithm="HS256")
        assert payload["sub"] == str(user_id)
        assert payload["sid"] == str(session_id)
        assert payload["typ"] == "access"


class TestPermissionMapping:
    def test_case_create_requires_permission(self) -> None:
        assert required_permission("POST", "/cases") == "case.create"
        assert required_permission("GET", "/audit") == "audit.view"
        assert required_permission("GET", "/system/health") == "system.monitor"


class TestAuthApi:
    @pytest.mark.asyncio
    async def test_login_success(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        data = await login(client)
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["username"] == "admin"
        assert "Administrator" in data["user"]["roles"]

    @pytest.mark.asyncio
    async def test_login_failure(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "WrongPassw0rd!"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_and_logout(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        tokens = await login(client)
        refresh = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh.status_code == 200
        access = refresh.json()["data"]["access_token"]
        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert me.status_code == 200
        logout = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access}"},
            json={"refresh_token": refresh.json()["data"]["refresh_token"]},
        )
        assert logout.status_code == 200
        me_after = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access}"},
        )
        assert me_after.status_code == 401

    @pytest.mark.asyncio
    async def test_protected_endpoint_requires_auth(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        response = await client.get("/api/v1/cases")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_permission_enforcement(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        admin = await login(client)
        created = await client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin['access_token']}"},
            json={
                "username": "viewer1",
                "password": "ViewerPassw0rd!",
                "display_name": "Viewer One",
                "role_names": ["Viewer"],
            },
        )
        assert created.status_code == 201
        viewer = await login(client, "viewer1", "ViewerPassw0rd!")
        forbidden = await client.get(
            "/api/v1/system/health",
            headers={"Authorization": f"Bearer {viewer['access_token']}"},
        )
        assert forbidden.status_code == 403
        allowed = await client.get(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {viewer['access_token']}"},
        )
        assert allowed.status_code == 200

    @pytest.mark.asyncio
    async def test_user_crud_and_role_assignment(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        admin = await login(client)
        headers = {"Authorization": f"Bearer {admin['access_token']}"}
        created = await client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "username": "analyst1",
                "password": "AnalystPassw0rd!",
                "display_name": "Analyst One",
                "role_names": ["Analyst"],
            },
        )
        assert created.status_code == 201
        user_id = created.json()["data"]["id"]
        patched = await client.patch(
            f"/api/v1/users/{user_id}",
            headers=headers,
            json={"role_names": ["Investigator"]},
        )
        assert patched.status_code == 200
        assert patched.json()["data"]["roles"] == ["Investigator"]
        deleted = await client.delete(f"/api/v1/users/{user_id}", headers=headers)
        assert deleted.status_code == 200

    @pytest.mark.asyncio
    async def test_session_revocation(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        tokens = await login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        sessions = await client.get("/api/v1/sessions", headers=headers)
        assert sessions.status_code == 200
        session_id = sessions.json()["data"]["items"][0]["id"]
        revoke = await client.delete(
            f"/api/v1/sessions/{session_id}",
            headers=headers,
        )
        assert revoke.status_code == 200
        me = await client.get("/api/v1/auth/me", headers=headers)
        assert me.status_code == 401

    @pytest.mark.asyncio
    async def test_roles_and_permissions_lists(
        self,
        auth_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = auth_client
        tokens = await login(client)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        roles = await client.get("/api/v1/roles", headers=headers)
        permissions = await client.get("/api/v1/permissions", headers=headers)
        assert roles.status_code == 200
        assert permissions.status_code == 200
        assert any(item["name"] == "Administrator" for item in roles.json()["data"])
        assert any(
            item["code"] == "admin.manage_users"
            for item in permissions.json()["data"]
        )


class TestMigration:
    def test_migration_file_loads(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase8a_migration", MIGRATION_PATH,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260902_0020"
        assert module.down_revision == "20260901_0019"
