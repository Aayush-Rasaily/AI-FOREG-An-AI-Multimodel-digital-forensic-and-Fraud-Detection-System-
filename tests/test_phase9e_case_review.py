"""Tests for Phase 9E case review & evidence validation framework."""

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
from backend.app.case_review.approvals import (
    approval_completion,
    normalize_approval_decision,
)
from backend.app.case_review.checklist import generate_checklist
from backend.app.case_review.engine import infer_stage, plan_review
from backend.app.case_review.models import ProvenanceBundle, ReviewStage
from backend.app.case_review.policy import (
    CHECKLIST_ITEMS,
    CR_ENGINE_VERSION,
    CR_POLICY_VERSION,
    REQUIRED_APPROVER_ROLES,
)
from backend.app.case_review.provenance import provenance_to_dict
from backend.app.case_review.scoring import compute_metrics
from backend.app.case_review.service import CaseReviewService
from backend.app.case_review.validation import evaluate_signals
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260911_0030_add_case_review.py"
)


def _empty_snapshot() -> dict:
    return {
        "evidence": [],
        "custody_by_evidence": {},
        "hypotheses": [],
        "recommendations": [],
        "timeline_events": [],
        "timeline_conflicts": [],
        "correlations": [],
        "fusion_runs": [],
        "fusion_conflicts": [],
        "ai_findings": [],
        "knowledge_graph_ids": [],
        "reports": [],
        "open_workflow_tasks": 0,
        "workflow_completion": 0.0,
        "workflow_task_ids": [],
        "open_conflicts": [],
        "source_kinds": ["case"],
    }


def _rich_snapshot() -> dict:
    return {
        "evidence": [
            {"id": "e1", "sha256_hash": "abc", "has_metadata": True},
            {"id": "e2", "sha256_hash": "def", "has_metadata": True},
        ],
        "custody_by_evidence": {"e1": 1, "e2": 2},
        "hypotheses": [{"hypothesis_key": "h1"}],
        "recommendations": [{"recommendation_key": "r1"}],
        "timeline_events": [{"id": "t1"}],
        "timeline_conflicts": [],
        "correlations": [{"id": "c1"}],
        "fusion_runs": [{"id": "f1"}],
        "fusion_conflicts": [],
        "ai_findings": [{"id": "a1"}],
        "knowledge_graph_ids": ["kg1"],
        "reports": [{"id": "rep1"}],
        "open_workflow_tasks": 0,
        "workflow_completion": 1.0,
        "workflow_task_ids": ["w1"],
        "open_conflicts": [],
        "source_kinds": ["case", "evidence", "timeline"],
    }


