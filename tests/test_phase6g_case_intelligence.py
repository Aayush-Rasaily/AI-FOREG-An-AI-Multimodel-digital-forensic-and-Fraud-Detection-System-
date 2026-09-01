"""Tests for Phase 6G case-level forensic intelligence."""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
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
from backend.app.case_intelligence.conflicts import detect_case_conflicts
from backend.app.case_intelligence.consistency import _metadata_timestamp_conflicts
from backend.app.case_intelligence.coverage import compute_coverage
from backend.app.case_intelligence.models import (
    CaseConflictType,
    EvidenceCoverageStatus,
    EvidenceParticipation,
    RelationshipType,
)
from backend.app.case_intelligence.policy import (
    ENGINE_VERSION,
    POLICY_VERSION,
    _case_confidence,
    _case_risk_score,
    _case_verdict,
)
from backend.app.case_intelligence.relationships import (
    _deduplicate_relationships,
    _duplicate_hash_relationships,
)
from backend.app.core.config import Settings
from backend.app.fusion.models import FusionVerdict
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.models.case_intelligence import CaseIntelligenceRun
from backend.app.models.fusion import FusionAnalysisRun
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract


def _participation(
    *,
    evidence_id: UUID | None = None,
    evidence_number: str = "EVID-TEST",
    evidence_hash: str = "a" * 64,
    verdict: FusionVerdict | None = None,
    risk_score: float | None = None,
    confidence: float | None = None,
    coverage_status: EvidenceCoverageStatus = EvidenceCoverageStatus.ANALYZED,
    fusion_completed_at: datetime | None = None,
) -> EvidenceParticipation:
    evidence_id = evidence_id or uuid4()
    return EvidenceParticipation(
        evidence_id=evidence_id,
        evidence_number=evidence_number,
        evidence_type="document",
        evidence_hash=evidence_hash,
        evidence_status="ANALYZED",
        coverage_status=coverage_status,
        fusion_run_id=uuid4() if verdict else None,
        fusion_verdict=verdict,
        risk_score=risk_score,
        confidence=confidence,
        supporting_finding_ids=(),
        contradictory_finding_ids=(),
        conflicts_count=0,
        participating_modalities=("forensics",),
        unavailable_modalities=(),
        fusion_engine_version="1.0",
        fusion_policy_version="1.0",
        fusion_completed_at=fusion_completed_at or datetime.now(UTC),
    )


