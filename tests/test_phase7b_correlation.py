"""Tests for Phase 7B cross-evidence correlation engine."""

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
from backend.app.correlation.engine import CorrelationEngine
from backend.app.correlation.matchers import extract_emails, extract_phones
from backend.app.correlation.models import CorrelationType
from backend.app.correlation.policy import (
    ENGINE_VERSION,
    POLICY_VERSION,
    SCORE_SAME_HASH,
)
from backend.app.correlation.provenance import canonical_pair, correlation_key
from backend.app.correlation.repository import CorrelationRepository
from backend.app.correlation.scoring import filename_similarity, score_for
from backend.app.correlation.service import CorrelationService
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.case import Case
from backend.app.models.correlation import (
    CorrelationAnalysisRun,
    EvidenceCorrelationRecord,
)
from backend.app.models.evidence import Evidence
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract

MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "backend"
    / "alembic"
    / "versions"
    / "20260901_0015_add_correlation.py"
)


@pytest_asyncio.fixture
async def phase7b_client(
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


async def _poll_latest(
    client: httpx.AsyncClient,
    case_id: str,
) -> dict:
    for _ in range(40):
        response = await client.get(f"/api/v1/cases/{case_id}/correlations/latest")
        if response.status_code == 200:
            payload = response.json()["data"]
            if payload["status"] in {"SUCCEEDED", "FAILED"}:
                return payload
        await asyncio.sleep(0.05)
    raise AssertionError("Correlation analysis did not complete in time.")


def test_policy_versions_documented() -> None:
    assert ENGINE_VERSION == "1.0"
    assert POLICY_VERSION == "1.0"
    assert score_for(CorrelationType.SAME_HASH) == SCORE_SAME_HASH


def test_canonical_pair_and_duplicate_key() -> None:
    left = UUID("00000000-0000-0000-0000-000000000002")
    right = UUID("00000000-0000-0000-0000-000000000001")
    a, b = canonical_pair(left, right)
    assert str(a) < str(b)
    assert correlation_key(left, right, "same_hash") == correlation_key(
        right,
        left,
        "same_hash",
    )


def test_email_and_phone_extraction() -> None:
    text = "Contact alice@example.com or +1-555-123-4567 about INV-1001."
    assert "alice@example.com" in extract_emails(text)
    phones = extract_phones(text)
    assert any(phone.endswith("1234567") for phone in phones)


def test_filename_similarity_scoring() -> None:
    assert filename_similarity("invoice_final.pdf", "invoice_draft.pdf") > 0.4
    assert filename_similarity("a.pdf", "zzz.bin") < 0.5


def test_scoring_is_deterministic() -> None:
    assert score_for(CorrelationType.SAME_EMAIL) == 0.98
    assert score_for(CorrelationType.SIMILAR_FILENAME) == 0.45


@pytest.mark.asyncio
async def test_empty_case_correlation(phase7b_client) -> None:
    client, _, _, _ = phase7b_client
    case = await create_case(client)
    created = await client.post(f"/api/v1/cases/{case['id']}/correlations")
    assert created.status_code == 202
    latest = await _poll_latest(client, case["id"])
    assert latest["status"] == "SUCCEEDED"
    assert latest["correlation_count"] == 0


@pytest.mark.asyncio
async def test_one_evidence_no_pairs(phase7b_client) -> None:
    client, _, _, _ = phase7b_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "solo.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/correlations")
    latest = await _poll_latest(client, case["id"])
    assert latest["status"] == "SUCCEEDED"
    assert latest["correlation_count"] == 0


def test_identical_hashes_correlation_matching() -> None:
    from backend.app.correlation.matchers import EvidenceSignals

    left_id = uuid4()
    right_id = uuid4()
    shared = "a" * 64
    signals = [
        EvidenceSignals(
            evidence_id=left_id,
            evidence_number="EVID-1",
            sha256_hash=shared,
            original_filename="a.pdf",
            mime_type="application/pdf",
        ),
        EvidenceSignals(
            evidence_id=right_id,
            evidence_number="EVID-2",
            sha256_hash=shared,
            original_filename="b.pdf",
            mime_type="application/pdf",
        ),
    ]
    results = CorrelationEngine()._match_exact_groups(
        uuid4(),
        signals,
        CorrelationType.SAME_HASH,
        lambda item: {item.sha256_hash},
        "sha256_hash",
    )
    assert len(results) == 1
    assert results[0].score == 1.0
    assert results[0].correlation_type == CorrelationType.SAME_HASH
    a, b = canonical_pair(left_id, right_id)
    assert results[0].left_evidence_id == a
    assert results[0].right_evidence_id == b