@pytest_asyncio.fixture
async def phase9e_client(
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
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client, session_factory
    await engine.dispose()


class TestMigration:
    def test_migration_file_and_chain(self) -> None:
        assert MIGRATION_PATH.is_file()
        spec = importlib.util.spec_from_file_location("cr_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260911_0030"
        assert module.down_revision == "20260910_0029"


class TestValidationAndChecklist:
    def test_empty_review_signals(self) -> None:
        signals = evaluate_signals(_empty_snapshot())
        assert signals["evidence_total"] == 0
        assert signals["evidence_with_hash"] == 0

    def test_checklist_generation_empty(self) -> None:
        items = generate_checklist(_empty_snapshot())
        assert len(items) == len(CHECKLIST_ITEMS)
        integrity = next(i for i in items if i.item_code == "EVIDENCE_INTEGRITY")
        assert integrity.blocking is True
        assert integrity.status.value == "PENDING"

    def test_checklist_generation_rich(self) -> None:
        items = generate_checklist(_rich_snapshot())
        assert all(i.status.value == "PENDING" for i in items)
        sha = next(i for i in items if i.item_code == "SHA256_VERIFIED")
        assert sha.suggested_status.value == "PASS"

    def test_deterministic_ordering(self) -> None:
        a = [i.item_code for i in generate_checklist(_rich_snapshot())]
        b = [i.item_code for i in generate_checklist(_rich_snapshot())]
        assert a == b
        assert a == [code for code, _ in CHECKLIST_ITEMS]

    def test_repeatability_item_keys(self) -> None:
        a = [i.item_key for i in generate_checklist(_rich_snapshot())]
        b = [i.item_key for i in generate_checklist(_rich_snapshot())]
        assert a == b

    def test_validation_scoring(self) -> None:
        checklist = generate_checklist(_rich_snapshot())
        metrics = compute_metrics(
            checklist,
            evidence_total=2,
            evidence_with_hash=2,
            approvals_done=0,
            approvals_required=4,
        )
        assert metrics.evidence_coverage_pct == 1.0
        assert metrics.approval_completion_pct == 0.0
        assert metrics.outstanding_issues >= 0

    def test_blocking_and_outstanding(self) -> None:
        plan = plan_review(_empty_snapshot())
        assert plan.metrics.blocking_issues >= 1
        assert len(plan.blocking) >= 1
        assert plan.stage in {
            ReviewStage.UNDER_REVIEW,
            ReviewStage.PENDING,
        }

    def test_rich_plan_stage(self) -> None:
        plan = plan_review(_rich_snapshot())
        assert plan.required_approver_roles == list(REQUIRED_APPROVER_ROLES)
        assert plan.provenance["engine_version"] == CR_ENGINE_VERSION


class TestApprovals:
    def test_normalize_decision(self) -> None:
        assert normalize_approval_decision("approved") == "APPROVED"
        with pytest.raises(ValueError):
            normalize_approval_decision("maybe")

    def test_approval_completion_multiple_reviewers(self) -> None:
        roles = list(REQUIRED_APPROVER_ROLES)
        assert approval_completion(set(), roles) == 0.0
        assert approval_completion({roles[0]}, roles) == 0.25
        assert approval_completion(set(roles), roles) == 1.0

    def test_infer_stage_approved(self) -> None:
        stage = infer_stage(
            blocking=0,
            outstanding=0,
            approval_pct=1.0,
            has_rejection=False,
            has_changes=False,
            finalized=False,
        )
        assert stage == ReviewStage.APPROVED

    def test_infer_stage_rejected(self) -> None:
        stage = infer_stage(
            blocking=0,
            outstanding=0,
            approval_pct=0.5,
            has_rejection=True,
            has_changes=False,
            finalized=False,
        )
        assert stage == ReviewStage.REJECTED


class TestProvenance:
    def test_provenance_bundle(self) -> None:
        data = provenance_to_dict(
            ProvenanceBundle(
                evidence_ids=("e1",),
                timeline_ids=("t1",),
                detail="test",
            )
        )
        assert data["evidence_ids"] == ["e1"]
        assert data["engine_version"] == CR_ENGINE_VERSION
        assert data["policy_version"] == CR_POLICY_VERSION


class TestServiceAndApi:
    @pytest.mark.asyncio
    async def test_preview_and_generate(
        self,
        phase9e_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9e_client
        case = await create_case(client)
        preview = await client.get(
            f"/api/v1/cases/{case['id']}/case-review/preview",
        )
        assert preview.status_code == 200
        body = preview.json()["data"]
        assert body["persisted"] is False
        assert body["checklist_count"] == len(CHECKLIST_ITEMS)
        assert body["engine_version"] == CR_ENGINE_VERSION

        created = await client.post(
            f"/api/v1/cases/{case['id']}/case-review",
        )
        assert created.status_code == 200
        run = created.json()["data"]
        assert run["persisted"] is True
        assert run["id"] is not None
        assert len(run["checklist"]) == len(CHECKLIST_ITEMS)

    @pytest.mark.asyncio
    async def test_api_latest_metrics_checklist_approvals(
        self,
        phase9e_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9e_client
        case = await create_case(client)
        case_id = case["id"]
        created = await client.post(f"/api/v1/cases/{case_id}/case-review")
        run_id = created.json()["data"]["id"]
        item_id = created.json()["data"]["checklist"][0]["id"]

        latest = await client.get(f"/api/v1/cases/{case_id}/case-review/latest")
        assert latest.status_code == 200
        assert latest.json()["data"]["id"] == run_id

        by_id = await client.get(f"/api/v1/case-review/{run_id}")
        assert by_id.status_code == 200

        checklist = await client.get(
            f"/api/v1/cases/{case_id}/case-review/checklist",
        )
        assert checklist.status_code == 200
        assert checklist.json()["data"]["total"] == len(CHECKLIST_ITEMS)

        patched = await client.patch(
            f"/api/v1/case-review/checklist/{item_id}",
            json={"status": "PASS", "reviewer": "alice", "notes": "ok"},
        )
        assert patched.status_code == 200
        assert patched.json()["data"]["status"] == "PASS"

        for role in REQUIRED_APPROVER_ROLES:
            approval = await client.post(
                "/api/v1/case-review/approvals",
                json={
                    "case_id": case_id,
                    "run_id": run_id,
                    "reviewer": "alice",
                    "approver_role": role,
                    "decision": "APPROVED",
                    "comments": f"{role} ok",
                },
            )
            assert approval.status_code == 200

        approvals = await client.get(
            f"/api/v1/cases/{case_id}/case-review/approvals",
        )
        assert approvals.status_code == 200
        assert approvals.json()["data"]["total"] == 4

        metrics = await client.get(
            f"/api/v1/cases/{case_id}/case-review/metrics",
        )
        assert metrics.status_code == 200
        assert "validation_pct" in metrics.json()["data"]

        history = await client.get(
            f"/api/v1/cases/{case_id}/case-review/history",
        )
        assert history.status_code == 200
        assert history.json()["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_preview_does_not_persist(
        self,
        phase9e_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9e_client
        case = await create_case(client)
        await client.get(f"/api/v1/cases/{case['id']}/case-review/preview")
        latest = await client.get(f"/api/v1/cases/{case['id']}/case-review")
        assert latest.status_code == 404

    @pytest.mark.asyncio
    async def test_service_repository_roundtrip(
        self,
        phase9e_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, session_factory = phase9e_client
        case = await create_case(client)
        case_id = UUID(case["id"])
        async with session_factory() as session:
            service = CaseReviewService(session)
            preview = await service.preview(case_id)
            assert preview.persisted is False
            run = await service.generate(case_id)
            assert run.persisted is True
            again = await service.get_latest(case_id)
            assert again.id == run.id
            assert again.provenance.get("engine_version") == CR_ENGINE_VERSION

    @pytest.mark.asyncio
    async def test_rejection_edge_case(
        self,
        phase9e_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9e_client
        case = await create_case(client)
        created = await client.post(
            f"/api/v1/cases/{case['id']}/case-review",
        )
        run_id = created.json()["data"]["id"]
        rejected = await client.post(
            "/api/v1/case-review/approvals",
            json={
                "case_id": case["id"],
                "run_id": run_id,
                "reviewer": "bob",
                "approver_role": "CASE_SUPERVISOR",
                "decision": "REJECTED",
                "comments": "Insufficient custody",
            },
        )
        assert rejected.status_code == 200
        latest = await client.get(
            f"/api/v1/cases/{case['id']}/case-review/latest",
        )
        assert latest.json()["data"]["stage"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_invalid_approval_role(
        self,
        phase9e_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9e_client
        case = await create_case(client)
        await client.post(f"/api/v1/cases/{case['id']}/case-review")
        bad = await client.post(
            "/api/v1/case-review/approvals",
            json={
                "case_id": case["id"],
                "reviewer": "bob",
                "approver_role": "RANDOM_ROLE",
                "decision": "APPROVED",
            },
        )
        assert bad.status_code == 400