@pytest_asyncio.fixture
async def phase6g_client(
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


def test_empty_case_coverage() -> None:
    coverage = compute_coverage((), open_conflicts=0)
    assert coverage.total_evidence == 0
    assert coverage.not_analyzed == 0


def test_single_evidence_coverage() -> None:
    participation = _participation(verdict=FusionVerdict.SUSPICIOUS)
    coverage = compute_coverage((participation,), open_conflicts=0)
    assert coverage.total_evidence == 1
    assert coverage.analyzed == 1
    assert coverage.supporting_evidence == 1


def test_mixed_verdict_coverage() -> None:
    participations = (
        _participation(verdict=FusionVerdict.GENUINE),
        _participation(verdict=FusionVerdict.POTENTIAL_FRAUD),
        _participation(
            verdict=None,
            coverage_status=EvidenceCoverageStatus.NOT_ANALYZED,
        ),
    )
    coverage = compute_coverage(participations, open_conflicts=1)
    assert coverage.total_evidence == 3
    assert coverage.not_analyzed == 1
    assert coverage.supporting_evidence == 1
    assert coverage.contradictory_evidence == 1


def test_case_risk_not_averaged_blindly() -> None:
    low = _participation(
        verdict=FusionVerdict.SUSPICIOUS,
        risk_score=10.0,
        confidence=0.2,
    )
    high = _participation(
        verdict=FusionVerdict.POTENTIAL_FRAUD,
        risk_score=90.0,
        confidence=0.95,
    )
    low_score = _case_risk_score((low,), ())
    high_score = _case_risk_score((high,), ())
    assert low_score is not None
    assert high_score is not None
    assert high_score > low_score


def test_unavailable_evidence_does_not_force_fraud_verdict() -> None:
    participations = (
        _participation(
            verdict=None,
            coverage_status=EvidenceCoverageStatus.UNAVAILABLE,
        ),
    )
    coverage = compute_coverage(participations, open_conflicts=0)
    verdict = _case_verdict(participations, (), coverage)
    assert verdict in {
        FusionVerdict.UNAVAILABLE,
        FusionVerdict.INSUFFICIENT_EVIDENCE,
        FusionVerdict.INCONCLUSIVE,
    }


def test_inconclusive_not_treated_as_fraud() -> None:
    participations = (
        _participation(
            verdict=FusionVerdict.INCONCLUSIVE,
            coverage_status=EvidenceCoverageStatus.INCONCLUSIVE,
        ),
    )
    coverage = compute_coverage(participations, open_conflicts=0)
    verdict = _case_verdict(participations, (), coverage)
    assert verdict != FusionVerdict.POTENTIAL_FRAUD


@pytest.mark.asyncio
async def test_api_missing_case_returns_404(phase6g_client) -> None:
    client, _, _, _ = phase6g_client
    missing = UUID("00000000-0000-0000-0000-000000000404")
    response = await client.post(f"/api/v1/cases/{missing}/intelligence")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_case_intelligence_success(phase6g_client) -> None:
    client, session_factory, _, _ = phase6g_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "case-doc.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    fusion_queue = await client.post(
        f"/api/v1/evidence/{evidence['id']}/fusion-analysis",
    )
    assert fusion_queue.status_code == 202
    for _ in range(30):
        fusion_latest = await client.get(
            f"/api/v1/evidence/{evidence['id']}/fusion-analysis/latest",
        )
        if fusion_latest.status_code == 200:
            break
    queue = await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    assert queue.status_code == 202
    latest = None
    for _ in range(30):
        latest = await client.get(
            f"/api/v1/cases/{case['id']}/intelligence/latest",
        )
        if latest.status_code == 200:
            break
    assert latest is not None
    assert latest.status_code == 200
    payload = latest.json()["data"]
    assert payload["case_id"] == case["id"]
    assert "coverage" in payload
    assert "participations" in payload


@pytest.mark.asyncio
async def test_api_timeline_endpoint(phase6g_client) -> None:
    client, _, _, _ = phase6g_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "timeline.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/intelligence/latest")
        if latest.status_code == 200:
            break
    timeline = await client.get(f"/api/v1/cases/{case['id']}/timeline")
    assert timeline.status_code == 200
    assert isinstance(timeline.json()["data"], list)


@pytest.mark.asyncio
async def test_repeat_analysis_allowed(phase6g_client) -> None:
    client, _, _, _ = phase6g_client
    case = await create_case(client)
    first = await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    assert first.status_code == 202
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/intelligence/latest")
        if latest.status_code == 200:
            break
    second = await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    assert second.status_code == 202


def test_case_intelligence_models_importable() -> None:
    assert CaseIntelligenceRun.__tablename__ == "case_intelligence_runs"
    assert FusionAnalysisRun.__tablename__ == "fusion_analysis_runs"


def test_duplicate_hash_relationship_detection() -> None:
    left_id = uuid4()
    right_id = uuid4()
    shared_hash = "c" * 64
    participations = (
        _participation(evidence_id=left_id, evidence_hash=shared_hash),
        _participation(evidence_id=right_id, evidence_hash=shared_hash),
    )
    relationships = _duplicate_hash_relationships(participations)
    assert len(relationships) == 1
    assert relationships[0].relationship_type == RelationshipType.DUPLICATE_HASH
    assert relationships[0].confidence == 1.0


def test_verdict_disagreement_conflict() -> None:
    participations = (
        _participation(verdict=FusionVerdict.GENUINE),
        _participation(verdict=FusionVerdict.SUSPICIOUS),
    )
    conflicts = detect_case_conflicts(participations, ())
    assert any(
        conflict.conflict_type == CaseConflictType.VERDICT_DISAGREEMENT
        for conflict in conflicts
    )


