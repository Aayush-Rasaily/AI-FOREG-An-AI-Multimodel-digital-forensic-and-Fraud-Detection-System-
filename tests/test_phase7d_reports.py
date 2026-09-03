"""Tests for Phase 7D investigation report generator."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.reporting.builder import build_report_content
from backend.app.reporting.provenance import (
    SECTION_ORDER,
    canonical_json,
)
from backend.app.reporting.renderer import render_report
from tests.test_phase4_processing import (
    create_case,
    make_text_pdf,
    process_and_extract,
)

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260901_0017_add_reports.py"
)


@pytest_asyncio.fixture
async def phase7d_client(
    tmp_path: Path,
) -> AsyncIterator[
    tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ]
]:
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
        yield client, session_factory, engine, app


async def _poll_report(
    client: httpx.AsyncClient,
    case_id: str,
    *,
    max_iter: int = 60,
) -> dict:
    for _ in range(max_iter):
        resp = await client.get(
            f"/api/v1/cases/{case_id}/reports/latest",
        )
        if resp.status_code == 200:
            data = resp.json()["data"]
            if data["status"] in ("COMPLETED", "FAILED"):
                return data
        await asyncio.sleep(0.1)
    raise TimeoutError("Report generation timed out")


class TestReportGeneration:
    @pytest.mark.asyncio
    async def test_generate_report_and_download(
        self,
        phase7d_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, session_factory, _, _ = phase7d_client
        case = await create_case(client)
        case_id = case["id"]
        pdf_bytes = make_text_pdf()
        await process_and_extract(
            client,
            case_id,
            "test-doc.pdf",
            pdf_bytes,
            "application/pdf",
        )

        resp = await client.post(
            f"/api/v1/cases/{case_id}/reports",
        )
        assert resp.status_code == 202
        report_id = resp.json()["data"]["id"]

        data = await _poll_report(client, case_id)
        assert data["status"] == "COMPLETED"
        assert data["report_checksum"] is not None
        assert len(data["report_checksum"]) == 64

        # Download JSON
        resp = await client.get(
            f"/api/v1/reports/{report_id}/download?format=json",
        )
        assert resp.status_code == 200
        content = resp.json()
        assert "sections" in content
        assert "report_checksum" in content

        # Download Markdown
        resp = await client.get(
            f"/api/v1/reports/{report_id}/download?format=md",
        )
        assert resp.status_code == 200
        assert "# Forensic Investigation Report" in resp.text

        # Download HTML
        resp = await client.get(
            f"/api/v1/reports/{report_id}/download?format=html",
        )
        assert resp.status_code == 200
        assert "<html" in resp.text

    @pytest.mark.asyncio
    async def test_list_reports(
        self,
        phase7d_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7d_client
        case = await create_case(client)
        case_id = case["id"]
        pdf_bytes = make_text_pdf()
        await process_and_extract(
            client,
            case_id,
            "test.pdf",
            pdf_bytes,
            "application/pdf",
        )

        await client.post(f"/api/v1/cases/{case_id}/reports")
        await _poll_report(client, case_id)

        resp = await client.get(
            f"/api/v1/cases/{case_id}/reports",
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) >= 1

    @pytest.mark.asyncio
    async def test_get_report_detail(
        self,
        phase7d_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7d_client
        case = await create_case(client)
        case_id = case["id"]
        pdf_bytes = make_text_pdf()
        await process_and_extract(
            client,
            case_id,
            "test.pdf",
            pdf_bytes,
            "application/pdf",
        )

        resp = await client.post(
            f"/api/v1/cases/{case_id}/reports",
        )
        report_id = resp.json()["data"]["id"]
        await _poll_report(client, case_id)

        resp = await client.get(f"/api/v1/reports/{report_id}")
        assert resp.status_code == 200
        detail = resp.json()["data"]
        assert "section_order" in detail
        assert detail["section_order"] == list(SECTION_ORDER)
        assert "content" in detail
        assert "executive_summary" in detail


class TestDeterminism:
    def test_checksum_stability(self) -> None:
        snapshot: dict = {
            "case": {
                "case_id": "aaa",
                "case_number": "C-1",
                "title": "T",
                "description": "D",
                "status": "open",
                "priority": "medium",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            },
            "evidence": [],
            "evidence_hashes": [],
            "analysis_summaries": [],
            "fusion_snapshots": [],
            "case_intelligence": None,
            "correlation": None,
            "entity_resolution": None,
            "timeline": None,
        }
        c1 = build_report_content(
            report_id="r1",
            generated_at="2026-01-01T00:00:00",
            snapshot=snapshot,
        )
        c2 = build_report_content(
            report_id="r1",
            generated_at="2026-01-02T00:00:00",
            snapshot=snapshot,
        )
        assert c1["report_checksum"] == c2["report_checksum"]

    def test_canonical_json_deterministic(self) -> None:
        a = canonical_json({"b": 2, "a": 1})
        b = canonical_json({"a": 1, "b": 2})
        assert a == b

    def test_section_ordering(self) -> None:
        assert len(SECTION_ORDER) == 22
        assert SECTION_ORDER[0] == "case_summary"
        assert SECTION_ORDER[-1] == "appendix_raw_findings"


class TestMissingAnalysis:
    def test_missing_correlation_entity_timeline(self) -> None:
        snapshot: dict = {
            "case": {
                "case_id": "aaa",
                "case_number": "C-1",
                "title": "T",
                "description": "D",
                "status": "open",
                "priority": "medium",
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            },
            "evidence": [],
            "evidence_hashes": [],
            "analysis_summaries": [],
            "fusion_snapshots": [],
            "case_intelligence": None,
            "correlation": None,
            "entity_resolution": None,
            "timeline": None,
        }
        content = build_report_content(
            report_id="r1",
            generated_at="2026-01-01",
            snapshot=snapshot,
        )
        sections = content["sections"]
        assert sections["correlation_summary"]["available"] is False
        assert sections["entity_graph_summary"]["available"] is False
        assert sections["timeline"]["available"] is False


class TestRenderer:
    def test_render_json(self) -> None:
        content = {"report_id": "r1", "sections": {}}
        payload, media, suffix = render_report(content, "json")
        assert media == "application/json"
        parsed = json.loads(payload)
        assert parsed["report_id"] == "r1"

    def test_render_markdown(self) -> None:
        content = {
            "report_id": "r1",
            "title": "Test Report",
            "sections": {},
        }
        payload, media, suffix = render_report(content, "md")
        assert media == "text/markdown; charset=utf-8"
        assert "# Test Report" in payload.decode()

    def test_render_html(self) -> None:
        content = {
            "report_id": "r1",
            "title": "Test Report",
            "sections": {},
        }
        payload, media, suffix = render_report(content, "html")
        assert media == "text/html; charset=utf-8"
        assert b"<html" in payload


class TestMigration:
    def test_migration_exists(self) -> None:
        assert MIGRATION_PATH.exists()

    def test_migration_chain(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "m0017", MIGRATION_PATH,
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        assert mod.revision == "20260901_0017"
        assert mod.down_revision == "20260901_0016"
