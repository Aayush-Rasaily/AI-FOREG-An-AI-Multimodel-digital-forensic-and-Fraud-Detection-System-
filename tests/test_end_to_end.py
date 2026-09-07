"""End-to-end investigation workflow validation for AI-Forge v1.0."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
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
from tests.test_phase3_api import create_case
from tests.test_phase4_processing import make_text_pdf, process_and_extract


@pytest_asyncio.fixture
async def e2e_client(
    tmp_path,
) -> AsyncIterator[tuple[httpx.AsyncClient, AsyncEngine]]:
    settings = Settings(
        debug=True,
        app_env="test",
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        temp_storage_path=tmp_path / "data" / "tmp",
        ai_model_root=tmp_path / "models",
        log_config_path=tmp_path / "missing-logging.json",
        rate_limit_enabled=False,
        rate_limit_use_redis=False,
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
        autoflush=False,
    )

    async def database_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application = create_app(settings)
    application.dependency_overrides[get_db_session] = database_session
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, engine
    application.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_complete_investigation_workflow(
    e2e_client: tuple[httpx.AsyncClient, AsyncEngine],
) -> None:
    """Create case → evidence → process → extract → AI → fusion → report → export."""

    client, _ = e2e_client

    live = await client.get("/api/v1/health/live")
    assert live.status_code == 200
    assert live.json()["success"] is True

    case = await create_case(client)
    case_id = UUID(str(case["id"]))
    evidence = await process_and_extract(
        client,
        case["id"],
        "invoice.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    evidence_id = evidence["id"]

    jobs = await client.get(f"/api/v1/evidence/{evidence_id}/processing")
    assert jobs.status_code == 200
    assert jobs.json()["data"]["items"][0]["status"] == "SUCCEEDED"

    extractions = await client.get(f"/api/v1/evidence/{evidence_id}/extractions")
    assert extractions.status_code == 200
    assert extractions.json()["data"]["status"] in {"SUCCEEDED", "PARTIAL"}

    analyze = await client.post(f"/api/v1/evidence/{evidence_id}/analyze")
    assert analyze.status_code == 202
    document_ai = await client.post(f"/api/v1/evidence/{evidence_id}/document-analysis")
    assert document_ai.status_code == 202

    models = await client.get("/api/v1/models")
    assert models.status_code == 200
    assert any(item["name"] == "dummy" for item in models.json()["data"]["items"])

    fusion = await client.post(f"/api/v1/evidence/{evidence_id}/fusion-analysis")
    assert fusion.status_code == 202
    latest_fusion = await client.get(
        f"/api/v1/evidence/{evidence_id}/fusion-analysis/latest"
    )
    assert latest_fusion.status_code == 200
    assert latest_fusion.json()["data"]["id"]

    correlation = await client.post(f"/api/v1/cases/{case_id}/correlations")
    assert correlation.status_code == 202
    timeline = await client.post(f"/api/v1/cases/{case_id}/timeline")
    assert timeline.status_code == 202
    listed_timeline = await client.get(f"/api/v1/cases/{case_id}/timeline")
    assert listed_timeline.status_code == 200
    assert listed_timeline.json()["data"]["total"] >= 1

    report = await client.post(f"/api/v1/cases/{case_id}/reports")
    assert report.status_code == 202
    latest_report = await client.get(f"/api/v1/cases/{case_id}/reports/latest")
    assert latest_report.status_code == 200
    report_id = latest_report.json()["data"]["id"]
    status = await client.get(f"/api/v1/reports/{report_id}/status")
    assert status.status_code == 200

    exported = await client.post(
        f"/api/v1/cases/{case_id}/export",
        json={"format": "json_package", "include_binaries": False},
    )
    assert exported.status_code == 200
    assert exported.json()["data"]["status"] == "COMPLETED"

    monitoring = await client.get("/api/v1/monitoring/dashboard")
    assert monitoring.status_code == 200

    retrieved = await client.get(f"/api/v1/evidence/{evidence_id}")
    assert retrieved.status_code == 200
    stored = cast(dict[str, object], retrieved.json()["data"])
    assert stored["sha256_hash"]
    assert stored["original_filename"] == "invoice.pdf"
