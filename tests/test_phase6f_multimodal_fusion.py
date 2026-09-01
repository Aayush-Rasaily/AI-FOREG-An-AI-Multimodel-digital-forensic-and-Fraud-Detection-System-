"""Tests for Phase 6F multimodal fusion and AI jury."""

from __future__ import annotations

from collections.abc import AsyncIterator
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
from backend.app.core.config import Settings
from backend.app.forensics.models import AnalysisRunStatus, FindingCategory, Severity
from backend.app.fusion.engine import FusionEngine
from backend.app.fusion.jury import assess_jury
from backend.app.fusion.models import (
    FindingVerdict,
    FusionVerdict,
    Modality,
    ModalityAvailability,
    NormalizedFinding,
)
from backend.app.fusion.normalization import (
    deduplicate_findings,
    normalize_forensic_finding,
)
from backend.app.fusion.policy import fuse_evidence
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.models.evidence import Evidence
from backend.app.models.forensics import AnalysisRun, Finding
from backend.app.models.fusion import FusionAnalysisRun
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract


def _finding(
    *,
    finding_id: str,
    modality: Modality,
    verdict: FindingVerdict,
    severity: Severity = Severity.MEDIUM,
    confidence: float | None = 0.8,
    availability: ModalityAvailability = ModalityAvailability.AVAILABLE,
) -> NormalizedFinding:
    return NormalizedFinding(
        finding_id=finding_id,
        evidence_id=UUID("00000000-0000-0000-0000-000000000099"),
        modality=modality,
        analyzer="test",
        category="TEST",
        finding_type="test",
        verdict=verdict,
        confidence=confidence,
        severity=severity,
        description="Test finding",
        explanation="Test explanation",
        source_reference=f"{modality.value}:test",
        availability=availability,
    )


@pytest_asyncio.fixture
async def phase6f_client(
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


def test_normalize_forensic_finding_preserves_source() -> None:
    evidence_id = UUID("00000000-0000-0000-0000-000000000010")
    finding_id = uuid4()
    normalized = normalize_forensic_finding(
        evidence_id=evidence_id,
        finding_id=finding_id,
        detector="metadata",
        category="METADATA",
        severity=Severity.HIGH,
        confidence=0.9,
        description="Metadata mismatch",
        explanation="Software tag inconsistent",
        metadata={"source": "forensics"},
    )
    assert normalized.modality == Modality.FORENSICS
    assert normalized.verdict == FindingVerdict.SUPPORTS_FRAUD
    assert normalized.source_reference == f"forensics:{finding_id}"


def test_deduplicate_findings_removes_duplicates() -> None:
    first = _finding(
        finding_id="forensics:1:metadata",
        modality=Modality.FORENSICS,
        verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
    )
    duplicate = _finding(
        finding_id="forensics:1:metadata",
        modality=Modality.FORENSICS,
        verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
    )
    unique = deduplicate_findings((duplicate, first))
    assert len(unique) == 1
    assert unique[0].finding_id == "forensics:1:metadata"


def test_fuse_empty_findings_is_insufficient_evidence() -> None:
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000011"),
        source_hash="a" * 64,
        findings=(),
        modality_statuses=(),
    )
    assert result.assessment is not None
    assert result.assessment.verdict == FusionVerdict.INSUFFICIENT_EVIDENCE
    assert result.assessment.provenance["source_sha256"] == "a" * 64


def test_fuse_single_modality() -> None:
    findings = (
        _finding(
            finding_id="forensics:1:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        ),
    )
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000012"),
        source_hash="b" * 64,
        findings=findings,
        modality_statuses=(),
    )
    assert result.assessment is not None
    assert result.assessment.verdict in {
        FusionVerdict.SUSPICIOUS,
        FusionVerdict.POTENTIAL_FRAUD,
        FusionVerdict.INCONCLUSIVE,
    }


def test_fuse_multiple_modalities() -> None:
    findings = (
        _finding(
            finding_id="forensics:1:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        ),
        _finding(
            finding_id="image_ai:2:manipulation",
            modality=Modality.IMAGE_AI,
            verdict=FindingVerdict.SUPPORTS_FRAUD,
            severity=Severity.CRITICAL,
        ),
    )
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000013"),
        source_hash="c" * 64,
        findings=findings,
        modality_statuses=(),
    )
    assert result.assessment is not None
    assert result.assessment.risk_score is not None
    assert result.assessment.risk_score > 0


