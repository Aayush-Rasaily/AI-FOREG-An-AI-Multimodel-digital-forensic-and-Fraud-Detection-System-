"""Tests for Phase 5C reference comparison engine."""

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
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.api.dependencies import get_db_session
from backend.app.comparison.engine import ComparisonEngine
from backend.app.comparison.localization import regions_to_responses
from backend.app.comparison.matchers.metadata_matcher import MetadataMatcher
from backend.app.comparison.matchers.text_matcher import TextMatcher
from backend.app.comparison.models import (
    ComparisonContext,
    ComparisonRunStatus,
    DifferenceSeverity,
    DifferenceType,
    RegionBox,
)
from backend.app.comparison.repository import ComparisonRepository
from backend.app.comparison.utils import compute_ssim
from backend.app.core.config import Settings
from backend.app.domain.processing import EvidenceClassification
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.comparison import ComparisonRun, Difference, DifferenceRegion
from backend.app.models.evidence import Evidence
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract


def make_pdf_with_text(text: str) -> bytes:
    """Build a small PDF embedding the supplied text."""

    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)
    font = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    content = DecodedStreamObject()
    content.set_data(f"BT /F1 12 Tf 72 700 Td ({text}) Tj ET".encode())
    page[NameObject("/Contents")] = writer._add_object(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest_asyncio.fixture
async def phase5c_client(
    tmp_path,
) -> AsyncIterator[
    tuple[httpx.AsyncClient, async_sessionmaker[AsyncSession], AsyncEngine, FastAPI]
]:
    """Create an isolated API for reference comparison tests."""

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


def _comparison_context(
    storage: LocalStorage,
    settings: Settings,
    *,
    ref_text: str,
    q_text: str,
) -> ComparisonContext:
    case_id = uuid4()
    ref_id = uuid4()
    q_id = uuid4()
    ref_key = f"evidence/{case_id}/{ref_id}/original"
    q_key = f"evidence/{case_id}/{q_id}/original"
    ref_path = settings.storage_root.joinpath(*ref_key.split("/"))
    q_path = settings.storage_root.joinpath(*q_key.split("/"))
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    q_path.parent.mkdir(parents=True, exist_ok=True)
    ref_bytes = ref_text.encode("utf-8")
    q_bytes = q_text.encode("utf-8")
    ref_path.write_bytes(ref_bytes)
    q_path.write_bytes(q_bytes)
    extractions = lambda text: (  # noqa: E731
        {
            "id": str(uuid4()),
            "extraction_type": "TEXT",
            "content": text,
            "page_number": 1,
            "metadata": {},
        },
    )
    return ComparisonContext(
        case_id=case_id,
        questioned_evidence_id=q_id,
        reference_evidence_id=ref_id,
        questioned_filename="questioned.txt",
        reference_filename="reference.txt",
        questioned_mime_type="text/plain",
        reference_mime_type="text/plain",
        questioned_storage_key=q_key,
        reference_storage_key=ref_key,
        questioned_sha256=hashlib.sha256(q_bytes).hexdigest(),
        reference_sha256=hashlib.sha256(ref_bytes).hexdigest(),
        questioned_classification=EvidenceClassification.DOCUMENT,
        reference_classification=EvidenceClassification.DOCUMENT,
        storage=storage,
        settings=settings,
        questioned_extractions=extractions(q_text),
        reference_extractions=extractions(ref_text),
    )


@pytest.mark.asyncio
async def test_text_matcher_detects_number_change(tmp_path) -> None:
    """Text matcher flags numeric and currency changes."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "text",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _comparison_context(
        storage,
        settings,
        ref_text="Invoice total: ₹12,500 due 01/04/2026",
        q_text="Invoice total: ₹72,500 due 11/04/2026",
    )
    result = await TextMatcher().compare(context)
    types = {item.difference_type for item in result.differences}
    assert DifferenceType.NUMBER_CHANGED in types
    assert DifferenceType.DATE_CHANGED in types


@pytest.mark.asyncio
async def test_metadata_matcher_detects_field_change(tmp_path) -> None:
    """Metadata matcher reports producer and creator differences."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "meta",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = ComparisonContext(
        case_id=uuid4(),
        questioned_evidence_id=uuid4(),
        reference_evidence_id=uuid4(),
        questioned_filename="q.pdf",
        reference_filename="r.pdf",
        questioned_mime_type="application/pdf",
        reference_mime_type="application/pdf",
        questioned_storage_key="q/key",
        reference_storage_key="r/key",
        questioned_sha256="a" * 64,
        reference_sha256="b" * 64,
        questioned_classification=EvidenceClassification.DOCUMENT,
        reference_classification=EvidenceClassification.DOCUMENT,
        storage=storage,
        settings=settings,
        questioned_metadata={"producer": "Adobe", "creator": "Writer A"},
        reference_metadata={"producer": "Microsoft", "creator": "Writer B"},
    )
    result = await MetadataMatcher().compare(context)
    assert result.differences
    assert all(
        item.difference_type == DifferenceType.METADATA_CHANGED
        for item in result.differences
    )


