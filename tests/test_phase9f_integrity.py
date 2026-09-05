"""Tests for Phase 9F digital evidence integrity monitoring."""

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
from backend.app.integrity.custody_validator import custody_gaps
from backend.app.integrity.drift import current_fingerprints, detect_drifts
from backend.app.integrity.hash_monitor import custody_hash_mismatch
from backend.app.integrity.policy import CHECK_CODES, IM_ENGINE_VERSION
from backend.app.integrity.service import IntegrityMonitorService
from backend.app.integrity.verifier import verify_case_snapshot
from backend.app.main import create_app
from tests.test_phase3_api import create_case

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260912_0031_add_integrity_monitoring.py"
)


def _snapshot(*, with_evidence: bool = True, bad_custody: bool = False) -> dict:
    if not with_evidence:
        return {
            "evidence": [],
            "custody_by_evidence": {},
            "audit_evidence_ids": [],
            "ai_evidence_ids": [],
            "reports": [],
            "storage_presence": {},
            "observed_sizes": {},
        }
    evidence = [
        {
            "id": "e1",
            "evidence_number": "EV-1",
            "sha256_hash": "abc123",
            "file_size": 10,
            "mime_type": "image/png",
            "storage_key": "evidence/e1.bin",
            "metadata": {"a": 1},
            "created_at": "2026-09-01T00:00:00+00:00",
            "updated_at": "2026-09-01T00:00:00+00:00",
        }
    ]
    custody_hash = "deadbeef" if bad_custody else "abc123"
    return {
        "evidence": evidence,
        "custody_by_evidence": {
            "e1": [
                {
                    "id": "c1",
                    "event_type": "ACQUIRED",
                    "timestamp": "2026-09-01T00:00:00+00:00",
                    "sha256_hash": custody_hash,
                }
            ]
        },
        "audit_evidence_ids": ["e1"],
        "ai_evidence_ids": [],
        "reports": [{"id": "r1"}],
        "storage_presence": {"e1": True},
        "observed_sizes": {"e1": 10},
    }


