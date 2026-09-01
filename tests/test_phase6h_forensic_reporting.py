"""Tests for Phase 6H forensic investigation reporting."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

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
from backend.app.models.forensic_report import ForensicReport
from backend.app.reporting.builder import build_report_content
from backend.app.reporting.explainability import build_explainability
from backend.app.reporting.pdf import build_report_pdf
from backend.app.reporting.policy import ENGINE_VERSION, REPORT_VERSION
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract


@pytest_asyncio.fixture
async def phase6h_client(
    tmp_path,
) -> AsyncIterator[
    tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession], AsyncEngine, FastAPI]
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
        autoflush=False,
    )

    async def database_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application = create_app(settings)
    application.dependency_overrides[get_db_session] = database_session
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, engine, application
    await engine.dispose()


def _empty_snapshot() -> dict:
    return {
        "case": {
            "case_id": str(uuid4()),
            "case_number": "CASE-EMPTY",
            "title": "Empty",
            "status": "OPEN",
        },
        "evidence": [],
        "evidence_hashes": [],
        "analysis_summaries": [],
        "fusion_snapshots": [],
        "case_intelligence": None,
    }


def test_empty_case_report_content() -> None:
    content = build_report_content(
        report_id=str(uuid4()),
        generated_at="2026-08-31T00:00:00+00:00",
        snapshot=_empty_snapshot(),
    )
    assert content["report_version"] == REPORT_VERSION
    assert content["sections"]["executive_summary"]["evidence_count"] == 0


def test_explainability_without_intelligence() -> None:
    explainability = build_explainability(_empty_snapshot())
    assert "No Phase 6G" in explainability["limitations"][0]
    assert explainability["confidence_note"]


def test_report_pdf_generation() -> None:
    content = build_report_content(
        report_id=str(uuid4()),
        generated_at="2026-08-31T00:00:00+00:00",
        snapshot=_empty_snapshot(),
    )
    pdf = build_report_pdf(content)
    assert pdf.startswith(b"%PDF")


def test_policy_versions_documented() -> None:
    assert ENGINE_VERSION == "1.0"
    assert REPORT_VERSION == "1.0"


def test_deterministic_report_content() -> None:
    snapshot = _empty_snapshot()
    first = build_report_content(
        report_id="fixed-id",
        generated_at="2026-08-31T00:00:00+00:00",
        snapshot=snapshot,
    )
    second = build_report_content(
        report_id="fixed-id",
        generated_at="2026-08-31T00:00:00+00:00",
        snapshot=snapshot,
    )
    assert (
        first["sections"]["executive_summary"]
        == second["sections"]["executive_summary"]
    )


@pytest.mark.asyncio
async def test_api_missing_case_returns_404(phase6h_client) -> None:
    client, _, _, _ = phase6h_client
    missing = UUID("00000000-0000-0000-0000-000000000501")
    response = await client.post(f"/api/v1/cases/{missing}/reports")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_report_generation_success(phase6h_client) -> None:
    client, _, _, _ = phase6h_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "report-doc.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/evidence/{evidence['id']}/fusion-analysis")
    for _ in range(30):
        fusion_latest = await client.get(
            f"/api/v1/evidence/{evidence['id']}/fusion-analysis/latest",
        )
        if fusion_latest.status_code == 200:
            break
    await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    for _ in range(30):
        intel = await client.get(f"/api/v1/cases/{case['id']}/intelligence/latest")
        if intel.status_code == 200:
            break
    queue = await client.post(f"/api/v1/cases/{case['id']}/reports")
    assert queue.status_code == 202
    latest = None
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/reports/latest")
        if latest.status_code == 200 and latest.json()["data"]["status"] == "COMPLETED":
            break
    assert latest is not None
    assert latest.status_code == 200
    payload = latest.json()["data"]
    assert payload["case_id"] == case["id"]
    assert payload["status"] == "COMPLETED"
    assert payload["has_pdf"] is True
    assert payload["pdf_sha256"]
    assert "content" in payload
    assert "executive_summary" in payload


@pytest.mark.asyncio
async def test_api_report_status_endpoint(phase6h_client) -> None:
    client, _, _, _ = phase6h_client
    case = await create_case(client)
    queued = await client.post(f"/api/v1/cases/{case['id']}/reports")
    report_id = queued.json()["data"]["id"]
    for _ in range(30):
        status = await client.get(f"/api/v1/reports/{report_id}/status")
        if status.json()["data"]["status"] == "COMPLETED":
            break
    assert status.status_code == 200


@pytest.mark.asyncio
async def test_api_repeat_generation_allowed(phase6h_client) -> None:
    client, _, _, _ = phase6h_client
    case = await create_case(client)
    first = await client.post(f"/api/v1/cases/{case['id']}/reports")
    assert first.status_code == 202
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/reports/latest")
        if latest.status_code == 200 and latest.json()["data"]["status"] == "COMPLETED":
            break
    second = await client.post(f"/api/v1/cases/{case['id']}/reports")
    assert second.status_code == 202


@pytest.mark.asyncio
async def test_api_download_endpoint(phase6h_client) -> None:
    client, _, _, _ = phase6h_client
    case = await create_case(client)
    await client.post(f"/api/v1/cases/{case['id']}/reports")
    latest = None
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/reports/latest")
        if latest.status_code == 200 and latest.json()["data"]["status"] == "COMPLETED":
            break
    report_id = latest.json()["data"]["id"]
    download = await client.get(f"/api/v1/reports/{report_id}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")


def test_forensic_report_model_importable() -> None:
    assert ForensicReport.__tablename__ == "forensic_reports"