@pytest.mark.asyncio
async def test_multiple_evidence_and_api(phase7b_client) -> None:
    client, _, _, _ = phase7b_client
    case = await create_case(client)
    for index in range(2):
        await process_and_extract(
            client,
            case["id"],
            f"report-{index}.pdf",
            make_text_pdf() + f"-{index}".encode(),
            "application/pdf",
        )
    created = await client.post(f"/api/v1/cases/{case['id']}/correlations")
    assert created.status_code == 202
    latest = await _poll_latest(client, case["id"])
    assert latest["status"] == "SUCCEEDED"
    listed = await client.get(f"/api/v1/cases/{case['id']}/correlations")
    assert listed.status_code == 200
    assert listed.json()["data"]["total"] >= 1
    if latest["correlations"]:
        item = latest["correlations"][0]
        detail = await client.get(f"/api/v1/correlations/{item['id']}")
        assert detail.status_code == 200
        evidence_list = await client.get(
            f"/api/v1/evidence/{item['left_evidence_id']}/correlations"
        )
        assert evidence_list.status_code == 200


@pytest.mark.asyncio
async def test_similar_filename_correlation(phase7b_client) -> None:
    client, _, _, _ = phase7b_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "invoice_final.pdf",
        make_text_pdf() + b"-a",
        "application/pdf",
    )
    await process_and_extract(
        client,
        case["id"],
        "invoice_draft.pdf",
        make_text_pdf() + b"-b",
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/correlations")
    latest = await _poll_latest(client, case["id"])
    types = {item["correlation_type"] for item in latest["correlations"]}
    assert "similar_filename" in types


@pytest.mark.asyncio
async def test_ocr_email_phone_correlation(phase7b_client) -> None:
    client, session_factory, _, _ = phase7b_client
    case = await create_case(client)
    first = await process_and_extract(
        client,
        case["id"],
        "alpha.pdf",
        make_text_pdf() + b"-alpha",
        "application/pdf",
    )
    second = await process_and_extract(
        client,
        case["id"],
        "beta.pdf",
        make_text_pdf() + b"-beta",
        "application/pdf",
    )
    from backend.app.extraction.models import ExtractionSourceType, ExtractionType
    from backend.app.models.extraction import ExtractionRecord

    async with session_factory() as session:
        for evidence_id, suffix in (
            (first["id"], "a"),
            (second["id"], "b"),
        ):
            session.add(
                ExtractionRecord(
                    id=uuid4(),
                    evidence_id=UUID(str(evidence_id)),
                    extraction_type=ExtractionType.TEXT,
                    source_type=ExtractionSourceType.ORIGINAL,
                    source_identifier=f"ocr-{suffix}",
                    content=(
                        "Contact shared@example.com phone 555-987-6543 "
                        f"INV-2026001 variant {suffix}"
                    ),
                    method="test",
                    version="1.0",
                    metadata_json={},
                )
            )
        await session.commit()

    await client.post(f"/api/v1/cases/{case['id']}/correlations")
    latest = await _poll_latest(client, case["id"])
    types = {item["correlation_type"] for item in latest["correlations"]}
    assert "same_email" in types
    assert "same_phone" in types
    assert "same_document" in types or "shared_identifier" in types
    email_item = next(
        item
        for item in latest["correlations"]
        if item["correlation_type"] == "same_email"
    )
    assert "provenance" in email_item
    assert email_item["score"] == 0.98


@pytest.mark.asyncio
async def test_qr_and_gps_correlation(phase7b_client) -> None:
    client, session_factory, _, _ = phase7b_client
    case = await create_case(client)
    first = await process_and_extract(
        client,
        case["id"],
        "qr-a.pdf",
        make_text_pdf() + b"-qr-a",
        "application/pdf",
    )
    second = await process_and_extract(
        client,
        case["id"],
        "qr-b.pdf",
        make_text_pdf() + b"-qr-b",
        "application/pdf",
    )
    from backend.app.extraction.models import ExtractionSourceType, ExtractionType
    from backend.app.models.extraction import ExtractionRecord

    async with session_factory() as session:
        for evidence_id in (first["id"], second["id"]):
            evidence = await session.get(Evidence, UUID(str(evidence_id)))
            assert evidence is not None
            evidence.metadata_json = {
                **evidence.metadata_json,
                "exif": {"gps": {"latitude": "12.34", "longitude": "56.78"}},
            }
            session.add(
                ExtractionRecord(
                    id=uuid4(),
                    evidence_id=UUID(str(evidence_id)),
                    extraction_type=ExtractionType.QR_CODE,
                    source_type=ExtractionSourceType.ORIGINAL,
                    source_identifier="qr",
                    content="https://example.com/pay/ABC",
                    method="test",
                    version="1.0",
                    metadata_json={},
                )
            )
        await session.commit()

    await client.post(f"/api/v1/cases/{case['id']}/correlations")
    latest = await _poll_latest(client, case["id"])
    types = {item["correlation_type"] for item in latest["correlations"]}
    assert "same_qr" in types
    assert "same_location" in types


@pytest.mark.asyncio
async def test_repeat_generation_and_duplicate_prevention(phase7b_client) -> None:
    client, session_factory, _, application = phase7b_client
    case = await create_case(client)
    first = await client.post(f"/api/v1/cases/{case['id']}/correlations")
    assert first.status_code == 202
    await _poll_latest(client, case["id"])
    second = await client.post(f"/api/v1/cases/{case['id']}/correlations")
    assert second.status_code == 202
    await _poll_latest(client, case["id"])
    listed = await client.get(f"/api/v1/cases/{case['id']}/correlations")
    assert listed.json()["data"]["total"] >= 2

    settings = application.state.settings
    async with session_factory() as session:
        service = CorrelationService(
            session=session,
            storage=LocalStorage(settings.storage_root),
            hash_service=HashService(),
            settings=settings,
        )
        await service.create_analysis(UUID(str(case["id"])))
        with pytest.raises(ConflictError):
            await service.create_analysis(UUID(str(case["id"])))


@pytest.mark.asyncio
async def test_repository_and_migration(phase7b_client) -> None:
    client, session_factory, _, _ = phase7b_client
    case = await create_case(client)
    created = await client.post(f"/api/v1/cases/{case['id']}/correlations")
    run_id = created.json()["data"]["id"]
    await _poll_latest(client, case["id"])
    async with session_factory() as session:
        repository = CorrelationRepository(session)
        latest = await repository.get_latest_for_case(UUID(str(case["id"])))
        assert latest is not None
        assert str(latest.id) == run_id
        await repository.delete_run(UUID(str(run_id)))
        await session.commit()
        assert await repository.get_run(UUID(str(run_id))) is None

    spec = importlib.util.spec_from_file_location("migration_0015", MIGRATION_PATH)
    assert spec and spec.loader
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert migration.revision == "20260901_0015"
    assert migration.down_revision == "20260901_0014"


@pytest.mark.asyncio
async def test_engine_deterministic_ordering(phase7b_client) -> None:
    client, session_factory, _, _ = phase7b_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "shared_name_one.pdf",
        make_text_pdf() + b"-1",
        "application/pdf",
    )
    await process_and_extract(
        client,
        case["id"],
        "shared_name_two.pdf",
        make_text_pdf() + b"-2",
        "application/pdf",
    )
    async with session_factory() as session:
        case_row = await session.get(Case, UUID(str(case["id"])))
        assert case_row is not None
        first = await CorrelationEngine().build(session, case_row)
        second = await CorrelationEngine().build(session, case_row)
        assert [item.correlation_id for item in first.correlations] == [
            item.correlation_id for item in second.correlations
        ]


def test_models_importable() -> None:
    assert CorrelationAnalysisRun.__tablename__ == "correlation_analysis_runs"
    assert EvidenceCorrelationRecord.__tablename__ == "evidence_correlations"
