"""Tests for Phase 7C entity resolution and investigation graph."""

from __future__ import annotations

import asyncio
import importlib.util
from collections.abc import AsyncIterator
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import select
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
from backend.app.entities.confidence import confidence_for_entity
from backend.app.entities.models import EntityType, RelationshipType
from backend.app.entities.normalizer import normalize_email, normalize_phone
from backend.app.entities.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.entities.provenance import format_canonical_id
from backend.app.entities.repository import EntityRepository
from backend.app.entities.resolver import EntityResolver
from backend.app.entities.service import EntityService
from backend.app.extraction.models import ExtractionSourceType, ExtractionType
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.case import Case
from backend.app.models.entity import EntityResolutionRun, InvestigationEntityRecord
from backend.app.models.evidence import Evidence
from backend.app.models.extraction import ExtractionRecord
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260901_0016_add_entities.py"
)


@pytest_asyncio.fixture
async def phase7c_client(
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


async def _poll_latest(client: httpx.AsyncClient, case_id: str) -> dict:
    for _ in range(40):
        response = await client.get(f"/api/v1/cases/{case_id}/entities/latest")
        if response.status_code == 404:
            await asyncio.sleep(0.05)
            continue
        assert response.status_code == 200
        payload = response.json()["data"]
        if payload["status"] in {"SUCCEEDED", "FAILED"}:
            return payload
        await asyncio.sleep(0.05)
    raise AssertionError("Entity resolution did not complete in time")


def _add_text_extraction(
    session: AsyncSession,
    evidence_id: UUID,
    content: str,
) -> None:
    session.add(
        ExtractionRecord(
            id=uuid4(),
            evidence_id=evidence_id,
            extraction_type=ExtractionType.TEXT,
            source_type=ExtractionSourceType.ORIGINAL,
            source_identifier="ocr-test",
            content=content,
            method="test",
            version="1.0",
            metadata_json={},
        )
    )


async def _upload_pdf(
    client: httpx.AsyncClient,
    case_id: str,
    filename: str,
    suffix: bytes = b"",
) -> dict[str, object]:
    return await process_and_extract(
        client,
        case_id,
        filename,
        make_text_pdf() + suffix,
        "application/pdf",
    )


@pytest.mark.asyncio
async def test_empty_case_resolves_zero_entities(phase7c_client) -> None:
    client, _, _, _ = phase7c_client
    case = await create_case(client)
    response = await client.post(f"/api/v1/cases/{case['id']}/entities")
    assert response.status_code == 202
    latest = await _poll_latest(client, case["id"])
    assert latest["status"] == "SUCCEEDED"
    assert latest["entity_count"] == 0
    assert latest["relationship_count"] == 0
    assert latest["graph"]["nodes"] == []


@pytest.mark.asyncio
async def test_one_evidence_creates_media_and_hash(phase7c_client) -> None:
    client, _, _, _ = phase7c_client
    case = await create_case(client)
    await _upload_pdf(client, case["id"], "one.pdf")
    response = await client.post(f"/api/v1/cases/{case['id']}/entities")
    assert response.status_code == 202
    latest = await _poll_latest(client, case["id"])
    assert latest["status"] == "SUCCEEDED"
    assert latest["entity_count"] >= 2
    types = {item["entity_type"] for item in latest["entities"]}
    assert "file_hash" in types
    assert "document" in types or "image" in types


@pytest.mark.asyncio
async def test_email_merge_across_evidence(phase7c_client) -> None:
    client, session_factory, _, _ = phase7c_client
    case = await create_case(client)
    await _upload_pdf(client, case["id"], "a.pdf", b"-a")
    await _upload_pdf(client, case["id"], "b.pdf", b"-b")
    async with session_factory() as session:
        evidence_rows = list(
            await session.scalars(
                select(Evidence).where(Evidence.case_id == UUID(case["id"]))
            )
        )
        for evidence in evidence_rows:
            _add_text_extraction(
                session,
                evidence.id,
                "Reach shared@example.com for details",
            )
        await session.commit()

    response = await client.post(f"/api/v1/cases/{case['id']}/entities")
    assert response.status_code == 202
    latest = await _poll_latest(client, case["id"])
    emails = [item for item in latest["entities"] if item["entity_type"] == "email"]
    assert len(emails) == 1
    assert emails[0]["normalized_key"] == "shared@example.com"
    assert emails[0]["support_count"] >= 2
    assert len(emails[0]["evidence_ids"]) >= 2
    assert emails[0]["canonical_id"].startswith("ENTITY-")
    assert "extraction_ids" in emails[0]["provenance"]


@pytest.mark.asyncio
async def test_phone_and_gps_entities(phase7c_client) -> None:
    client, session_factory, _, _ = phase7c_client
    case = await create_case(client)
    await _upload_pdf(client, case["id"], "p.pdf")
    async with session_factory() as session:
        evidence = (
            await session.scalars(
                select(Evidence).where(Evidence.case_id == UUID(case["id"]))
            )
        ).first()
        assert evidence is not None
        _add_text_extraction(session, evidence.id, "Call +1 (555) 123-4567")
        evidence.metadata_json = {
            **(evidence.metadata_json or {}),
            "exif": {"gps": {"latitude": "12.34", "longitude": "56.78"}},
            "camera_model": "Canon EOS",
        }
        await session.commit()

    latest_response = await client.post(f"/api/v1/cases/{case['id']}/entities")
    assert latest_response.status_code == 202
    latest = await _poll_latest(client, case["id"])
    types = {item["entity_type"] for item in latest["entities"]}
    assert "phone" in types
    assert "location" in types
    assert "camera" in types
    rel_types = {item["relationship_type"] for item in latest["relationships"]}
    assert (
        "contains" in rel_types
        or "located_at" in rel_types
        or "captured_by" in rel_types
    )


@pytest.mark.asyncio
async def test_duplicate_prevention_and_deterministic_ids(phase7c_client) -> None:
    client, session_factory, _, _ = phase7c_client
    case = await create_case(client)
    await _upload_pdf(client, case["id"], "x.pdf")
    async with session_factory() as session:
        evidence = (
            await session.scalars(
                select(Evidence).where(Evidence.case_id == UUID(case["id"]))
            )
        ).first()
        assert evidence is not None
        for _ in range(2):
            _add_text_extraction(session, evidence.id, "mail@example.com")
        await session.commit()

    await client.post(f"/api/v1/cases/{case['id']}/entities")
    first = await _poll_latest(client, case["id"])
    await client.post(f"/api/v1/cases/{case['id']}/entities")
    second = await _poll_latest(client, case["id"])
    first_ids = [item["canonical_id"] for item in first["entities"]]
    second_ids = [item["canonical_id"] for item in second["entities"]]
    assert first_ids == second_ids
    emails = [item for item in first["entities"] if item["entity_type"] == "email"]
    assert len(emails) == 1


@pytest.mark.asyncio
async def test_active_run_conflict(phase7c_client, tmp_path) -> None:
    client, session_factory, _, _ = phase7c_client
    case = await create_case(client)
    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
    )
    async with session_factory() as session:
        service = EntityService(
            session=session,
            storage=LocalStorage(settings.storage_root),
            hash_service=HashService(),
            settings=settings,
        )
        await service.create_analysis(UUID(case["id"]))
        with pytest.raises(ConflictError):
            await service.create_analysis(UUID(case["id"]))


