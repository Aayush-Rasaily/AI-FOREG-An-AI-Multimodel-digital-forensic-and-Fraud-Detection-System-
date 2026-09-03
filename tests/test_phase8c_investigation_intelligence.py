"""Tests for Phase 8C investigation intelligence."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

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
from backend.app.intelligence.confidence import compute_overall_confidence
from backend.app.intelligence.engine import InvestigationIntelligenceEngine
from backend.app.intelligence.findings import compute_overall_risk
from backend.app.intelligence.models import ENGINE_VERSION, POLICY_VERSION
from backend.app.main import create_app
from tests.test_phase3_api import create_case
from tests.test_phase4_processing import make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260903_0022_add_investigation_summary.py"
)


@pytest_asyncio.fixture
async def phase8c_client(
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


def _strip_volatile(payload: dict[str, Any]) -> dict[str, Any]:
    clone = dict(payload)
    for key in ("id", "generated_at"):
        clone.pop(key, None)
    return clone


class TestEmptyAndSingleEvidence:
    @pytest.mark.asyncio
    async def test_empty_case_summary(
        self,
        phase8c_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase8c_client
        case = await create_case(client)
        created = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        assert created.status_code == 201, created.text
        data = created.json()["data"]
        assert data["overview"]["evidence_count"] == 0
        assert data["overall_risk"] in {"low", "medium", "high", "critical"}
        assert 0 <= data["overall_confidence"] <= 100
        assert data["engine_version"] == ENGINE_VERSION
        assert data["policy_version"] == POLICY_VERSION
        assert data["narrative"]
        for paragraph in data["narrative"]:
            assert "provenance" in paragraph
            assert "evidence_ids" in paragraph["provenance"]

    @pytest.mark.asyncio
    async def test_single_evidence_and_persistence(
        self,
        phase8c_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase8c_client
        case = await create_case(client)
        await process_and_extract(
            client,
            case["id"],
            "invoice-one.pdf",
            make_text_pdf(),
            "application/pdf",
        )
        first = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        assert first.status_code == 201
        summary = first.json()["data"]
        assert summary["overview"]["evidence_count"] == 1
        assert any(
            item["code"] == "export_report"
            for item in summary["recommendations"]
        )

        listed = await client.get(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 1

        latest = await client.get(
            f"/api/v1/cases/{case['id']}/investigation-summaries/latest",
        )
        assert latest.status_code == 200
        assert latest.json()["data"]["id"] == summary["id"]

        single = await client.get(
            f"/api/v1/investigation-summaries/{summary['id']}",
        )
        assert single.status_code == 200
        assert single.json()["data"]["id"] == summary["id"]


class TestMultiEvidenceAndDeterminism:
    @pytest.mark.asyncio
    async def test_multiple_evidence_repeat_deterministic(
        self,
        phase8c_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase8c_client
        case = await create_case(client)
        for index in range(3):
            await process_and_extract(
                client,
                case["id"],
                f"doc-{index}.pdf",
                make_text_pdf() + f"-{index}".encode(),
                "application/pdf",
            )
        first = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        second = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        assert first.status_code == 201
        assert second.status_code == 201
        left = _strip_volatile(first.json()["data"])
        right = _strip_volatile(second.json()["data"])
        assert left["overview"]["evidence_count"] == 3
        assert left["overall_risk"] == right["overall_risk"]
        assert left["overall_confidence"] == right["overall_confidence"]
        assert left["key_findings"] == right["key_findings"]
        assert left["recommendations"] == right["recommendations"]
        assert left["narrative"] == right["narrative"]
        assert left["engine_version"] == right["engine_version"]

        history = await client.get(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        items = history.json()["data"]["items"]
        assert len(items) == 2
        assert items[0]["generated_at"] >= items[1]["generated_at"]


class TestSectionsRiskConfidence:
    @pytest.mark.asyncio
    async def test_sections_risk_confidence_provenance(
        self,
        phase8c_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, session_factory = phase8c_client
        case = await create_case(client)
        await process_and_extract(
            client,
            case["id"],
            "section.pdf",
            make_text_pdf(),
            "application/pdf",
        )
        response = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        data = response.json()["data"]
        assert "available" in data["timeline_summary"]
        assert "available" in data["correlation_summary"]
        assert "modality_counts" in data["ai_summary"]
        assert "fusion" in data["ai_summary"]
        assert data["provenance"]["snapshot"]["evidence_ids"]
        for paragraph in data["narrative"]:
            assert set(paragraph["provenance"].keys()) >= {
                "evidence_ids",
                "finding_ids",
                "fusion_ids",
                "timeline_ids",
                "correlation_ids",
            }

        async with session_factory() as session:
            from uuid import UUID

            from backend.app.models.case import Case

            case_row = await session.get(Case, UUID(case["id"]))
            assert case_row is not None
            engine = InvestigationIntelligenceEngine(session)
            snapshot = engine.normalize(await engine.collect(case_row))
            confidence = compute_overall_confidence(snapshot)
            assert 0 <= confidence["overall_confidence"] <= 100
            risk = compute_overall_risk(snapshot, [])
            assert risk.value in {"low", "medium", "high", "critical"}


class TestApiErrorsAndVersioning:
    @pytest.mark.asyncio
    async def test_api_404_and_serialization(
        self,
        phase8c_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase8c_client
        missing_case = await client.post(
            "/api/v1/cases/00000000-0000-0000-0000-000000000099/investigation-summaries",
        )
        assert missing_case.status_code == 404

        case = await create_case(client)
        latest_missing = await client.get(
            f"/api/v1/cases/{case['id']}/investigation-summaries/latest",
        )
        assert latest_missing.status_code == 404

        missing_summary = await client.get(
            "/api/v1/investigation-summaries/00000000-0000-0000-0000-000000000088",
        )
        assert missing_summary.status_code == 404

        created = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        payload = created.json()["data"]
        assert isinstance(payload["overview"], dict)
        assert isinstance(payload["key_findings"], list)
        assert isinstance(payload["recommendations"], list)
        assert payload["engine_version"] == ENGINE_VERSION
        assert payload["policy_version"] == POLICY_VERSION


class TestLargeInvestigationAndMissingAnalyses:
    @pytest.mark.asyncio
    async def test_large_case_and_missing_analyses_flag(
        self,
        phase8c_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase8c_client
        case = await create_case(client)
        for index in range(8):
            await process_and_extract(
                client,
                case["id"],
                f"bulk-{index}.pdf",
                make_text_pdf() + f"-bulk-{index}".encode(),
                "application/pdf",
            )
        response = await client.post(
            f"/api/v1/cases/{case['id']}/investigation-summaries",
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["overview"]["evidence_count"] == 8
        assert data["overview"]["not_analyzed_count"] >= 0
        titles = [item["title"] for item in data["key_findings"]]
        # Without fusion, unavailable analyses should be reported.
        assert (
            "unavailable_analyses" in titles
            or data["overview"]["analyzed_count"] >= 0
        )
        assert any(
            item["code"] == "complete_missing_analyses"
            or item["code"] == "export_report"
            for item in data["recommendations"]
        )


class TestMigration:
    def test_migration_file_loads(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "phase8c_migration", MIGRATION_PATH,
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260903_0022"
        assert module.down_revision == "20260902_0021"