def test_ssim_is_deterministic() -> None:
    """SSIM helper returns stable scores for identical arrays."""

    array = np.full((32, 32), 128, dtype=np.uint8)
    assert compute_ssim(array, array) == pytest.approx(1.0, abs=1e-6)
    changed = array.copy()
    changed[10:20, 10:20] = 200
    assert compute_ssim(array, changed) < 0.99


@pytest.mark.asyncio
async def test_comparison_repository_persists_regions(
    phase5c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Repository stores differences with localized regions."""

    _, session_factory, _, _ = phase5c_client
    async with session_factory() as session:
        evidence = Evidence(
            id=uuid4(),
            case_id=uuid4(),
            evidence_number="EVID-CMP-001",
            original_filename="test.pdf",
            stored_filename="test.pdf",
            mime_type="application/pdf",
            file_size=10,
            sha256_hash="c" * 64,
            storage_key="evidence/test/original",
            metadata_json={},
        )
        session.add(evidence)
        await session.flush()
        repository = ComparisonRepository(session)
        run = ComparisonRun(
            id=uuid4(),
            evidence_id=evidence.id,
            reference_record_id=uuid4(),
            reference_evidence_id=uuid4(),
            status=ComparisonRunStatus.SUCCEEDED,
            engine_version="1.0",
            differences_count=1,
        )
        await repository.add_run(run)
        difference = Difference(
            id=uuid4(),
            comparison_run_id=run.id,
            evidence_id=evidence.id,
            matcher="text",
            difference_type=DifferenceType.TEXT_CHANGED,
            severity=DifferenceSeverity.MEDIUM,
            confidence=0.8,
            description="Changed",
            explanation="Text changed",
        )
        await repository.add_difference(difference)
        await repository.add_region(
            DifferenceRegion(
                id=uuid4(),
                difference_id=difference.id,
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
        loaded, total = await repository.list_differences_for_evidence(
            evidence.id,
            limit=10,
            offset=0,
        )
        assert total == 1
        assert loaded[0].regions[0].height == 4.0


@pytest.mark.asyncio
async def test_localization_maps_difference_regions() -> None:
    """Localization helper exposes normalized coordinates for differences."""

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
async def test_comparison_engine_runs_matchers(tmp_path) -> None:
    """Engine aggregates matcher output without switch dispatch."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "engine",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    context = _comparison_context(
        storage,
        settings,
        ref_text="Amount 100",
        q_text="Amount 999",
    )
    result = await ComparisonEngine().compare(context)
    assert result.status == ComparisonRunStatus.SUCCEEDED
    assert result.differences


