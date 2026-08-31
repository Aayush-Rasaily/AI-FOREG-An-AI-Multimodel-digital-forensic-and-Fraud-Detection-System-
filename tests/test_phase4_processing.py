"""Integration tests for the Phase 4 deterministic processing pipeline."""

import hashlib
from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

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
from backend.app.application.services.processing_service import (
    ProcessingOrchestrator,
)
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models import Artifact, Evidence
from tests.test_phase3_api import create_case


@pytest_asyncio.fixture
async def phase4_client(
    tmp_path,
) -> AsyncIterator[
    tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession], AsyncEngine, FastAPI]
]:
    """Create an isolated API, SQLite database, and local storage root."""

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
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client, session_factory, engine, application
    application.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_processing_creates_artifacts_and_preserves_original(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """The mandatory integrity invariant holds across a completed pipeline."""

    client, session_factory, _, application = phase4_client
    case = await create_case(client)
    content = b"%PDF-1.7\nphase-four-original\n"
    uploaded = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("invoice.pdf", content, "application/pdf")},
    )
    assert uploaded.status_code == 201
    evidence = uploaded.json()["data"]
    original_hash = hashlib.sha256(content).hexdigest()

    queued = await client.post(f"/api/v1/evidence/{evidence['id']}/process")
    assert queued.status_code == 202
    assert queued.json()["data"]["status"] == "QUEUED"

    jobs = await client.get(f"/api/v1/evidence/{evidence['id']}/processing")
    assert jobs.status_code == 200
    job = jobs.json()["data"]["items"][0]
    assert job["status"] == "SUCCEEDED"
    assert job["attempt"] == 1

    artifacts = await client.get(f"/api/v1/evidence/{evidence['id']}/artifacts")
    assert artifacts.status_code == 200
    artifact_items = artifacts.json()["data"]["items"]
    assert {item["artifact_type"] for item in artifact_items} == {
        "METADATA",
        "CLASSIFICATION",
        "PREVIEW",
    }
    assert all(len(item["sha256_hash"]) == 64 for item in artifact_items)
    classification_artifact = next(
        item for item in artifact_items if item["artifact_type"] == "CLASSIFICATION"
    )
    assert classification_artifact["metadata"]["classification"] == "DOCUMENT"

    async with session_factory() as session:
        stored = await session.get(Evidence, UUID(str(evidence["id"])))
        assert stored is not None
        stored_path = application.state.settings.storage_root.joinpath(
            *stored.storage_key.split("/")
        )
        stored_artifacts = list(
            (
                await session.scalars(
                    select(Artifact).where(
                        Artifact.evidence_id == stored.id
                    )
                )
            ).all()
        )
        assert len(stored_artifacts) == 3
        assert all(
            application.state.settings.storage_root.joinpath(
                *artifact.storage_key.split("/")
            ).is_file()
            for artifact in stored_artifacts
        )
    assert stored_path.read_bytes() == content
    assert hashlib.sha256(stored_path.read_bytes()).hexdigest() == original_hash

    retrieved = await client.get(f"/api/v1/evidence/{evidence['id']}")
    assert retrieved.json()["data"]["status"] == "READY_FOR_ANALYSIS"
    event_types = {
        event["event_type"] for event in retrieved.json()["data"]["custody_events"]
    }
    assert {"PROCESSING_STARTED", "PROCESSING_COMPLETED", "ARTIFACT_CREATED"} <= (
        event_types
    )
    assert len(event_types) >= 4


@pytest.mark.asyncio
async def test_active_processing_jobs_are_unique_and_repeat_is_allowed(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """Active duplicates conflict, while a later explicit run is allowed."""

    client, session_factory, _, application = phase4_client
    case = await create_case(client)
    uploaded = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("invoice.pdf", b"%PDF-1.7\nrepeat", "application/pdf")},
    )
    evidence = uploaded.json()["data"]
    settings: Settings = application.state.settings
    async with session_factory() as session:
        orchestrator = ProcessingOrchestrator(
            session,
            LocalStorage(settings.storage_root),
            HashService(),
            settings,
        )
        first = await orchestrator.create_job(UUID(str(evidence["id"])))
        with pytest.raises(ConflictError):
            await orchestrator.create_job(UUID(str(evidence["id"])))
        await orchestrator.run(first.id)

    second = await client.post(f"/api/v1/evidence/{evidence['id']}/process")
    assert second.status_code == 202
    jobs = await client.get(f"/api/v1/evidence/{evidence['id']}/processing")
    assert jobs.json()["data"]["total"] == 2


@pytest.mark.asyncio
async def test_integrity_mismatch_fails_safely_without_artifacts(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """Tampering produces a safe failure and never replaces the evidence row."""

    client, session_factory, _, application = phase4_client
    case = await create_case(client)
    content = b"%PDF-1.7\noriginal"
    uploaded = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("invoice.pdf", content, "application/pdf")},
    )
    evidence = cast(dict[str, object], uploaded.json()["data"])
    async with session_factory() as session:
        stored = await session.get(Evidence, UUID(str(evidence["id"])))
        assert stored is not None
        stored_path = application.state.settings.storage_root.joinpath(
            *stored.storage_key.split("/")
        )
    stored_path.write_bytes(b"%PDF-1.7\ntampered")

    queued = await client.post(f"/api/v1/evidence/{evidence['id']}/process")
    assert queued.status_code == 202
    jobs = await client.get(f"/api/v1/evidence/{evidence['id']}/processing")
    failed = jobs.json()["data"]["items"][0]
    assert failed["status"] == "FAILED"
    assert failed["error_code"] == "EVIDENCE_INTEGRITY_MISMATCH"
    assert "Traceback" not in (failed["error_message"] or "")

    artifacts = await client.get(f"/api/v1/evidence/{evidence['id']}/artifacts")
    assert artifacts.json()["data"]["total"] == 0


@pytest.mark.asyncio
async def test_processing_rejects_missing_evidence_and_missing_original(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """Processing exposes stable safe errors for unavailable inputs."""

    client, session_factory, _, application = phase4_client
    missing = await client.post(
        "/api/v1/evidence/00000000-0000-0000-0000-000000000099/process"
    )
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    case = await create_case(client)
    uploaded = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("invoice.pdf", b"%PDF-1.7\nmissing", "application/pdf")},
    )
    evidence = uploaded.json()["data"]
    async with session_factory() as session:
        stored = await session.get(Evidence, UUID(str(evidence["id"])))
        assert stored is not None
        application.state.settings.storage_root.joinpath(
            *stored.storage_key.split("/")
        ).unlink()

    unavailable = await client.post(f"/api/v1/evidence/{evidence['id']}/process")
    assert unavailable.status_code == 422
    assert unavailable.json()["error"]["code"] == "EVIDENCE_FILE_MISSING"
