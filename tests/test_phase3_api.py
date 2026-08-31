"""Deterministic API tests for Phase 3 case and evidence management."""

import hashlib
from collections.abc import AsyncIterator
from pathlib import Path
from typing import cast
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session, get_storage_service
from backend.app.core.config import Settings
from backend.app.core.exceptions import StorageError
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models import Case, Evidence


@pytest_asyncio.fixture
async def phase3_client(
    tmp_path: Path,
) -> AsyncIterator[
    tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ]
]:
    """Create an isolated API, database, and local storage root."""

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


async def create_case(client: httpx.AsyncClient) -> dict[str, object]:
    """Create one case and return its API data."""

    response = await client.post(
        "/api/v1/cases",
        json={"title": "Evidence preservation test", "priority": "HIGH"},
    )
    assert response.status_code == 201
    return cast(dict[str, object], response.json()["data"])


@pytest.mark.asyncio
async def test_case_lifecycle_and_pagination(
    phase3_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
    ],
) -> None:
    """Cases receive public IDs and support retrieval, listing, and PATCH."""

    client, _, _, _ = phase3_client
    created = await create_case(client)
    assert created["case_number"] == "CASE-000001"
    case_id = created["id"]

    listed = await client.get("/api/v1/cases?limit=10&offset=0")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1

    retrieved = await client.get(f"/api/v1/cases/{case_id}")
    assert retrieved.status_code == 200
    assert retrieved.json()["data"]["title"] == "Evidence preservation test"

    updated = await client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "IN_PROGRESS", "title": "Updated case"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["status"] == "IN_PROGRESS"

    missing = await client.get("/api/v1/cases/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "RESOURCE_NOT_FOUND"


@pytest.mark.asyncio
async def test_evidence_upload_hash_and_custody_relationship(
    phase3_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
    ],
) -> None:
    """Upload persists exact metadata, hash, and initial custody event."""

    client, session_factory, _, application = phase3_client
    case = await create_case(client)
    content = b"%PDF-1.7\npreserved forensic bytes\n"
    response = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("original.pdf", content, "application/pdf")},
    )
    assert response.status_code == 201
    evidence = response.json()["data"]
    assert evidence["evidence_number"] == "EVID-000001"
    expected_hash = hashlib.sha256(content).hexdigest()
    assert evidence["sha256_hash"] == expected_hash
    assert evidence["custody_events"][0]["event_type"] == "EVIDENCE_INGESTED"
    assert evidence["custody_events"][0]["sha256_hash"] == expected_hash

    retrieved = await client.get(f"/api/v1/evidence/{evidence['id']}")
    assert retrieved.status_code == 200
    assert len(retrieved.json()["data"]["custody_events"]) == 1

    listed = await client.get(f"/api/v1/cases/{case['id']}/evidence")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] == 1
    duplicate = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": ("copy.pdf", content, "application/pdf")},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "CONFLICT"

    async with session_factory() as session:
        stored = await session.get(Evidence, UUID(str(evidence["id"])))
        assert stored is not None
        assert stored.case_id == UUID(str(case["id"]))
        assert stored.storage_key.startswith("evidence/")
        stored_path = application.state.settings.storage_root.joinpath(
            *stored.storage_key.split("/")
        )
        assert stored_path.is_file()
        assert await session.get(Case, UUID(str(case["id"]))) is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("filename", "content_type", "content", "expected_code"),
    [
        ("payload.exe", "application/octet-stream", b"MZ", "UNSUPPORTED_FILE_TYPE"),
        ("../unsafe.pdf", "application/pdf", b"%PDF-1.7", "INVALID_FILE"),
        ("empty.pdf", "application/pdf", b"", "INVALID_FILE"),
    ],
)
async def test_evidence_validation_rejects_untrusted_uploads(
    phase3_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
    ],
    filename: str,
    content_type: str,
    content: bytes,
    expected_code: str,
) -> None:
    """Unsupported, unsafe, and empty uploads are rejected consistently."""

    client, _, _, _ = phase3_client
    case = await create_case(client)
    response = await client.post(
        f"/api/v1/cases/{case['id']}/evidence",
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code in {400, 415}
    assert response.json()["error"]["code"] == expected_code


class FailingCommitStorage(LocalStorage):
    """Storage double that fails after staging and before database persistence."""

    async def commit(self, temporary_key: str, storage_key: str) -> None:
        raise StorageError("simulated final storage failure")


@pytest.mark.asyncio
async def test_evidence_ingestion_failure_cleans_staging_and_persists_nothing(
    phase3_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """A final-storage failure leaves no staged object or evidence row."""

    client, session_factory, _, application = phase3_client
    case = await create_case(client)
    settings = application.state.settings
    failing_storage = FailingCommitStorage(settings.storage_root)
    application.dependency_overrides[get_storage_service] = lambda: failing_storage
    try:
        response = await client.post(
            f"/api/v1/cases/{case['id']}/evidence",
            files={"file": ("original.pdf", b"%PDF-1.7\n", "application/pdf")},
        )
    finally:
        application.dependency_overrides.pop(get_storage_service, None)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "STORAGE_UNAVAILABLE"
    staging_root = settings.storage_root / ".tmp"
    assert not staging_root.exists() or not any(staging_root.iterdir())
    async with session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(Evidence)) == 0