async def _register_reference(
    client: httpx.AsyncClient,
    case_id: object,
    evidence_id: object,
    label: str,
) -> dict[str, object]:
    response = await client.post(
        f"/api/v1/cases/{case_id}/references",
        json={"evidence_id": evidence_id, "label": label},
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.mark.asyncio
async def test_comparison_api_end_to_end(
    phase5c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Compare API registers reference, runs comparison, and returns differences."""

    client, _, _, _ = phase5c_client
    case = await create_case(client)
    reference = await process_and_extract(
        client,
        case["id"],
        "reference.pdf",
        make_pdf_with_text("Reference invoice total 12500"),
        "application/pdf",
    )
    questioned = await process_and_extract(
        client,
        case["id"],
        "questioned.pdf",
        make_pdf_with_text("Reference invoice total 72500"),
        "application/pdf",
    )
    ref_record = await _register_reference(
        client,
        case["id"],
        reference["id"],
        "Trusted reference",
    )
    compare = await client.post(
        f"/api/v1/evidence/{questioned['id']}/compare",
        json={"reference_evidence_id": ref_record["id"]},
    )
    assert compare.status_code == 202
    differences = await client.get(
        f"/api/v1/evidence/{questioned['id']}/differences",
    )
    assert differences.status_code == 200
    comparisons = await client.get(
        f"/api/v1/evidence/{questioned['id']}/comparisons",
    )
    assert comparisons.status_code == 200
    assert comparisons.json()["data"]["total"] >= 1


@pytest.mark.asyncio
async def test_comparison_preserves_original_hash(
    phase5c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Comparison never modifies original evidence bytes."""

    client, session_factory, _, application = phase5c_client
    case = await create_case(client)
    questioned_content = make_pdf_with_text("Modified content")
    reference = await process_and_extract(
        client,
        case["id"],
        "ref.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    questioned = await process_and_extract(
        client,
        case["id"],
        "q.pdf",
        make_pdf_with_text("Modified content"),
        "application/pdf",
    )
    ref_record = await _register_reference(
        client,
        case["id"],
        reference["id"],
        "Reference",
    )
    await client.post(
        f"/api/v1/evidence/{questioned['id']}/compare",
        json={"reference_evidence_id": ref_record["id"]},
    )
    questioned_content = make_pdf_with_text("Modified content")
    original_hash = hashlib.sha256(questioned_content).hexdigest()
    async with session_factory() as session:
        stored = await session.get(Evidence, UUID(str(questioned["id"])))
        assert stored is not None
        stored_path = application.state.settings.storage_root.joinpath(
            *stored.storage_key.split("/")
        )
        assert hashlib.sha256(stored_path.read_bytes()).hexdigest() == original_hash


@pytest.mark.asyncio
async def test_reference_hash_verification_blocks_tampered_reference(
    phase5c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    """Comparison rejects references whose hash no longer matches registration."""

    client, session_factory, _, _ = phase5c_client
    case = await create_case(client)
    reference = await process_and_extract(
        client,
        case["id"],
        "ref.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    questioned = await process_and_extract(
        client,
        case["id"],
        "q.pdf",
        make_pdf_with_text("Questioned"),
        "application/pdf",
    )
    ref_record = await _register_reference(
        client,
        case["id"],
        reference["id"],
        "Reference",
    )
    async with session_factory() as session:
        from backend.app.models.comparison import ReferenceEvidence

        record = await session.get(ReferenceEvidence, UUID(str(ref_record["id"])))
        assert record is not None
        record.reference_hash = "d" * 64
        await session.commit()
    response = await client.post(
        f"/api/v1/evidence/{questioned['id']}/compare",
        json={"reference_evidence_id": ref_record["id"]},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_image_ssim_comparison(tmp_path) -> None:
    """Image matcher produces SSIM-based differences for changed pixels."""

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "img",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    case_id = uuid4()
    ref_id = uuid4()
    q_id = uuid4()
    ref_key = f"evidence/{case_id}/{ref_id}/original"
    q_key = f"evidence/{case_id}/{q_id}/original"
    ref_path = settings.storage_root.joinpath(*ref_key.split("/"))
    q_path = settings.storage_root.joinpath(*q_key.split("/"))
    ref_path.parent.mkdir(parents=True, exist_ok=True)
    q_path.parent.mkdir(parents=True, exist_ok=True)
    ref_image = Image.new("RGB", (64, 64), color=(100, 100, 100))
    q_image = Image.new("RGB", (64, 64), color=(100, 100, 100))
    for x in range(20, 40):
        for y in range(20, 40):
            q_image.putpixel((x, y), (255, 0, 0))
    buffer = io.BytesIO()
    ref_image.save(buffer, format="PNG")
    ref_bytes = buffer.getvalue()
    buffer = io.BytesIO()
    q_image.save(buffer, format="PNG")
    q_bytes = buffer.getvalue()
    ref_path.write_bytes(ref_bytes)
    q_path.write_bytes(q_bytes)
    context = ComparisonContext(
        case_id=case_id,
        questioned_evidence_id=q_id,
        reference_evidence_id=ref_id,
        questioned_filename="q.png",
        reference_filename="r.png",
        questioned_mime_type="image/png",
        reference_mime_type="image/png",
        questioned_storage_key=q_key,
        reference_storage_key=ref_key,
        questioned_sha256=hashlib.sha256(q_bytes).hexdigest(),
        reference_sha256=hashlib.sha256(ref_bytes).hexdigest(),
        questioned_classification=EvidenceClassification.IMAGE,
        reference_classification=EvidenceClassification.IMAGE,
        storage=storage,
        settings=settings,
    )
    from backend.app.comparison.matchers.image_matcher import ImageMatcher

    result = await ImageMatcher().compare(context)
    assert result.differences
    assert result.metadata["ssim"] < 0.98