def test_unavailable_findings_do_not_reduce_confidence() -> None:
    findings = (
        _finding(
            finding_id="audio_ai:1:synthetic",
            modality=Modality.AUDIO_AI,
            verdict=FindingVerdict.UNAVAILABLE,
            availability=ModalityAvailability.UNAVAILABLE,
            confidence=None,
        ),
        _finding(
            finding_id="forensics:2:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
            confidence=0.7,
        ),
    )
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000014"),
        source_hash="d" * 64,
        findings=findings,
        modality_statuses=(),
    )
    assert result.assessment is not None
    assert result.assessment.confidence is not None


def test_jury_agreement_with_consistent_votes() -> None:
    findings = (
        _finding(
            finding_id="forensics:1:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        ),
    )
    jury = assess_jury(findings)
    senior = next(item for item in jury if item.role.value == "senior_judge")
    assert senior.availability == ModalityAvailability.AVAILABLE
    assert senior.verdict in {
        FusionVerdict.SUSPICIOUS,
        FusionVerdict.POTENTIAL_FRAUD,
        FusionVerdict.INCONCLUSIVE,
    }


def test_jury_disagreement_preserved() -> None:
    findings = (
        _finding(
            finding_id="forensics:1:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_GENUINE,
        ),
        _finding(
            finding_id="signature_ai:2:signature",
            modality=Modality.SIGNATURE_AI,
            verdict=FindingVerdict.SUPPORTS_FRAUD,
            severity=Severity.HIGH,
        ),
    )
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000015"),
        source_hash="e" * 64,
        findings=findings,
        modality_statuses=(),
    )
    assert result.assessment is not None
    assert len(result.assessment.conflicts) >= 1


def test_conflicting_findings_detected() -> None:
    findings = (
        _finding(
            finding_id="image_ai:1:manipulation",
            modality=Modality.IMAGE_AI,
            verdict=FindingVerdict.SUPPORTS_FRAUD,
        ),
        _finding(
            finding_id="forensics:2:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_GENUINE,
        ),
    )
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000016"),
        source_hash="f" * 64,
        findings=findings,
        modality_statuses=(),
    )
    assert result.assessment is not None
    assert result.assessment.conflicts


def test_weighted_fusion_risk_score() -> None:
    low = _finding(
        finding_id="forensics:1:low",
        modality=Modality.FORENSICS,
        verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        severity=Severity.LOW,
        confidence=0.2,
    )
    high = _finding(
        finding_id="forensics:2:high",
        modality=Modality.FORENSICS,
        verdict=FindingVerdict.SUPPORTS_FRAUD,
        severity=Severity.CRITICAL,
        confidence=0.95,
    )
    low_result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000017"),
        source_hash="g" * 64,
        findings=(low,),
        modality_statuses=(),
    )
    high_result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000017"),
        source_hash="g" * 64,
        findings=(high,),
        modality_statuses=(),
    )
    assert low_result.assessment is not None
    assert high_result.assessment is not None
    assert (high_result.assessment.risk_score or 0) > (
        low_result.assessment.risk_score or 0
    )


def test_model_unavailable_finding_verdict() -> None:
    finding = _finding(
        finding_id="audio_ai:1:synthetic",
        modality=Modality.AUDIO_AI,
        verdict=FindingVerdict.UNAVAILABLE,
        availability=ModalityAvailability.UNAVAILABLE,
        confidence=None,
    )
    jury = assess_jury((finding,))
    unavailable_members = [
        item for item in jury if item.availability != ModalityAvailability.AVAILABLE
    ]
    assert unavailable_members


def test_deterministic_ordering() -> None:
    findings = (
        _finding(
            finding_id="z:1:test",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        ),
        _finding(
            finding_id="a:1:test",
            modality=Modality.IMAGE_AI,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        ),
    )
    ordered = deduplicate_findings(findings)
    assert ordered[0].finding_id == "a:1:test"
    assert ordered[1].finding_id == "z:1:test"


