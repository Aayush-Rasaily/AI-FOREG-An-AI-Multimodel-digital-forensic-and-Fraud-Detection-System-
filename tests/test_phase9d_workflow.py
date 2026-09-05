"""Tests for Phase 9D decision support / investigator workflow engine."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID

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
from backend.app.decision_support.planner import plan_workflow
from backend.app.decision_support.policy import DS_ENGINE_VERSION, DS_POLICY_VERSION
from backend.app.decision_support.review_queue import build_review_queue
from backend.app.decision_support.scoring import (
    priority_from_score,
    task_priority_score,
)
from backend.app.decision_support.service import DecisionSupportService
from backend.app.decision_support.task_generator import generate_tasks
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260910_0029_add_decision_support.py"
)


@pytest_asyncio.fixture
async def phase9d_client(
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


class TestMigration:
    def test_migration_file_and_chain(self) -> None:
        assert MIGRATION_PATH.is_file()
        spec = importlib.util.spec_from_file_location("ds_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260910_0029"
        assert module.down_revision == "20260909_0028"


class TestScoringAndTasks:
    def test_priority_thresholds(self) -> None:
        assert priority_from_score(0.9).value == "HIGH"
        assert priority_from_score(0.5).value == "MEDIUM"
        assert priority_from_score(0.1).value == "LOW"

    def test_task_priority_boost(self) -> None:
        base = task_priority_score("REVIEW_AI_CONFLICT", support_count=1)
        boosted = task_priority_score(
            "REVIEW_AI_CONFLICT", support_count=4, severity_boost=0.1,
        )
        assert boosted >= base

    def test_empty_case_generates_acquire_task(self) -> None:
        tasks = generate_tasks({"evidence": [], "recommendations": [], "gaps": []})
        assert any(
            item.task_type.value == "ACQUIRE_ORIGINAL_EVIDENCE" for item in tasks
        )

    def test_gap_maps_to_custody_task(self) -> None:
        tasks = generate_tasks(
            {
                "evidence": [{"id": "e1"}],
                "gaps": [
                    {
                        "gap_key": "g1",
                        "gap_type": "MISSING_CHAIN_OF_CUSTODY",
                        "severity": "HIGH",
                        "reason": "No custody",
                        "affected_evidence_ids": ["e1"],
                    }
                ],
                "recommendations": [],
            }
        )
        assert any(
            item.task_type.value == "COMPLETE_CHAIN_OF_CUSTODY" for item in tasks
        )

    def test_recommendation_maps_to_task(self) -> None:
        tasks = generate_tasks(
            {
                "evidence": [{"id": "e1"}],
                "gaps": [],
                "recommendations": [
                    {
                        "recommendation_key": "r1",
                        "code": "VERIFY_DIGITAL_SIGNATURE",
                        "action_text": "Verify signature",
                        "priority": "HIGH",
                        "affected_evidence_ids": ["e1"],
                    }
                ],
            }
        )
        assert any(
            item.task_type.value == "RUN_SIGNATURE_VERIFICATION" for item in tasks
        )

    def test_review_queue_ordering_deterministic(self) -> None:
        snapshot = {
            "evidence": [
                {"id": "e2", "has_metadata": False},
                {"id": "e1", "has_metadata": False},
            ],
            "custody_by_evidence": {"e1": 0, "e2": 0},
            "gaps": [],
            "open_conflicts": [],
            "fusion_runs": [],
            "correlations": [],
        }
        first = build_review_queue(snapshot)
        second = build_review_queue(snapshot)
        assert [item.queue_key for item in first] == [
            item.queue_key for item in second
        ]
        assert first[0].priority_score >= first[-1].priority_score

    def test_plan_metrics(self) -> None:
        plan = plan_workflow(
            {
                "evidence": [{"id": "e1", "has_metadata": False}],
                "gaps": [
                    {
                        "gap_key": "g1",
                        "gap_type": "MISSING_METADATA",
                        "severity": "MEDIUM",
                        "reason": "meta",
                        "affected_evidence_ids": ["e1"],
                    }
                ],
                "recommendations": [],
                "coverage": {
                    "evidence_total": 1,
                    "overall_completeness": 0.2,
                },
                "custody_by_evidence": {"e1": 0},
                "open_conflicts": [],
                "fusion_runs": [],
                "correlations": [],
                "reports": [],
                "source_kinds": ["evidence"],
            }
        )
        assert plan.tasks
        assert plan.metrics.open_tasks >= 1
        assert 0 <= plan.metrics.investigation_progress <= 1

    def test_repeatability(self) -> None:
        snapshot = {
            "evidence": [],
            "gaps": [],
            "recommendations": [],
            "coverage": {"evidence_total": 0, "overall_completeness": 0},
            "source_kinds": [],
        }
        assert [t.task_key for t in plan_workflow(snapshot).tasks] == [
            t.task_key for t in plan_workflow(snapshot).tasks
        ]

    def test_policy_versions(self) -> None:
        assert DS_ENGINE_VERSION.startswith("9d.")
        assert DS_POLICY_VERSION


class TestApiAndService:
    @pytest.mark.asyncio
    async def test_preview_empty_case(
        self,
        phase9d_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9d_client
        case = await create_case(client)
        preview = await client.get(
            f"/api/v1/cases/{case['id']}/decision-support/preview",
        )
        assert preview.status_code == 200, preview.text
        data = preview.json()["data"]
        assert data["persisted"] is False
        assert data["engine_version"] == DS_ENGINE_VERSION
        assert data["task_count"] >= 1

    @pytest.mark.asyncio
    async def test_preview_does_not_persist(
        self,
        phase9d_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9d_client
        case = await create_case(client)
        await client.get(
            f"/api/v1/cases/{case['id']}/decision-support/preview",
        )
        missing = await client.get(
            f"/api/v1/cases/{case['id']}/decision-support",
        )
        assert missing.status_code == 404

    @pytest.mark.asyncio
    async def test_generate_get_tasks_queue_metrics_decision(
        self,
        phase9d_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9d_client
        case = await create_case(client)
        case_id = case["id"]

        built = await client.post(
            f"/api/v1/cases/{case_id}/decision-support",
        )
        assert built.status_code == 200, built.text
        body = built.json()["data"]
        assert body["status"] == "SUCCEEDED"
        run_id = body["id"]
        assert body["tasks"]
        task_id = body["tasks"][0]["id"]

        latest = await client.get(
            f"/api/v1/cases/{case_id}/decision-support/latest",
        )
        assert latest.status_code == 200
        assert latest.json()["data"]["id"] == run_id

        by_id = await client.get(f"/api/v1/decision-support/{run_id}")
        assert by_id.status_code == 200

        tasks = await client.get(
            f"/api/v1/cases/{case_id}/decision-support/tasks",
        )
        assert tasks.status_code == 200
        assert tasks.json()["data"]["total"] >= 1

        queue = await client.get(
            f"/api/v1/cases/{case_id}/decision-support/review-queue",
        )
        assert queue.status_code == 200

        metrics = await client.get(
            f"/api/v1/cases/{case_id}/decision-support/metrics",
        )
        assert metrics.status_code == 200
        assert "open_tasks" in metrics.json()["data"]

        patched = await client.patch(
            f"/api/v1/decision-support/tasks/{task_id}",
            json={"status": "COMPLETED"},
        )
        assert patched.status_code == 200
        assert patched.json()["data"]["status"] == "COMPLETED"

        decision = await client.post(
            "/api/v1/decision-support/decisions",
            json={
                "case_id": case_id,
                "decision_type": "MARKED_REVIEWED",
                "investigator": "alice",
                "justification": "Reviewed workflow task.",
                "task_id": task_id,
            },
        )
        assert decision.status_code == 200, decision.text
        assert decision.json()["data"]["decision_type"] == "MARKED_REVIEWED"

        decisions = await client.get(
            f"/api/v1/cases/{case_id}/decision-support/decisions",
        )
        assert decisions.status_code == 200
        assert decisions.json()["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_repeat_generate_new_runs(
        self,
        phase9d_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9d_client
        case = await create_case(client)
        first = await client.post(
            f"/api/v1/cases/{case['id']}/decision-support",
        )
        second = await client.post(
            f"/api/v1/cases/{case['id']}/decision-support",
        )
        assert first.json()["data"]["id"] != second.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_service_preview(
        self,
        phase9d_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, session_factory = phase9d_client
        case = await create_case(client)
        async with session_factory() as session:
            service = DecisionSupportService(session)
            preview = await service.preview(UUID(case["id"]))
            assert preview.task_count >= 1
            assert preview.persisted is False

    @pytest.mark.asyncio
    async def test_missing_run_404(
        self,
        phase9d_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9d_client
        missing = await client.get(
            "/api/v1/decision-support/"
            "00000000-0000-0000-0000-000000000099",
        )
        assert missing.status_code == 404

    def test_task_provenance_present(self) -> None:
        tasks = generate_tasks(
            {
                "evidence": [{"id": "e1"}],
                "gaps": [
                    {
                        "gap_key": "g1",
                        "gap_type": "MISSING_OCR",
                        "severity": "LOW",
                        "reason": "ocr",
                        "affected_evidence_ids": ["e1"],
                    }
                ],
                "recommendations": [],
            }
        )
        assert tasks
        assert tasks[0].provenance is not None

    def test_invalid_decision_rejected(
        self,
    ) -> None:
        from backend.app.decision_support.decision_log import (
            normalize_decision_type,
        )

        with pytest.raises(ValueError):
            normalize_decision_type("MAKE_LEGAL_FINDING")

    def test_hypothesis_timeline_creates_review_task(self) -> None:
        tasks = generate_tasks(
            {
                "evidence": [{"id": "e1"}],
                "gaps": [],
                "recommendations": [],
                "hypotheses": [
                    {
                        "hypothesis_key": "h1",
                        "hypothesis_type": "TIMELINE_CONFLICT",
                        "explanation": "Clock skew",
                        "supporting_evidence_ids": ["e1"],
                        "provenance": {"timeline_ids": ["t1"]},
                    }
                ],
            }
        )
        assert any(
            item.task_type.value == "REVIEW_TIMELINE_CONFLICT" for item in tasks
        )

    def test_close_investigation_when_complete(self) -> None:
        tasks = generate_tasks(
            {
                "evidence": [{"id": "e1"}, {"id": "e2"}],
                "gaps": [],
                "recommendations": [],
                "coverage": {"overall_completeness": 0.9},
                "open_conflicts": [],
            }
        )
        assert any(
            item.task_type.value == "CLOSE_INVESTIGATION" for item in tasks
        )
