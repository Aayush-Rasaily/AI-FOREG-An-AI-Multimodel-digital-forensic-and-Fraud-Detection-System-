"""Phase 6I end-to-end validation, audit, and production hardening tests."""

from __future__ import annotations

import hashlib
import re
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
from backend.app.application.services.storage import StorageService
from backend.app.case_intelligence.policy import (
    ENGINE_VERSION as CI_ENGINE_VERSION,
)
from backend.app.case_intelligence.policy import (
    POLICY_VERSION as CI_POLICY_VERSION,
)
from backend.app.case_intelligence.service import CaseIntelligenceService
from backend.app.core.config import Settings
from backend.app.core.exceptions import ConflictError, ResourceNotFoundError
from backend.app.fusion.normalization import (
    deduplicate_findings,
    normalize_forensic_finding,
)
from backend.app.fusion.policy import ENGINE_VERSION as FUSION_ENGINE_VERSION
from backend.app.fusion.policy import POLICY_VERSION as FUSION_POLICY_VERSION
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.evidence import Evidence
from backend.app.reporting.policy import ENGINE_VERSION as REPORT_ENGINE_VERSION
from backend.app.reporting.policy import REPORT_VERSION
from backend.app.reporting.service import ReportService
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract

MIGRATION_DIR = Path(__file__).resolve().parents[1] / "backend" / "alembic" / "versions"
EXPECTED_MIGRATION_CHAIN = [
    "20260831_0001",
    "20260831_0002",
    "20260831_0003",
    "20260831_0004",
    "20260831_0005",
    "20260831_0006",
    "20260831_0007",
    "20260831_0008",
    "20260831_0009",
    "20260831_0010",
    "20260831_0011",
    "20260831_0012",
    "20260831_0013",
    "20260901_0014",
    "20260901_0015",
    "20260901_0016",
    "20260901_0017",
    "20260901_0018",
    "20260901_0019",
]

NONDETERMINISTIC_FIELDS = frozenset(
    {
        "generated_at",
        "created_at",
        "started_at",
        "completed_at",
        "id",
        "report_id",
        "analysis_run_id",
        "fusion_run_id",
    }
)


@pytest_asyncio.fixture
async def phase6i_client(
    tmp_path,
) -> AsyncIterator[
    tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
        Settings,
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
        autoflush=False,
    )

    async def database_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    application = create_app(settings)
    application.dependency_overrides[get_db_session] = database_session
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, engine, application, settings
    await engine.dispose()


async def _poll_fusion(client: httpx.AsyncClient, evidence_id: str) -> dict:
    for _ in range(30):
        response = await client.get(
            f"/api/v1/evidence/{evidence_id}/fusion-analysis/latest",
        )
        if response.status_code == 200:
            return response.json()["data"]
    raise AssertionError("Fusion analysis did not complete")


async def _poll_intelligence(client: httpx.AsyncClient, case_id: str) -> dict:
    for _ in range(30):
        response = await client.get(
            f"/api/v1/cases/{case_id}/intelligence/latest",
        )
        if response.status_code == 200:
            return response.json()["data"]
    raise AssertionError("Case intelligence did not complete")


async def _poll_report(client: httpx.AsyncClient, case_id: str) -> dict:
    for _ in range(30):
        response = await client.get(f"/api/v1/cases/{case_id}/reports/latest")
        if response.status_code == 200:
            payload = response.json()["data"]
            if payload["status"] == "COMPLETED":
                return payload
    raise AssertionError("Report generation did not complete")


async def _run_full_pipeline(
    client: httpx.AsyncClient,
    *,
    pdf_content: bytes | None = None,
) -> dict[str, object]:
    case = await create_case(client)
    content = pdf_content or make_text_pdf()
    original_hash = hashlib.sha256(content).hexdigest()
    evidence = await process_and_extract(
        client,
        case["id"],
        "pipeline.pdf",
        content,
        "application/pdf",
    )
    await client.post(f"/api/v1/evidence/{evidence['id']}/fusion-analysis")
    fusion = await _poll_fusion(client, str(evidence["id"]))
    await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    intelligence = await _poll_intelligence(client, case["id"])
    await client.post(f"/api/v1/cases/{case['id']}/reports")
    report = await _poll_report(client, case["id"])
    return {
        "case": case,
        "evidence": evidence,
        "original_hash": original_hash,
        "fusion": fusion,
        "intelligence": intelligence,
        "report": report,
    }


def _strip_nondeterministic(value: object) -> object:
    if isinstance(value, dict):
        return {
            key: _strip_nondeterministic(item)
            for key, item in value.items()
            if key not in NONDETERMINISTIC_FIELDS
        }
    if isinstance(value, list):
        return [_strip_nondeterministic(item) for item in value]
    return value


