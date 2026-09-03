"""Tests for Phase 8B collaboration."""

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
from backend.app.auth.service import AuthService
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260902_0021_add_collaboration.py"
)

JWT_SECRET = "phase8b-test-secret-key-value-32b+"


@pytest_asyncio.fixture
async def collab_client(
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
        transport=transport, base_url="http://test",
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
        json={
            "username": username,
            "password": password,
            "remember_me": False,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


async def auth_headers(client: httpx.AsyncClient) -> dict[str, str]:
    tokens = await login(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def create_case(
    client: httpx.AsyncClient, headers: dict[str, str],
) -> str:
    response = await client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": "Collab Case", "description": "Phase 8B"},
    )
    assert response.status_code == 201, response.text
    return str(response.json()["data"]["id"])


class TestMembers:
    @pytest.mark.asyncio
    async def test_member_lifecycle(
        self,
        collab_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = collab_client
        headers = await auth_headers(client)
        case_id = await create_case(client, headers)
        created = await client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "username": "analyst2",
                "password": "AnalystPassw0rd!",
                "display_name": "Analyst Two",
                "role_names": ["Analyst"],
            },
        )
        assert created.status_code == 201
        user_id = created.json()["data"]["id"]
        member = await client.post(
            f"/api/v1/cases/{case_id}/members",
            headers=headers,
            json={"user_id": user_id, "role": "analyst"},
        )
        assert member.status_code == 201
        listed = await client.get(
            f"/api/v1/cases/{case_id}/members", headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 1


class TestTasksCommentsWorkflow:
    @pytest.mark.asyncio
    async def test_task_comment_workflow(
        self,
        collab_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = collab_client
        headers = await auth_headers(client)
        case_id = await create_case(client, headers)

        task = await client.post(
            f"/api/v1/cases/{case_id}/tasks",
            headers=headers,
            json={"title": "Review packet", "priority": "high"},
        )
        assert task.status_code == 201
        task_id = task.json()["data"]["id"]
        completed = await client.patch(
            f"/api/v1/tasks/{task_id}",
            headers=headers,
            json={"status": "completed"},
        )
        assert completed.status_code == 200
        assert completed.json()["data"]["status"] == "completed"

        comment = await client.post(
            "/api/v1/comments",
            headers=headers,
            json={
                "case_id": case_id,
                "resource_type": "case",
                "resource_id": case_id,
                "body": "Looks good @admin",
            },
        )
        assert comment.status_code == 201
        comments = await client.get(
            f"/api/v1/comments/case/{case_id}", headers=headers,
        )
        assert comments.status_code == 200
        assert comments.json()["data"]["total"] >= 1

        workflow = await client.get(
            f"/api/v1/cases/{case_id}/workflow", headers=headers,
        )
        assert workflow.status_code == 200
        assert workflow.json()["data"]["stage"] == "open"
        advanced = await client.patch(
            f"/api/v1/cases/{case_id}/workflow",
            headers=headers,
            json={"stage": "evidence_collection"},
        )
        assert advanced.status_code == 200
        assert advanced.json()["data"]["stage"] == "evidence_collection"
        bad = await client.patch(
            f"/api/v1/cases/{case_id}/workflow",
            headers=headers,
            json={"stage": "archived"},
        )
        assert bad.status_code == 400


class TestReviewsNotificationsActivity:
    @pytest.mark.asyncio
    async def test_review_and_notifications(
        self,
        collab_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = collab_client
        headers = await auth_headers(client)
        case_id = await create_case(client, headers)
        review = await client.post(
            "/api/v1/reviews",
            headers=headers,
            json={
                "case_id": case_id,
                "resource_type": "case_closure",
                "resource_id": case_id,
            },
        )
        assert review.status_code == 201
        review_id = review.json()["data"]["id"]
        decided = await client.patch(
            f"/api/v1/reviews/{review_id}",
            headers=headers,
            json={"decision": "approve", "comments": "Ready"},
        )
        assert decided.status_code == 200
        assert decided.json()["data"]["state"] == "approved"

        activity = await client.get(
            f"/api/v1/cases/{case_id}/activity", headers=headers,
        )
        assert activity.status_code == 200
        assert activity.json()["data"]["total"] >= 1
        actions = [item["action"] for item in activity.json()["data"]["items"]]
        assert "review.completed" in actions

        notifications = await client.get(
            "/api/v1/notifications", headers=headers,
        )
        assert notifications.status_code == 200


class TestAssignmentsThreadsAuth:
    @pytest.mark.asyncio
    async def test_assignment_thread_mention_and_authz(
        self,
        collab_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession], Settings
        ],
    ) -> None:
        client, _, _ = collab_client
        headers = await auth_headers(client)
        case_id = await create_case(client, headers)

        uploaded = await client.post(
            f"/api/v1/cases/{case_id}/evidence",
            headers=headers,
            files={"file": ("note.pdf", b"%PDF-1.7\n", "application/pdf")},
        )
        assert uploaded.status_code == 201, uploaded.text
        evidence_id = uploaded.json()["data"]["id"]

        viewer = await client.post(
            "/api/v1/users",
            headers=headers,
            json={
                "username": "viewer8b",
                "password": "ViewerPassw0rd!",
                "display_name": "Viewer Eight",
                "role_names": ["Viewer"],
            },
        )
        assert viewer.status_code == 201
        viewer_id = viewer.json()["data"]["id"]

        assigned = await client.post(
            f"/api/v1/evidence/{evidence_id}/assign",
            headers=headers,
            json={
                "assignee_id": viewer_id,
                "priority": "high",
                "notes": "Please triage",
            },
        )
        assert assigned.status_code == 201, assigned.text
        listed = await client.get(
            f"/api/v1/evidence/{evidence_id}/assignments",
            headers=headers,
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 1
        assert listed.json()["data"]["items"][0]["status"] == "pending"

        parent = await client.post(
            "/api/v1/comments",
            headers=headers,
            json={
                "case_id": case_id,
                "resource_type": "evidence",
                "resource_id": evidence_id,
                "body": "Parent note @viewer8b",
            },
        )
        assert parent.status_code == 201
        parent_id = parent.json()["data"]["id"]
        assert viewer_id in [
            str(item) for item in parent.json()["data"]["mentions"]
        ]

        reply = await client.post(
            "/api/v1/comments",
            headers=headers,
            json={
                "case_id": case_id,
                "resource_type": "evidence",
                "resource_id": evidence_id,
                "parent_id": parent_id,
                "body": "Threaded reply",
            },
        )
        assert reply.status_code == 201
        assert reply.json()["data"]["parent_id"] == parent_id

        viewer_login = await login(client, "viewer8b", "ViewerPassw0rd!")
        viewer_headers = {
            "Authorization": f"Bearer {viewer_login['access_token']}",
        }
        forbidden = await client.post(
            f"/api/v1/cases/{case_id}/members",
            headers=viewer_headers,
            json={"user_id": viewer_id, "role": "investigator"},
        )
        assert forbidden.status_code in {401, 403}


class TestMigration:
    def test_migration_file_loads(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase8b_migration", MIGRATION_PATH,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260902_0021"
        assert module.down_revision == "20260902_0020"
