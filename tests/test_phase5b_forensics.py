"""Tests for Phase 5B classical forensic analysis."""

import hashlib
import io
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import httpx
import numpy as np
import pytest
import pytest_asyncio
from fastapi import FastAPI
from PIL import Image
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.detectors.document.consistency import ConsistencyDetector
from backend.app.forensics.detectors.document.layout import LayoutDetector
from backend.app.forensics.detectors.image.copy_move import CopyMoveDetector
from backend.app.forensics.detectors.image.ela import ElaDetector
from backend.app.forensics.detectors.image.metadata import ImageMetadataDetector
from backend.app.forensics.detectors.image.noise import NoiseDetector
from backend.app.forensics.engine import ForensicAnalysisEngine
from backend.app.forensics.localization import regions_to_responses
from backend.app.forensics.models import (
    AnalysisContext,
    AnalysisRunStatus,
    FindingCategory,
    Severity,
)
from backend.app.forensics.repository import ForensicRepository
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.evidence import Evidence
from backend.app.models.forensics import AnalysisRun, Finding, FindingRegion
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract


@pytest_asyncio.fixture
async def phase5b_client(
    tmp_path,
) -> AsyncIterator[
    tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession], AsyncEngine, FastAPI]
]:
    """Create an isolated API for forensic analysis tests."""

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


def _jpeg_bytes() -> bytes:
    image = Image.new("RGB", (128, 128), color=(120, 80, 40))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def _copy_move_image_bytes() -> bytes:
    array = np.zeros((200, 200, 3), dtype=np.uint8)
    patch = np.random.default_rng(1).integers(20, 220, (60, 60, 3), dtype=np.uint8)
    array[20:80, 20:80] = patch
    array[120:180, 120:180] = patch
    image = Image.fromarray(array, mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _analysis_context(
    storage: LocalStorage,
    settings: Settings,
    *,
    filename: str,
    content: bytes,
    classification: EvidenceClassification,
) -> AnalysisContext:
    case_id = uuid4()
    evidence_id = uuid4()
    storage_key = f"evidence/{case_id}/{evidence_id}/original"
    path = settings.storage_root.joinpath(*storage_key.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return AnalysisContext(
        evidence_id=evidence_id,
        case_id=case_id,
        original_filename=filename,
        mime_type="image/jpeg",
        storage_key=storage_key,
        classification=classification,
        source_sha256=hashlib.sha256(content).hexdigest(),
        storage=storage,
        settings=settings,
    )


@pytest.mark.asyncio
async def test_ela_detector_executes_on_image(tmp_path) -> None:
    """ELA produces deterministic forensic output for a JPEG."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "ela",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _analysis_context(
        storage,
        settings,
        filename="sample.jpg",
        content=_jpeg_bytes(),
        classification=EvidenceClassification.IMAGE,
    )
    result = await ElaDetector().analyze(context)
    assert result.detector == "ela"
    assert result.metadata["ela_score"] >= 0.0
    assert any(
        artifact.artifact_type.value == "ELA_RESULT" for artifact in result.artifacts
    )


@pytest.mark.asyncio
async def test_image_metadata_detector_reports_missing_exif(tmp_path) -> None:
    """Metadata detector records absent EXIF as informational evidence."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "meta",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _analysis_context(
        storage,
        settings,
        filename="plain.jpg",
        content=_jpeg_bytes(),
        classification=EvidenceClassification.IMAGE,
    )
    result = await ImageMetadataDetector().analyze(context)
    assert result.findings
    assert result.findings[0].category.value == "METADATA"


@pytest.mark.asyncio
async def test_noise_detector_executes(tmp_path) -> None:
    """Noise detector returns bounded scores and optional heatmap artifacts."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "noise",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _analysis_context(
        storage,
        settings,
        filename="noise.jpg",
        content=_jpeg_bytes(),
        classification=EvidenceClassification.IMAGE,
    )
    result = await NoiseDetector().analyze(context)
    assert "noise_score" in result.metadata


@pytest.mark.asyncio
async def test_copy_move_detector_finds_duplicated_regions(tmp_path) -> None:
    """Copy-move detector localizes duplicated patches."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "copy",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _analysis_context(
        storage,
        settings,
        filename="copy.png",
        content=_copy_move_image_bytes(),
        classification=EvidenceClassification.IMAGE,
    )
    result = await CopyMoveDetector().analyze(context)
    assert result.metadata["match_count"] >= 1
    assert result.findings
    assert result.findings[0].regions


