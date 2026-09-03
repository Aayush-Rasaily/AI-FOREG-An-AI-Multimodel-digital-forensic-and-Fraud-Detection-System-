"""Tests for Phase 7E audit, compliance, and evidence integrity."""

from __future__ import annotations

import importlib.util
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
from backend.app.audit.events import (
    build_audit_event,
    compute_integrity_hash,
)
from backend.app.audit.policy import ENGINE_VERSION, POLICY_VERSION
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260901_0018_add_audit_framework.py"
)


@pytest_asyncio.fixture
async def phase7e_client(
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


async def _record_event(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    operation: str = "case.created",
    category: str = "case",
    case_id: str | None = None,
) -> str:
    """Record one audit event directly via the recorder."""
    from uuid import UUID

    from backend.app.audit.recorder import AuditRecorder

    async with session_factory() as session:
        recorder = AuditRecorder(session)
        event_id = await recorder.record(
            operation=operation,
            category=category,
            case_id=UUID(case_id) if case_id else None,
        )
        await session.commit()
        return str(event_id)


class TestEventRecording:
    @pytest.mark.asyncio
    async def test_record_and_list_events(
        self,
        phase7e_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, session_factory, _, _ = phase7e_client
        case = await create_case(client)
        case_id = str(case["id"])

        await _record_event(
            session_factory,
            operation="case.created",
            category="case",
            case_id=case_id,
        )
        await _record_event(
            session_factory,
            operation="evidence.uploaded",
            category="evidence",
            case_id=case_id,
        )

        resp = await client.get(
            f"/api/v1/cases/{case_id}/audit",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_get_single_event(
        self,
        phase7e_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, session_factory, _, _ = phase7e_client
        event_id = await _record_event(session_factory)
        resp = await client.get(f"/api/v1/audit/{event_id}")
        assert resp.status_code == 200
        event = resp.json()["data"]
        assert event["operation"] == "case.created"
        assert event["integrity_hash"]
        assert len(event["integrity_hash"]) == 64


class TestChecksumAndIntegrity:
    def test_integrity_hash_deterministic(self) -> None:
        h1 = compute_integrity_hash(
            audit_id="a1",
            timestamp="2026-01-01T00:00:00",
            operation="case.created",
            case_id="c1",
            evidence_id=None,
            sha256_checksum=None,
            previous_state=None,
            new_state={"title": "T"},
        )
        h2 = compute_integrity_hash(
            audit_id="a1",
            timestamp="2026-01-01T00:00:00",
            operation="case.created",
            case_id="c1",
            evidence_id=None,
            sha256_checksum=None,
            previous_state=None,
            new_state={"title": "T"},
        )
        assert h1 == h2
        assert len(h1) == 64

    def test_build_audit_event_has_all_fields(self) -> None:
        event = build_audit_event(
            operation="evidence.uploaded",
            category="evidence",
        )
        assert event["id"]
        assert event["timestamp"]
        assert event["integrity_hash"]
        assert event["engine_version"] == ENGINE_VERSION
        assert event["policy_version"] == POLICY_VERSION

    @pytest.mark.asyncio
    async def test_verify_case_integrity(
        self,
        phase7e_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, *_ = phase7e_client
        case = await create_case(client)
        case_id = str(case["id"])
        pdf_bytes = make_text_pdf()
        await process_and_extract(
            client,
            case_id,
            "doc.pdf",
            pdf_bytes,
            "application/pdf",
        )

        resp = await client.post(
            f"/api/v1/audit/verify?case_id={case_id}",
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["overall_status"] == "VERIFIED"
        assert data["verified_count"] >= 1


class TestFiltering:
    @pytest.mark.asyncio
    async def test_filter_by_operation(
        self,
        phase7e_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, session_factory, _, _ = phase7e_client
        await _record_event(
            session_factory,
            operation="case.created",
            category="case",
        )
        await _record_event(
            session_factory,
            operation="evidence.uploaded",
            category="evidence",
        )
        resp = await client.get(
            "/api/v1/audit?operation=case.created",
        )
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert all(
            i["operation"] == "case.created" for i in items
        )


class TestExport:
    @pytest.mark.asyncio
    async def test_export_json(
        self,
        phase7e_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, session_factory, _, _ = phase7e_client
        await _record_event(session_factory)
        resp = await client.get("/api/v1/audit/export")
        assert resp.status_code == 200
        data = resp.json()
        assert "audit_events" in data
        assert data["total"] >= 1
        assert "X-Audit-Checksum" in resp.headers


class TestDeterministicOrdering:
    @pytest.mark.asyncio
    async def test_events_ordered_by_timestamp(
        self,
        phase7e_client: tuple[
            httpx.AsyncClient,
            async_sessionmaker[AsyncSession],
            AsyncEngine,
            FastAPI,
        ],
    ) -> None:
        client, session_factory, _, _ = phase7e_client
        for i in range(5):
            await _record_event(
                session_factory,
                operation=f"event.{i}",
                category="system",
            )
        resp = await client.get("/api/v1/audit?limit=10")
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        timestamps = [i["timestamp"] for i in items]
        assert timestamps == sorted(timestamps, reverse=True)


class TestMigration:
    def test_migration_exists(self) -> None:
        assert MIGRATION_PATH.exists()

    def test_migration_chain(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "m0018", MIGRATION_PATH,
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        assert mod.revision == "20260901_0018"
        assert mod.down_revision == "20260901_0017"