@pytest.mark.asyncio
async def test_entity_detail_endpoints(phase7c_client) -> None:
    client, _, _, _ = phase7c_client
    case = await create_case(client)
    await _upload_pdf(client, case["id"], "api.pdf")
    await client.post(f"/api/v1/cases/{case['id']}/entities")
    latest = await _poll_latest(client, case["id"])
    entity = latest["entities"][0]
    detail = await client.get(f"/api/v1/entities/{entity['id']}")
    assert detail.status_code == 200
    assert detail.json()["data"]["canonical_id"] == entity["canonical_id"]
    graph = await client.get(f"/api/v1/entities/{entity['id']}/graph")
    assert graph.status_code == 200
    assert "nodes" in graph.json()["data"]
    rels = await client.get(f"/api/v1/entities/{entity['id']}/relationships")
    assert rels.status_code == 200
    history = await client.get(f"/api/v1/cases/{case['id']}/entities")
    assert history.status_code == 200
    assert history.json()["data"]["total"] >= 1


def test_migration_revision_chain() -> None:
    spec = importlib.util.spec_from_file_location("migration_0016", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "20260901_0016"
    assert module.down_revision == "20260901_0015"


def test_canonical_id_and_confidence_policy() -> None:
    assert format_canonical_id(1) == "ENTITY-000001"
    assert format_canonical_id(12) == "ENTITY-000012"
    assert confidence_for_entity(EntityType.EMAIL) == 0.98
    assert confidence_for_entity(EntityType.FILE_HASH) == 1.0
    assert normalize_email("A@B.com") == "a@b.com"
    assert normalize_phone("+1 (555) 000-1111") == "15550001111"
    assert RelationshipType.CONTAINS.value == "contains"


@pytest.mark.asyncio
async def test_repository_latest(phase7c_client) -> None:
    client, session_factory, _, _ = phase7c_client
    case = await create_case(client)
    await _upload_pdf(client, case["id"], "repo.pdf")
    await client.post(f"/api/v1/cases/{case['id']}/entities")
    await _poll_latest(client, case["id"])
    async with session_factory() as session:
        repository = EntityRepository(session)
        latest = await repository.get_latest_for_case(UUID(case["id"]))
        assert latest is not None
        assert isinstance(latest, EntityResolutionRun)
        assert latest.entity_count >= 1
        assert all(
            isinstance(item, InvestigationEntityRecord) for item in latest.entities
        )


@pytest.mark.asyncio
async def test_resolver_direct_empty(phase7c_client) -> None:
    client, session_factory, _, _ = phase7c_client
    case_payload = await create_case(client)
    async with session_factory() as session:
        case = await session.get(Case, UUID(case_payload["id"]))
        assert case is not None
        result = await EntityResolver().resolve(session, case)
        assert result.entities == ()
        assert result.relationships == ()
        assert result.metadata["evidence_count"] == 0
        assert result.provenance["engine_version"] == ENGINE_VERSION
        assert result.provenance["policy_version"] == POLICY_VERSION

