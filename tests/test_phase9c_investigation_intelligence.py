"""Tests for Phase 9C investigation intelligence & hypothesis engine."""

from __future__ import annotations

import importlib.util
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
from backend.app.investigation_intelligence.evidence_gaps import detect_gaps
from backend.app.investigation_intelligence.hypothesis import generate_hypotheses
from backend.app.investigation_intelligence.models import (
    CoverageMetrics,
    HypothesisType,
)
from backend.app.investigation_intelligence.policy import (
    II_ENGINE_VERSION,
    II_POLICY_VERSION,
)
from backend.app.investigation_intelligence.prioritization import (
    priority_from_score,
)
from backend.app.investigation_intelligence.recommendations import (
    generate_recommendations,
)
from backend.app.investigation_intelligence.scoring import (
    investigation_score,
    score_hypothesis,
)
from backend.app.investigation_intelligence.service import (
    InvestigationIntelligenceEngineService,
)
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260909_0028_add_investigation_intelligence.py"
)


@pytest_asyncio.fixture
async def phase9c_client(
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
        spec = importlib.util.spec_from_file_location("ii_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260909_0028"
        assert module.down_revision == "20260908_0027"


class TestScoringAndPriority:
    def test_score_hypothesis_support_boost(self) -> None:
        base = score_hypothesis(
            "TIMELINE_CONFLICT",
            support_count=1,
            contradict_count=0,
            provenance_count=1,
        )
        boosted = score_hypothesis(
            "TIMELINE_CONFLICT",
            support_count=4,
            contradict_count=0,
            provenance_count=3,
        )
        assert boosted >= base
        assert 0 < boosted <= 1

    def test_investigation_score_bounds(self) -> None:
        score = investigation_score(
            overall_completeness=0.8,
            open_conflicts=1,
            high_priority_gaps=1,
            hypothesis_count=3,
        )
        assert 0 <= score <= 100

    def test_priority_thresholds(self) -> None:
        assert priority_from_score(0.9).value == "HIGH"
        assert priority_from_score(0.5).value == "MEDIUM"
        assert priority_from_score(0.1).value == "LOW"


class TestHypothesisAndGaps:
    def test_empty_investigation_insufficient_evidence(self) -> None:
        coverage = CoverageMetrics()
        hyps = generate_hypotheses({"evidence": []}, coverage)
        assert any(
            item.hypothesis_type == HypothesisType.INSUFFICIENT_EVIDENCE
            for item in hyps
        )

    def test_timeline_conflict_hypothesis(self) -> None:
        coverage = CoverageMetrics(evidence_total=2, overall_completeness=0.4)
        snapshot = {
            "evidence": [
                {"id": "e1", "mime_type": "image/jpeg", "has_metadata": True,
                 "has_timestamp": True, "missing_original": False},
                {"id": "e2", "mime_type": "image/jpeg", "has_metadata": True,
                 "has_timestamp": True, "missing_original": False},
            ],
            "ai_findings": [],
            "correlations": [],
            "timeline_conflicts": [
                {"id": "c1", "conflict_type": "CLOCK_SKEW", "evidence_ids": ["e1"]},
            ],
            "fusion_runs": [],
            "signatures": [],
            "graph_relationships": [],
            "graph_entities": [],
            "custody_by_evidence": {"e1": 1, "e2": 1},
            "timeline_event_clusters": [],
        }
        hyps = generate_hypotheses(snapshot, coverage)
        assert any(
            item.hypothesis_type == HypothesisType.TIMELINE_CONFLICT
            for item in hyps
        )

    def test_gap_detection_missing_custody(self) -> None:
        coverage = CoverageMetrics(evidence_total=1, open_conflicts=0)
        snapshot = {
            "evidence": [
                {
                    "id": "e1",
                    "mime_type": "application/pdf",
                    "has_metadata": False,
                    "has_timestamp": False,
                    "missing_original": False,
                }
            ],
            "extractions": [],
            "ai_findings": [],
            "signatures": [],
            "correlations": [],
            "timeline_events": [],
            "graph_entities": [],
            "custody_by_evidence": {"e1": 0},
        }
        gaps = detect_gaps(snapshot, coverage)
        types = {item.gap_type.value for item in gaps}
        assert "MISSING_CHAIN_OF_CUSTODY" in types
        assert "MISSING_METADATA" in types

    def test_recommendations_from_gaps(self) -> None:
        coverage = CoverageMetrics(evidence_total=1)
        snapshot = {
            "evidence": [
                {
                    "id": "e1",
                    "mime_type": "image/jpeg",
                    "has_metadata": True,
                    "has_timestamp": True,
                    "missing_original": True,
                }
            ],
            "extractions": [],
            "ai_findings": [],
            "signatures": [],
            "correlations": [],
            "timeline_events": [{"id": "t1"}],
            "graph_entities": [{"id": "g1"}],
            "custody_by_evidence": {"e1": 1},
        }
        gaps = detect_gaps(snapshot, coverage)
        hyps = generate_hypotheses(snapshot, coverage)
        recs = generate_recommendations(hyps, gaps)
        assert recs
        assert all(item.action_text for item in recs)

    def test_deterministic_ordering_repeatable(self) -> None:
        coverage = CoverageMetrics(evidence_total=0)
        first = generate_hypotheses({"evidence": []}, coverage)
        second = generate_hypotheses({"evidence": []}, coverage)
        assert [item.hypothesis_key for item in first] == [
            item.hypothesis_key for item in second
        ]

    def test_multi_evidence_corroboration(self) -> None:
        coverage = CoverageMetrics(evidence_total=2, overall_completeness=0.5)
        snapshot = {
            "evidence": [
                {"id": "e1", "mime_type": "image/jpeg", "has_metadata": True,
                 "has_timestamp": True, "missing_original": False},
                {"id": "e2", "mime_type": "image/jpeg", "has_metadata": True,
                 "has_timestamp": True, "missing_original": False},
            ],
            "ai_findings": [],
            "correlations": [
                {
                    "id": "corr1",
                    "left_evidence_id": "e1",
                    "right_evidence_id": "e2",
                }
            ],
            "timeline_conflicts": [],
            "fusion_runs": [],
            "signatures": [],
            "graph_relationships": [],
            "graph_entities": [],
            "custody_by_evidence": {"e1": 1, "e2": 1},
            "timeline_event_clusters": [],
        }
        hyps = generate_hypotheses(snapshot, coverage)
        assert any(
            item.hypothesis_type == HypothesisType.CROSS_EVIDENCE_CORROBORATION
            for item in hyps
        )


class TestApiAndService:
    @pytest.mark.asyncio
    async def test_preview_empty_case(
        self,
        phase9c_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9c_client
        case = await create_case(client)
        preview = await client.get(
            f"/api/v1/cases/{case['id']}/investigation-preview",
        )
        assert preview.status_code == 200, preview.text
        data = preview.json()["data"]
        assert data["persisted"] is False
        assert data["engine_version"] == II_ENGINE_VERSION
        assert data["policy_version"] == II_POLICY_VERSION
        assert data["hypothesis_count"] >= 1

    @pytest.mark.asyncio
    async def test_preview_does_not_persist(
        self,
        phase9c_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9c_client
        case = await create_case(client)
        await client.get(
            f"/api/v1/cases/{case['id']}/investigation-preview",
        )
        missing = await client.get(
            f"/api/v1/cases/{case['id']}/investigation-intelligence",
        )
        assert missing.status_code == 404

    @pytest.mark.asyncio
    async def test_analyze_get_lists_summary(
        self,
        phase9c_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9c_client
        case = await create_case(client)
        case_id = case["id"]

        built = await client.post(
            f"/api/v1/cases/{case_id}/investigation-intelligence",
        )
        assert built.status_code == 200, built.text
        body = built.json()["data"]
        assert body["status"] == "SUCCEEDED"
        assert body["persisted"] is True
        run_id = body["id"]
        assert "coverage" in body
        assert isinstance(body["hypotheses"], list)

        latest = await client.get(
            f"/api/v1/cases/{case_id}/investigation-intelligence/latest",
        )
        assert latest.status_code == 200
        assert latest.json()["data"]["id"] == run_id

        by_id = await client.get(
            f"/api/v1/investigation-intelligence/{run_id}",
        )
        assert by_id.status_code == 200

        hyps = await client.get(f"/api/v1/cases/{case_id}/hypotheses")
        assert hyps.status_code == 200
        gaps = await client.get(f"/api/v1/cases/{case_id}/evidence-gaps")
        assert gaps.status_code == 200
        recs = await client.get(f"/api/v1/cases/{case_id}/recommendations")
        assert recs.status_code == 200
        summary = await client.get(
            f"/api/v1/cases/{case_id}/investigation-summary",
        )
        assert summary.status_code == 200
        assert "investigation_score" in summary.json()["data"]

    @pytest.mark.asyncio
    async def test_repeat_analyze_new_runs(
        self,
        phase9c_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9c_client
        case = await create_case(client)
        first = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-intelligence",
        )
        second = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-intelligence",
        )
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json()["data"]["id"] != second.json()["data"]["id"]

    @pytest.mark.asyncio
    async def test_service_coverage_metrics(
        self,
        phase9c_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, session_factory = phase9c_client
        case = await create_case(client)
        from uuid import UUID

        async with session_factory() as session:
            service = InvestigationIntelligenceEngineService(session)
            preview = await service.preview(UUID(case["id"]))
            assert preview.coverage.evidence_total >= 0
            assert 0 <= preview.coverage.overall_completeness <= 1

    @pytest.mark.asyncio
    async def test_missing_run_404(
        self,
        phase9c_client: tuple[
            httpx.AsyncClient, async_sessionmaker[AsyncSession]
        ],
    ) -> None:
        client, _ = phase9c_client
        missing = await client.get(
            "/api/v1/investigation-intelligence/"
            "00000000-0000-0000-0000-000000000099",
        )
        assert missing.status_code == 404

    def test_provenance_on_hypothesis(self) -> None:
        coverage = CoverageMetrics(evidence_total=1)
        snapshot = {
            "evidence": [
                {
                    "id": "e1",
                    "mime_type": "image/jpeg",
                    "has_metadata": True,
                    "has_timestamp": True,
                    "missing_original": False,
                }
            ],
            "ai_findings": [],
            "correlations": [],
            "timeline_conflicts": [],
            "fusion_runs": [],
            "signatures": [],
            "graph_relationships": [],
            "graph_entities": [],
            "custody_by_evidence": {"e1": 0},
            "timeline_event_clusters": [],
        }
        hyps = generate_hypotheses(snapshot, coverage)
        assert hyps
        assert hyps[0].provenance is not None

    def test_edge_case_single_evidence_gaps(self) -> None:
        coverage = CoverageMetrics(evidence_total=1)
        snapshot = {
            "evidence": [
                {
                    "id": "e1",
                    "mime_type": "image/png",
                    "has_metadata": True,
                    "has_timestamp": True,
                    "missing_original": False,
                }
            ],
            "extractions": [],
            "ai_findings": [],
            "signatures": [],
            "correlations": [],
            "timeline_events": [],
            "graph_entities": [],
            "custody_by_evidence": {"e1": 1},
        }
        gaps = detect_gaps(snapshot, coverage)
        assert any(
            item.gap_type.value == "MISSING_COMPARISON_TARGET" for item in gaps
        )

    def test_policy_versions(self) -> None:
        assert II_ENGINE_VERSION.startswith("9c.")
        assert II_POLICY_VERSION

    def test_shared_identity_hypothesis(self) -> None:
        coverage = CoverageMetrics(evidence_total=2, overall_completeness=0.5)
        snapshot = {
            "evidence": [
                {"id": "e1", "mime_type": "text/plain", "has_metadata": True,
                 "has_timestamp": True, "missing_original": False},
                {"id": "e2", "mime_type": "text/plain", "has_metadata": True,
                 "has_timestamp": True, "missing_original": False},
            ],
            "ai_findings": [],
            "correlations": [],
            "timeline_conflicts": [],
            "fusion_runs": [],
            "signatures": [],
            "graph_relationships": [],
            "graph_entities": [
                {
                    "entity_key": "EMAIL:a@b.com",
                    "entity_type": "EMAIL",
                    "evidence_ids": ["e1", "e2"],
                }
            ],
            "custody_by_evidence": {"e1": 1, "e2": 1},
            "timeline_event_clusters": [],
        }
        hyps = generate_hypotheses(snapshot, coverage)
        types = {item.hypothesis_type for item in hyps}
        assert HypothesisType.SHARED_IDENTITY_INDICATORS in types