@pytest_asyncio.fixture
async def phase9f_client(
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
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client, session_factory
    await engine.dispose()


class TestMigration:
    def test_migration_file_and_chain(self) -> None:
        assert MIGRATION_PATH.is_file()
        spec = importlib.util.spec_from_file_location("im_mig", MIGRATION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.revision == "20260912_0031"
        assert module.down_revision == "20260911_0030"


class TestHashAndCustody:
    def test_hash_mismatch(self) -> None:
        assert custody_hash_mismatch("abc", ["abc"]) == []
        assert custody_hash_mismatch("abc", ["zzz"]) == ["zzz"]

    def test_custody_gaps_empty(self) -> None:
        assert custody_gaps([]) == ["No custody events recorded."]

    def test_custody_monotonic(self) -> None:
        issues = custody_gaps(
            [
                {
                    "id": "2",
                    "timestamp": "2026-09-02T00:00:00+00:00",
                    "event_type": "TRANSFERRED",
                },
                {
                    "id": "1",
                    "timestamp": "2026-09-01T00:00:00+00:00",
                    "event_type": "ACQUIRED",
                },
            ]
        )
        assert issues == []


class TestDriftAndVerifier:
    def test_drift_detection(self) -> None:
        evidence = _snapshot()["evidence"]
        fps = current_fingerprints(evidence)
        evidence[0]["metadata"] = {"a": 2}
        drifts = detect_drifts(evidence, fps)
        assert len(drifts) == 1
        assert drifts[0].field_name == "metadata"

    def test_verifier_hash_mismatch_alert(self) -> None:
        checks, alerts, drifts, timeline = verify_case_snapshot(
            _snapshot(bad_custody=True)
        )
        sha = [c for c in checks if c.check_code == "SHA256_CONSISTENCY"]
        assert sha and sha[0].status.value == "FAIL"
        assert any(a.alert_code == "SHA256_CONSISTENCY" for a in alerts)
        assert timeline

    def test_deterministic_ordering(self) -> None:
        a, _, _, _ = verify_case_snapshot(_snapshot())
        b, _, _, _ = verify_case_snapshot(_snapshot())
        assert [c.check_key for c in a] == [c.check_key for c in b]
        codes = [c.check_code for c in a]
        # policy codes appear in non-decreasing order by first occurrence index
        order = {code: i for i, (code, _) in enumerate(CHECK_CODES)}
        idxs = [order[c] for c in codes]
        assert idxs == sorted(idxs)

    def test_empty_case_checks(self) -> None:
        checks, alerts, drifts, _ = verify_case_snapshot(_snapshot(with_evidence=False))
        assert checks
        assert drifts == []


class TestServiceAndApi:
    @pytest.mark.asyncio
    async def test_preview_and_generate(
        self,
        phase9f_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9f_client
        case = await create_case(client)
        preview = await client.get(
            f"/api/v1/cases/{case['id']}/integrity/preview",
        )
        assert preview.status_code == 200
        body = preview.json()["data"]
        assert body["persisted"] is False
        assert body["engine_version"] == IM_ENGINE_VERSION

        created = await client.post(
            f"/api/v1/cases/{case['id']}/integrity-check",
        )
        assert created.status_code == 200
        run = created.json()["data"]
        assert run["persisted"] is True
        assert run["id"] is not None

    @pytest.mark.asyncio
    async def test_api_latest_alerts_drift_history(
        self,
        phase9f_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9f_client
        case = await create_case(client)
        case_id = case["id"]
        created = await client.post(f"/api/v1/cases/{case_id}/integrity-check")
        run_id = created.json()["data"]["id"]

        latest = await client.get(f"/api/v1/cases/{case_id}/integrity/latest")
        assert latest.status_code == 200
        assert latest.json()["data"]["id"] == run_id

        by_id = await client.get(f"/api/v1/integrity/{run_id}")
        assert by_id.status_code == 200

        alerts = await client.get(f"/api/v1/cases/{case_id}/integrity/alerts")
        assert alerts.status_code == 200

        drift = await client.get(f"/api/v1/cases/{case_id}/integrity/drift")
        assert drift.status_code == 200

        history = await client.get(
            f"/api/v1/cases/{case_id}/integrity/history",
        )
        assert history.status_code == 200
        assert history.json()["data"]["total"] >= 1

    @pytest.mark.asyncio
    async def test_preview_does_not_persist(
        self,
        phase9f_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9f_client
        case = await create_case(client)
        await client.get(f"/api/v1/cases/{case['id']}/integrity/preview")
        latest = await client.get(f"/api/v1/cases/{case['id']}/integrity")
        assert latest.status_code == 404

    @pytest.mark.asyncio
    async def test_service_repository_roundtrip(
        self,
        phase9f_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, session_factory = phase9f_client
        case = await create_case(client)
        from uuid import UUID

        case_id = UUID(case["id"])
        async with session_factory() as session:
            service = IntegrityMonitorService(session)
            preview = await service.preview(case_id)
            assert preview.persisted is False
            run = await service.generate(case_id)
            assert run.persisted is True
            again = await service.get_latest(case_id)
            assert again.id == run.id

    @pytest.mark.asyncio
    async def test_second_run_can_detect_drift_baseline(
        self,
        phase9f_client: tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession]],
    ) -> None:
        client, _ = phase9f_client
        case = await create_case(client)
        first = await client.post(
            f"/api/v1/cases/{case['id']}/integrity-check",
        )
        assert first.status_code == 200
        second = await client.post(
            f"/api/v1/cases/{case['id']}/integrity-check",
        )
        assert second.status_code == 200
        # Empty case: no evidence drift, but fingerprints baseline recorded
        assert second.json()["data"]["engine_version"] == IM_ENGINE_VERSION