@pytest.mark.asyncio
async def test_end_to_end_pipeline_traceable(phase6i_client) -> None:
    """Validate the complete evidence-to-report lifecycle."""

    client, _, _, _, _ = phase6i_client
    result = await _run_full_pipeline(client)
    assert result["fusion"]["engine_version"] == FUSION_ENGINE_VERSION
    assert result["intelligence"]["engine_version"] == CI_ENGINE_VERSION
    assert result["report"]["report_version"] == REPORT_VERSION
    assert result["report"]["has_pdf"] is True
    assert result["original_hash"] in result["report"]["evidence_hashes"]


@pytest.mark.asyncio
async def test_evidence_hash_preserved_through_pipeline(phase6i_client) -> None:
    """Original SHA-256 must remain unchanged after processing and analysis."""

    client, session_factory, _, _, _ = phase6i_client
    content = make_text_pdf()
    original_hash = hashlib.sha256(content).hexdigest()
    result = await _run_full_pipeline(client, pdf_content=content)
    async with session_factory() as session:
        evidence = await session.get(Evidence, UUID(str(result["evidence"]["id"])))
        assert evidence is not None
        assert evidence.sha256_hash == original_hash


@pytest.mark.asyncio
async def test_provenance_chain_references(phase6i_client) -> None:
    """Final report provenance must link to fusion and evidence hashes."""

    client, _, _, _, _ = phase6i_client
    result = await _run_full_pipeline(client)
    provenance = result["report"]["provenance"]
    assert provenance.get("case_id") == result["case"]["id"]
    assert result["original_hash"] in provenance.get("evidence_hashes", [])
    assert provenance.get("fusion_run_ids")
    assert provenance.get("report_sha256") == result["report"]["pdf_sha256"]
    explainability = result["report"]["explainability"]
    assert "confidence_note" in explainability
    assert "Risk" in explainability["confidence_note"]


def test_fusion_normalization_is_deterministic() -> None:
    """Identical forensic inputs must normalize identically."""

    from backend.app.forensics.models import Severity

    evidence_id = uuid4()
    finding_id = uuid4()
    first = normalize_forensic_finding(
        evidence_id=evidence_id,
        finding_id=finding_id,
        detector="metadata",
        category="METADATA",
        severity=Severity.LOW,
        confidence=0.5,
        description="test",
        explanation="test",
    )
    second = normalize_forensic_finding(
        evidence_id=evidence_id,
        finding_id=finding_id,
        detector="metadata",
        category="METADATA",
        severity=Severity.LOW,
        confidence=0.5,
        description="test",
        explanation="test",
    )
    assert first.finding_id == second.finding_id
    assert deduplicate_findings((first, second)) == (first,)


@pytest.mark.asyncio
async def test_report_snapshot_stable_excluding_timestamps(phase6i_client) -> None:
    """Report section content must be stable aside from known variable fields."""

    client, _, _, _, _ = phase6i_client
    first = await _run_full_pipeline(client)
    second = await _run_full_pipeline(client)
    first_sections = _strip_nondeterministic(first["report"]["content"]["sections"])
    second_sections = _strip_nondeterministic(second["report"]["content"]["sections"])
    assert first_sections["executive_summary"] == second_sections["executive_summary"]


def test_version_constants_documented() -> None:
    """Engine and policy versions must be explicit across phases."""

    assert FUSION_ENGINE_VERSION == "1.0"
    assert FUSION_POLICY_VERSION == "1.0"
    assert CI_ENGINE_VERSION == "1.0"
    assert CI_POLICY_VERSION == "1.0"
    assert REPORT_ENGINE_VERSION == "1.0"
    assert REPORT_VERSION == "1.0"


@pytest.mark.asyncio
async def test_active_report_duplicate_raises_conflict(phase6i_client) -> None:
    """Active report jobs must reject duplicate queue requests."""

    client, session_factory, _, _, settings = phase6i_client
    case = await create_case(client)
    storage: StorageService = LocalStorage(settings.storage_root)
    hash_service = HashService()
    async with session_factory() as session:
        service = ReportService(session, storage, hash_service, settings)
        await service.create_report(UUID(case["id"]))
        with pytest.raises(ConflictError):
            await service.create_report(UUID(case["id"]))


@pytest.mark.asyncio
async def test_active_case_intelligence_duplicate_conflict(
    phase6i_client,
) -> None:
    """Active case intelligence jobs must reject duplicate queue requests."""

    client, session_factory, _, _, settings = phase6i_client
    case = await create_case(client)
    storage: StorageService = LocalStorage(settings.storage_root)
    hash_service = HashService()
    async with session_factory() as session:
        service = CaseIntelligenceService(session, storage, hash_service, settings)
        await service.create_analysis(UUID(case["id"]))
        with pytest.raises(ConflictError):
            await service.create_analysis(UUID(case["id"]))


