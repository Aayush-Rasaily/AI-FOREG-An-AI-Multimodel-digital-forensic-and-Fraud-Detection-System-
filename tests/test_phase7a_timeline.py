"""Tests for Phase 7A investigation timeline engine."""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
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
from backend.app.application.services.hashing import HashService
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.timeline import InvestigationTimeline, TimelineEventRecord
from backend.app.timeline.confidence import score_confidence
from backend.app.timeline.engine import TimelineEngine
from backend.app.timeline.models import TimelineEvent, TimelineEventType
from backend.app.timeline.normalization import normalize_timestamp
from backend.app.timeline.ordering import order_events
from backend.app.timeline.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.timeline.repository import TimelineRepository
from backend.app.timeline.service import TimelineService
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260901_0014_add_timeline.py"
)


@pytest_asyncio.fixture
async def phase7a_client(
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


async def _poll_latest_timeline(
    client: httpx.AsyncClient,
    case_id: str,
) -> dict:
    for _ in range(40):
        response = await client.get(f"/api/v1/cases/{case_id}/timeline/latest")
        if response.status_code == 200:
            payload = response.json()["data"]
            if payload["status"] in {"SUCCEEDED", "FAILED"}:
                return payload
        await _sleep_briefly()
    raise AssertionError("Timeline reconstruction did not complete in time.")


async def _sleep_briefly() -> None:
    import asyncio

    await asyncio.sleep(0.05)


def test_policy_versions_documented() -> None:
    assert ENGINE_VERSION == "1.0"
    assert POLICY_VERSION == "1.0"


def test_timezone_normalization_to_utc() -> None:
    normalized = normalize_timestamp(
        "2026-08-31T12:00:00+05:30",
        source="exif",
    )
    assert normalized.normalized_timestamp is not None
    assert normalized.normalized_timestamp.tzinfo == UTC
    assert normalized.timezone is not None
    assert normalized.confidence > 0


def test_missing_timezone_deducts_confidence() -> None:
    with_tz = normalize_timestamp(
        datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
        source="filesystem",
    )
    without_tz = normalize_timestamp(
        datetime(2026, 8, 31, 12, 0),
        source="filesystem",
    )
    assert without_tz.confidence < with_tz.confidence


def test_confidence_scoring_is_deterministic() -> None:
    assert score_confidence("exif", timezone_known=True, timestamp_present=True) == 0.9
    assert (
        score_confidence("missing", timezone_known=False, timestamp_present=False)
        == 0.0
    )


def test_ordering_is_deterministic() -> None:
    first = TimelineEvent(
        event_id="b",
        case_id=uuid4(),
        evidence_id=None,
        event_type=TimelineEventType.EVIDENCE_UPLOADED,
        timestamp=datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
        timezone="UTC",
        normalized_timestamp=datetime(2026, 8, 31, 12, 0, tzinfo=UTC),
        confidence=0.9,
        uncertainty_ms=1000,
        description="later",
        source="evidence",
        source_id="b",
        provenance={},
    )
    second = TimelineEvent(
        event_id="a",
        case_id=first.case_id,
        evidence_id=None,
        event_type=TimelineEventType.EVIDENCE_UPLOADED,
        timestamp=datetime(2026, 8, 31, 11, 0, tzinfo=UTC),
        timezone="UTC",
        normalized_timestamp=datetime(2026, 8, 31, 11, 0, tzinfo=UTC),
        confidence=0.95,
        uncertainty_ms=1000,
        description="earlier",
        source="evidence",
        source_id="a",
        provenance={},
    )
    ordered = order_events([first, second])
    assert ordered[0].event_id == "a"
    assert ordered[1].event_id == "b"


@pytest.mark.asyncio
async def test_empty_case_timeline(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    created = await client.post(f"/api/v1/cases/{case['id']}/timeline")
    assert created.status_code == 202
    timeline = await _poll_latest_timeline(client, case["id"])
    assert timeline["status"] == "SUCCEEDED"
    assert timeline["event_count"] == 0


@pytest.mark.asyncio
async def test_single_evidence_timeline(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "timeline.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline = await _poll_latest_timeline(client, case["id"])
    assert timeline["event_count"] >= 1
    assert any(
        event["event_type"] == "evidence_uploaded" for event in timeline["events"]
    )


@pytest.mark.asyncio
async def test_multiple_evidence_timeline(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    for index in range(2):
        content = make_text_pdf() + f"variant-{index}".encode()
        await process_and_extract(
            client,
            case["id"],
            f"evidence-{index}.pdf",
            content,
            "application/pdf",
        )
    await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline = await _poll_latest_timeline(client, case["id"])
    evidence_ids = {
        event["evidence_id"]
        for event in timeline["events"]
        if event["evidence_id"] is not None
    }
    assert len(evidence_ids) >= 2


@pytest.mark.asyncio
async def test_provenance_references_evidence(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "prov.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline = await _poll_latest_timeline(client, case["id"])
    uploaded = next(
        event
        for event in timeline["events"]
        if event["event_type"] == "evidence_uploaded"
    )
    assert "evidence_id" in uploaded["provenance"]
    assert "sha256_hash" in uploaded["provenance"]


@pytest.mark.asyncio
async def test_missing_timestamp_event_for_document(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("missing-date.pdf", make_text_pdf(), "application/pdf")},
    )
    await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline = await _poll_latest_timeline(client, case["id"])
    assert any(
        event["event_type"] == "timestamp_missing" for event in timeline["events"]
    )


@pytest.mark.asyncio
async def test_api_list_and_get_timeline(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline = await _poll_latest_timeline(client, case["id"])
    listed = await client.get(f"/api/v1/cases/{case['id']}/timeline")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] >= 1
    detail = await client.get(f"/api/v1/timeline/{timeline['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == timeline["id"]


@pytest.mark.asyncio
async def test_conflicts_endpoint(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline = await _poll_latest_timeline(client, case["id"])
    response = await client.get(f"/api/v1/timeline/{timeline['id']}/conflicts")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


@pytest.mark.asyncio
async def test_repeat_generation_preserves_history(phase7a_client) -> None:
    client, _, _, _ = phase7a_client
    case = await create_case(client)
    first = await client.post(f"/api/v1/cases/{case['id']}/timeline")
    assert first.status_code == 202
    await _poll_latest_timeline(client, case["id"])
    second = await client.post(f"/api/v1/cases/{case['id']}/timeline")
    assert second.status_code == 202
    await _poll_latest_timeline(client, case["id"])
    listed = await client.get(f"/api/v1/cases/{case['id']}/timeline")
    assert listed.json()["data"]["total"] >= 2


@pytest.mark.asyncio
async def test_active_duplicate_prevention(phase7a_client) -> None:
    client, session_factory, _, application = phase7a_client
    case = await create_case(client)
    settings = application.state.settings
    async with session_factory() as session:
        service = TimelineService(
            session=session,
            storage=LocalStorage(settings.storage_root),
            hash_service=HashService(),
            settings=settings,
        )
        await service.create_timeline(UUID(str(case["id"])))
        with pytest.raises(ConflictError):
            await service.create_timeline(UUID(str(case["id"])))


@pytest.mark.asyncio
async def test_repository_latest_and_delete(phase7a_client) -> None:
    client, session_factory, _, _ = phase7a_client
    case = await create_case(client)
    created = await client.post(f"/api/v1/cases/{case['id']}/timeline")
    timeline_id = created.json()["data"]["id"]
    await _poll_latest_timeline(client, case["id"])
    async with session_factory() as session:
        repository = TimelineRepository(session)
        latest = await repository.get_latest_for_case(UUID(str(case["id"])))
        assert latest is not None
        assert str(latest.id) == timeline_id
        await repository.delete_timeline(UUID(str(timeline_id)))
        await session.commit()
        assert await repository.get_timeline(UUID(str(timeline_id))) is None


def test_migration_module() -> None:
    spec = importlib.util.spec_from_file_location("migration_0014", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "20260901_0014"
    assert migration.down_revision == "20260831_0013"
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)


def test_timeline_models_importable() -> None:
    assert InvestigationTimeline.__tablename__ == "investigation_timelines"
    assert TimelineEventRecord.__tablename__ == "timeline_events"


@pytest.mark.asyncio
async def test_engine_builds_without_fabrication(phase7a_client) -> None:
    client, session_factory, _, _ = phase7a_client
    case = await create_case(client)
    async with session_factory() as session:
        from backend.app.models.case import Case

        case_row = await session.get(Case, UUID(str(case["id"])))
        assert case_row is not None
        result = await TimelineEngine().build(session, case_row)
        assert result.events == ()
        assert result.provenance["engine_version"] == ENGINE_VERSION