@pytest.mark.asyncio
async def test_layout_detector_runs_on_pdf(tmp_path) -> None:
    """Layout detector executes against extracted PDF text blocks."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "layout",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    pdf = make_text_pdf()
    case_id = uuid4()
    evidence_id = uuid4()
    storage_key = f"evidence/{case_id}/{evidence_id}/original.pdf"
    path = settings.storage_root.joinpath(*storage_key.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(pdf)
    context = AnalysisContext(
        evidence_id=evidence_id,
        case_id=case_id,
        original_filename="invoice.pdf",
        mime_type="application/pdf",
        storage_key=storage_key,
        classification=EvidenceClassification.DOCUMENT,
        source_sha256=hashlib.sha256(pdf).hexdigest(),
        storage=storage,
        settings=settings,
    )
    result = await LayoutDetector().analyze(context)
    assert result.detector == "layout"


@pytest.mark.asyncio
async def test_consistency_detector_flags_impossible_dates(tmp_path) -> None:
    """Consistency detector reports invalid calendar dates."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "consistency",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    content = b"Issue date: 31/02/2026\nTotal: 10.00\n"
    case_id = uuid4()
    evidence_id = uuid4()
    storage_key = f"evidence/{case_id}/{evidence_id}/note.txt"
    path = settings.storage_root.joinpath(*storage_key.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    context = AnalysisContext(
        evidence_id=evidence_id,
        case_id=case_id,
        original_filename="note.txt",
        mime_type="text/plain",
        storage_key=storage_key,
        classification=EvidenceClassification.DOCUMENT,
        source_sha256=hashlib.sha256(content).hexdigest(),
        storage=storage,
        settings=settings,
    )
    result = await ConsistencyDetector().analyze(context)
    assert any(finding.category.value == "DATE" for finding in result.findings)


@pytest.mark.asyncio
async def test_forensic_repository_persists_findings_and_regions(
    phase5b_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Repository stores findings with localized regions."""

    _, session_factory, _, _ = phase5b_client
    async with session_factory() as session:
        evidence = Evidence(
            id=uuid4(),
            case_id=uuid4(),
            evidence_number="EVID-FORENSIC-001",
            original_filename="sample.jpg",
            stored_filename="sample.jpg",
            mime_type="image/jpeg",
            file_size=128,
            sha256_hash="a" * 64,
            storage_key="evidence/test/sample.jpg",
        )
        session.add(evidence)
        await session.flush()
        repository = ForensicRepository(session)
        run = AnalysisRun(
            id=uuid4(),
            evidence_id=evidence.id,
            status=AnalysisRunStatus.SUCCEEDED,
            engine_version="1.0",
            findings_count=1,
        )
        await repository.add_run(run)
        finding = Finding(
            id=uuid4(),
            analysis_run_id=run.id,
            evidence_id=evidence.id,
            detector="ela",
            category=FindingCategory.COMPRESSION,
            severity=Severity.LOW,
            confidence=0.6,
            description="Test finding",
            explanation="Test explanation",
        )
        await repository.add_finding(finding)
        await repository.add_region(
            FindingRegion(
                id=uuid4(),
                finding_id=finding.id,
                x=1.0,
                y=2.0,
                width=3.0,
                height=4.0,
                normalized_x=0.1,
                normalized_y=0.2,
                normalized_width=0.3,
                normalized_height=0.4,
            )
        )
        await session.commit()
        loaded = await repository.list_findings_for_evidence(
            evidence.id, limit=10, offset=0
        )
        assert loaded[1] == 1
        assert loaded[0][0].regions[0].height == 4.0


@pytest.mark.asyncio
async def test_localization_maps_regions_to_api_schema() -> None:
    """Localization helper exposes normalized coordinates."""

    from backend.app.forensics.models import RegionBox

    regions = (
        RegionBox(
            x=10,
            y=20,
            width=30,
            height=40,
            normalized=RegionBox(x=0.1, y=0.2, width=0.3, height=0.4),
        ),
    )
    responses = regions_to_responses(regions)
    assert responses[0].normalized_location == {
        "x": 0.1,
        "y": 0.2,
        "width": 0.3,
        "height": 0.4,
    }


@pytest.mark.asyncio
async def test_forensic_api_preserves_original_hash(
    phase5b_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Analysis never modifies the original evidence bytes."""

    client, session_factory, _, application = phase5b_client
    case = await create_case(client)
    content = make_text_pdf()
    evidence = await process_and_extract(
        client,
        case["id"],
        "invoice.pdf",
        content,
        "application/pdf",
    )
    original_hash = hashlib.sha256(content).hexdigest()
    analyzed = await client.post(f"/api/v1/evidence/{evidence['id']}/analyze")
    assert analyzed.status_code == 202

    findings = await client.get(f"/api/v1/evidence/{evidence['id']}/findings")
    assert findings.status_code == 200
    assert findings.json()["data"]["total"] >= 0

    async with session_factory() as session:
        stored = await session.get(Evidence, UUID(str(evidence["id"])))
        assert stored is not None
        stored_path = application.state.settings.storage_root.joinpath(
            *stored.storage_key.split("/")
        )
        assert stored_path.read_bytes() == content
        assert hashlib.sha256(stored_path.read_bytes()).hexdigest() == original_hash


@pytest.mark.asyncio
async def test_forensic_analysis_is_repeatable_for_pdf(
    phase5b_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Two analysis runs on unchanged evidence yield the same finding count."""

    client, _, _, _ = phase5b_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "invoice.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    first = await client.post(f"/api/v1/evidence/{evidence['id']}/analyze")
    assert first.status_code == 202
    first_findings = await client.get(f"/api/v1/evidence/{evidence['id']}/findings")
    first_count = first_findings.json()["data"]["total"]

    repeated = await client.post(f"/api/v1/evidence/{evidence['id']}/analyze")
    assert repeated.status_code == 202
    second_findings = await client.get(f"/api/v1/evidence/{evidence['id']}/findings")
    assert second_findings.json()["data"]["total"] == first_count


@pytest.mark.asyncio
async def test_engine_runs_all_compatible_detectors(tmp_path) -> None:
    """Engine executes plugins without switch-based dispatch."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "engine",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _analysis_context(
        storage,
        settings,
        filename="engine.jpg",
        content=_jpeg_bytes(),
        classification=EvidenceClassification.IMAGE,
    )
    result = await ForensicAnalysisEngine().analyze(context)
    assert result.status == AnalysisRunStatus.SUCCEEDED
    assert "detectors" in result.metadata
    assert "ela" in result.metadata["detectors"]