def test_case_confidence_averages_analyzed_evidence() -> None:
    participations = (
        _participation(confidence=0.6),
        _participation(confidence=0.8),
        _participation(
            confidence=0.1,
            coverage_status=EvidenceCoverageStatus.NOT_ANALYZED,
            verdict=None,
        ),
    )
    assert _case_confidence(participations) == 0.7


def test_temporal_inconsistency_when_timestamps_diverge() -> None:
    early = datetime(2026, 1, 1, tzinfo=UTC)
    late = datetime(2026, 1, 5, tzinfo=UTC)
    participations = (
        _participation(
            evidence_id=uuid4(),
            verdict=FusionVerdict.SUSPICIOUS,
            fusion_completed_at=early,
        ),
        _participation(
            evidence_id=uuid4(),
            verdict=FusionVerdict.SUSPICIOUS,
            fusion_completed_at=late,
        ),
    )
    conflicts = _metadata_timestamp_conflicts(participations)
    assert any(
        conflict.conflict_type == CaseConflictType.TEMPORAL_INCONSISTENCY
        for conflict in conflicts
    )


def test_relationship_deduplication_is_deterministic() -> None:
    left_id = uuid4()
    right_id = uuid4()
    shared_hash = "d" * 64
    participations = (
        _participation(evidence_id=left_id, evidence_hash=shared_hash),
        _participation(evidence_id=right_id, evidence_hash=shared_hash),
    )
    first = _duplicate_hash_relationships(participations)
    second = _duplicate_hash_relationships(participations)
    deduped = _deduplicate_relationships(list(first) + list(second))
    assert len(deduped) == 1
    assert deduped[0].relationship_id == first[0].relationship_id


def test_policy_versions_are_documented() -> None:
    assert ENGINE_VERSION == "1.0"
    assert POLICY_VERSION == "1.0"


def test_evidence_without_fusion_counts_as_not_analyzed() -> None:
    participations = (
        _participation(
            verdict=None,
            coverage_status=EvidenceCoverageStatus.NOT_ANALYZED,
        ),
    )
    coverage = compute_coverage(participations, open_conflicts=0)
    assert coverage.not_analyzed == 1
    assert coverage.analyzed == 0


@pytest.mark.asyncio
async def test_api_empty_case_intelligence(phase6g_client) -> None:
    client, _, _, _ = phase6g_client
    case = await create_case(client)
    queue = await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    assert queue.status_code == 202
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/intelligence/latest")
        if latest.status_code == 200:
            break
    payload = latest.json()["data"]
    assert payload["verdict"] == "insufficient_evidence"
    assert payload["coverage"]["total_evidence"] == 0


@pytest.mark.asyncio
async def test_api_evidence_without_fusion(phase6g_client) -> None:
    client, _, _, _ = phase6g_client
    case = await create_case(client)
    await process_and_extract(
        client,
        case["id"],
        "no-fusion.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    await client.post(f"/api/v1/cases/{case['id']}/intelligence")
    for _ in range(30):
        latest = await client.get(f"/api/v1/cases/{case['id']}/intelligence/latest")
        if latest.status_code == 200:
            break
    payload = latest.json()["data"]
    assert payload["coverage"]["not_analyzed"] >= 1
    assert any(
        item["coverage_status"] == "not_analyzed"
        for item in payload["participations"]
    )


@pytest.mark.asyncio
async def test_api_conflicts_and_relationships_endpoints(phase6g_client) -> None:
    client, _, _, _ = phase6g_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "conflict.pdf",
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
        latest = await client.get(f"/api/v1/cases/{case['id']}/intelligence/latest")
        if latest.status_code == 200:
            break
    conflicts = await client.get(f"/api/v1/cases/{case['id']}/conflicts")
    relationships = await client.get(f"/api/v1/cases/{case['id']}/relationships")
    assert conflicts.status_code == 200
    assert relationships.status_code == 200
    assert isinstance(conflicts.json()["data"], list)
    assert isinstance(relationships.json()["data"], list)
