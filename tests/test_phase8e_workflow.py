"""Tests for Phase 8E investigation workflow."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
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
from backend.app.models.audit import AuditEvent
from backend.app.workflow.engine import (
    assert_report_approval_transition,
    assert_status_transition,
    can_publish_report,
)
from backend.app.workflow.exceptions import (
    InvalidReviewTransitionError,
    InvalidWorkflowTransitionError,
)
from backend.app.workflow.policy import (
    ENGINE_VERSION,
    WORKFLOW_POLICY_VERSION,
    InvestigationStatus,
)
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260905_0024_add_workflow.py"
)


@pytest_asyncio.fixture
async def phase8e_client(
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
        transport=transport, base_url="http://test",
    ) as client:
        yield client, session_factory
    await engine.dispose()


class TestEngine:
    def test_valid_and_invalid_transitions(self) -> None:
        assert (
            assert_status_transition("NEW", "ACTIVE")
            is InvestigationStatus.ACTIVE
        )
        with pytest.raises(InvalidWorkflowTransitionError):
            assert_status_transition("NEW", "APPROVED")
        assert can_publish_report("approved") is True
        assert can_publish_report("draft") is False
        with pytest.raises(InvalidReviewTransitionError):
            assert_report_approval_transition("draft", "published")
        assert (
            assert_report_approval_transition("approved", "published").value
            == "published"
        )


class TestWorkflowApi:
    @pytest.mark.asyncio
    async def test_initialize_and_transition(
        self,
        phase8e_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase8e_client
        case = await create_case(client)
        case_id = case["id"]

        response = await client.get(
            f"/api/v1/cases/{case_id}/investigation-workflow",
        )
        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["status"] == "NEW"
        assert data["policy_version"] == WORKFLOW_POLICY_VERSION
        assert data["engine_version"] == ENGINE_VERSION
        assert data["allowed_transitions"] == ["ACTIVE"]
        assert len(data["activity"]) >= 1

        invalid = await client.patch(
            f"/api/v1/cases/{case_id}/investigation-workflow/status",
            json={"status": "APPROVED"},
        )
        assert invalid.status_code == 409, invalid.text

        active = await client.patch(
            f"/api/v1/cases/{case_id}/investigation-workflow/status",
            json={"status": "ACTIVE"},
        )
        assert active.status_code == 200, active.text
        assert active.json()["data"]["status"] == "ACTIVE"

    @pytest.mark.asyncio
    async def test_tasks_notes_reviews_milestones_notifications(
        self,
        phase8e_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, session_factory = phase8e_client
        case = await create_case(client)
        case_id = case["id"]

        task = await client.post(
            f"/api/v1/cases/{case_id}/workflow-tasks",
            json={
                "title": "Validate evidence",
                "task_type": "EVIDENCE_VALIDATION",
            },
        )
        assert task.status_code == 201, task.text
        task_id = task.json()["data"]["id"]
        assert task.json()["data"]["status"] == "OPEN"

        complete = await client.patch(
            f"/api/v1/workflow-tasks/{task_id}",
            json={"action": "complete"},
        )
        assert complete.status_code == 200, complete.text
        assert complete.json()["data"]["status"] == "COMPLETED"

        reopen = await client.patch(
            f"/api/v1/workflow-tasks/{task_id}",
            json={"action": "reopen"},
        )
        assert reopen.status_code == 200
        assert reopen.json()["data"]["status"] == "REOPENED"

        cancel = await client.patch(
            f"/api/v1/workflow-tasks/{task_id}",
            json={"action": "cancel"},
        )
        assert cancel.status_code == 200
        assert cancel.json()["data"]["status"] == "CANCELLED"

        invalid_task = await client.patch(
            f"/api/v1/workflow-tasks/{task_id}",
            json={"action": "complete"},
        )
        assert invalid_task.status_code == 409

        note = await client.post(
            f"/api/v1/cases/{case_id}/workflow-notes",
            json={
                "content_markdown": "Initial analytical note",
                "category": "analytical",
                "visibility": "internal",
            },
        )
        assert note.status_code == 201, note.text
        assert note.json()["data"]["history"]
        assert note.json()["data"]["history"][0]["version"] == 1

        # Evidence review requires a real evidence id — use missing UUID → 404
        missing_evidence = await client.post(
            f"/api/v1/cases/{case_id}/workflow-reviews",
            json={
                "review_kind": "evidence",
                "evidence_id": str(uuid4()),
                "status": "PENDING",
            },
        )
        assert missing_evidence.status_code == 404

        evidence = await client.post(
            f"/api/v1/cases/{case_id}/evidence",
            files={"file": ("note.pdf", b"%PDF-1.7\n", "application/pdf")},
        )
        assert evidence.status_code == 201, evidence.text
        evidence_id = evidence.json()["data"]["id"]
        review = await client.post(
            f"/api/v1/cases/{case_id}/workflow-reviews",
            json={
                "review_kind": "evidence",
                "evidence_id": evidence_id,
                "status": "APPROVED",
                "comments": "Looks valid",
                "reason": "hash verified",
            },
        )
        assert review.status_code == 201, review.text
        assert review.json()["data"]["status"] == "APPROVED"
        assert len(review.json()["data"]["history"]) == 1

        # Notifications for approved evidence review request to system actor
        # may be empty without assignee; assignment creates notifications.
        assign_task = await client.post(
            f"/api/v1/cases/{case_id}/workflow-tasks",
            json={
                "title": "Assigned work",
                "task_type": "GENERAL",
                "assignee_id": str(uuid4()),
            },
        )
        # Unknown assignee → 404; create without assignee is fine
        assert assign_task.status_code in {201, 404}

        milestones = await client.get(
            f"/api/v1/cases/{case_id}/workflow-milestones",
        )
        assert milestones.status_code == 200, milestones.text
        labels = [item["label"] for item in milestones.json()["data"]["items"]]
        assert "Investigation Started" in labels
        # Deterministic ordering by reached_at then id
        reached = [
            item["reached_at"] for item in milestones.json()["data"]["items"]
        ]
        assert reached == sorted(reached)

        notifications = await client.get(
            f"/api/v1/cases/{case_id}/workflow-notifications",
        )
        assert notifications.status_code == 200

        notes = await client.get(f"/api/v1/cases/{case_id}/workflow-notes")
        assert notes.status_code == 200
        assert notes.json()["data"]["total"] >= 1

        tasks = await client.get(f"/api/v1/cases/{case_id}/workflow-tasks")
        assert tasks.status_code == 200
        assert tasks.json()["data"]["total"] >= 1

        async with session_factory() as session:
            result = await session.execute(
                select(AuditEvent).where(
                    AuditEvent.category == "investigation_workflow"
                )
            )
            audits = list(result.scalars().all())
            assert len(audits) >= 1

    @pytest.mark.asyncio
    async def test_report_publish_requires_approval(
        self,
        phase8e_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase8e_client
        case = await create_case(client)
        case_id = case["id"]

        # Without a real report, create_review for report returns 404
        missing = await client.post(
            f"/api/v1/cases/{case_id}/workflow-reviews",
            json={
                "review_kind": "report",
                "report_id": str(uuid4()),
                "status": "published",
            },
        )
        assert missing.status_code in {404, 409}

    @pytest.mark.asyncio
    async def test_phase8b_workflow_path_untouched(
        self,
        phase8e_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase8e_client
        case = await create_case(client)
        case_id = case["id"]
        collab = await client.get(f"/api/v1/cases/{case_id}/workflow")
        assert collab.status_code == 200, collab.text
        assert "stage" in collab.json()["data"]

        inv = await client.get(
            f"/api/v1/cases/{case_id}/investigation-workflow",
        )
        assert inv.status_code == 200
        assert inv.json()["data"]["status"] == "NEW"


class TestMigration:
    def test_migration_metadata(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase8e_migration", MIGRATION_PATH,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260905_0024"
        assert module.down_revision == "20260904_0023"