@pytest.mark.asyncio
async def test_repeat_fusion_preserves_history(phase6i_client) -> None:
    """Repeat fusion must create auditable history without corrupting evidence."""

    client, _, _, _, _ = phase6i_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "repeat.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    first = await client.post(f"/api/v1/evidence/{evidence['id']}/fusion-analysis")
    assert first.status_code == 202
    await _poll_fusion(client, str(evidence["id"]))
    second = await client.post(f"/api/v1/evidence/{evidence['id']}/fusion-analysis")
    assert second.status_code == 202
    await _poll_fusion(client, str(evidence["id"]))
    history = await client.get(f"/api/v1/evidence/{evidence['id']}/fusion-analysis")
    assert history.status_code == 200
    assert history.json()["data"]["total"] >= 2


@pytest.mark.asyncio
async def test_missing_case_returns_structured_404(phase6i_client) -> None:
    """Missing resources must return structured API errors without tracebacks."""

    client, _, _, _, _ = phase6i_client
    missing = UUID("00000000-0000-0000-0000-000000000701")
    for path in (
        f"/api/v1/cases/{missing}/intelligence",
        f"/api/v1/cases/{missing}/reports",
    ):
        response = await client.post(path)
        assert response.status_code == 404
        body = response.json()
        assert body["success"] is False
        assert "traceback" not in response.text.lower()


@pytest.mark.asyncio
async def test_malformed_uuid_returns_422(phase6i_client) -> None:
    """Malformed IDs must not crash the API."""

    client, _, _, _, _ = phase6i_client
    response = await client.get("/api/v1/reports/not-a-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_report_without_intelligence_still_generates(phase6i_client) -> None:
    """Report generation must handle missing case intelligence safely."""

    client, _, _, _, _ = phase6i_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "no-intel.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/reports")
    report = await _poll_report(client, case["id"])
    sections = report["content"]["sections"]
    limitations = sections["confidence_and_limitations"]["limitations"]
    assert any("Phase 6G" in item for item in limitations)


@pytest.mark.asyncio
async def test_risk_and_confidence_are_separate_in_report(phase6i_client) -> None:
    """Reports must not equate risk score with confidence percentage."""

    client, _, _, _, _ = phase6i_client
    result = await _run_full_pipeline(client)
    note = result["report"]["explainability"]["confidence_note"]
    assert "Risk" in note
    assert "confidence" in note.lower()
    summary = result["report"]["executive_summary"]
    assert "risk_score" in summary
    assert "confidence" in summary


def test_alembic_migration_chain_is_linear() -> None:
    """Migration revisions must form a single chain through Phase 6H."""

    revisions: dict[str, str | None] = {}
    for path in sorted(MIGRATION_DIR.glob("*.py")):
        if path.name.startswith("__"):
            continue
        text = path.read_text(encoding="utf-8")
        revision_match = re.search(r'^revision = "([^"]+)"', text, re.MULTILINE)
        down_match = re.search(r'^down_revision = ("[^"]+"|None)', text, re.MULTILINE)
        assert revision_match and down_match, f"Invalid migration file: {path.name}"
        down = down_match.group(1)
        revisions[revision_match.group(1)] = None if down == "None" else down.strip('"')

    head = EXPECTED_MIGRATION_CHAIN[-1]
    chain: list[str] = []
    current: str | None = head
    while current is not None:
        chain.append(current)
        current = revisions[current]
    chain.reverse()
    assert chain == EXPECTED_MIGRATION_CHAIN


def test_report_explainability_does_not_fabricate_findings() -> None:
    """Explainability must not invent supporting findings without source data."""

    from backend.app.reporting.explainability import build_explainability

    snapshot = {
        "case_intelligence": None,
        "fusion_snapshots": [],
        "evidence": [
            {
                "evidence_number": "EVID-001",
                "coverage_status": "unavailable",
            }
        ],
    }
    result = build_explainability(snapshot)
    assert result["supporting_findings"] == []
    assert any("unavailable" in item.lower() for item in result["limitations"])


@pytest.mark.asyncio
async def test_download_rejects_incomplete_report(phase6i_client) -> None:
    """PDF download must not be available for incomplete reports."""

    client, session_factory, _, _, settings = phase6i_client
    case = await create_case(client)
    storage: StorageService = LocalStorage(settings.storage_root)
    hash_service = HashService()
    async with session_factory() as session:
        service = ReportService(session, storage, hash_service, settings)
        queued = await service.create_report(UUID(case["id"]))
        with pytest.raises(ResourceNotFoundError):
            await service.get_pdf_storage_key(queued.id)