@pytest.mark.asyncio
async def test_engine_preserves_provenance(
    phase6f_client,
) -> None:
    client, session_factory, _, _ = phase6f_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "report.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    evidence_id = UUID(str(evidence["id"]))
    async with session_factory() as session:
        db_evidence = await session.get(Evidence, evidence_id)
        assert db_evidence is not None
        run = AnalysisRun(
            id=uuid4(),
            evidence_id=db_evidence.id,
            status=AnalysisRunStatus.SUCCEEDED,
            engine_version="1.0",
            findings_count=1,
        )
        session.add(run)
        session.add(
            Finding(
                id=uuid4(),
                analysis_run_id=run.id,
                evidence_id=db_evidence.id,
                detector="metadata",
                category=FindingCategory.METADATA,
                severity=Severity.MEDIUM,
                confidence=0.75,
                description="Metadata inconsistency",
                explanation="Creator software mismatch",
            )
        )
        await session.commit()
    async with session_factory() as session:
        db_evidence = await session.get(Evidence, evidence_id)
        assert db_evidence is not None
        result = await FusionEngine().analyze(session, db_evidence)
    assert result.assessment is not None
    assert result.assessment.provenance["source_sha256"] == db_evidence.sha256_hash


@pytest.mark.asyncio
async def test_api_fusion_success(phase6f_client) -> None:
    client, _, _, _ = phase6f_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "fusion.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    evidence_id = evidence["id"]
    queue = await client.post(f"/api/v1/evidence/{evidence_id}/fusion-analysis")
    assert queue.status_code == 202
    latest = None
    for _ in range(30):
        latest = await client.get(
            f"/api/v1/evidence/{evidence_id}/fusion-analysis/latest",
        )
        if latest.status_code == 200:
            break
    assert latest is not None
    assert latest.status_code == 200
    payload = latest.json()["data"]
    assert payload["evidence_id"] == evidence_id
    assert payload["engine_version"] == "1.0"
    assert "jury_assessments" in payload


@pytest.mark.asyncio
async def test_api_missing_evidence_returns_404(phase6f_client) -> None:
    client, _, _, _ = phase6f_client
    missing = UUID("00000000-0000-0000-0000-000000000404")
    response = await client.post(f"/api/v1/evidence/{missing}/fusion-analysis")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_signals_preview(phase6f_client) -> None:
    client, _, _, _ = phase6f_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "signals.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    evidence_id = evidence["id"]
    response = await client.get(f"/api/v1/evidence/{evidence_id}/fusion-signals")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["evidence_id"] == evidence_id
    assert "modality_status" in data


@pytest.mark.asyncio
async def test_api_repeated_analysis_allowed_after_completion(
    phase6f_client,
) -> None:
    client, _, _, _ = phase6f_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "repeat.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    evidence_id = evidence["id"]
    first = await client.post(f"/api/v1/evidence/{evidence_id}/fusion-analysis")
    assert first.status_code == 202
    for _ in range(30):
        latest = await client.get(
            f"/api/v1/evidence/{evidence_id}/fusion-analysis/latest",
        )
        if latest.status_code == 200:
            break
    second = await client.post(f"/api/v1/evidence/{evidence_id}/fusion-analysis")
    assert second.status_code == 202


@pytest.mark.asyncio
async def test_fusion_models_importable() -> None:
    """Migration metadata includes fusion tables."""

    assert FusionAnalysisRun.__tablename__ == "fusion_analysis_runs"


def test_final_assessment_structure() -> None:
    findings = (
        _finding(
            finding_id="forensics:1:metadata",
            modality=Modality.FORENSICS,
            verdict=FindingVerdict.SUPPORTS_SUSPICIOUS,
        ),
    )
    result = fuse_evidence(
        evidence_id=UUID("00000000-0000-0000-0000-000000000018"),
        source_hash="h" * 64,
        findings=findings,
        modality_statuses=(),
    )
    assessment = result.assessment
    assert assessment is not None
    assert assessment.verdict
    assert assessment.explanation
    assert assessment.limitations
    assert assessment.engine_version
    assert assessment.policy_version
    assert assessment.jury_assessments
