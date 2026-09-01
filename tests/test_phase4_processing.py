"""Integration tests for the Phase 4 deterministic processing pipeline."""

import hashlib
import io
import wave
from collections.abc import AsyncIterator
from typing import cast
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import (
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
)
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
from backend.app.extraction.exceptions import ExtractionCapabilityUnavailableError
from backend.app.extraction.models import BoundingBox, normalize_bbox
from backend.app.extraction.ocr import TesseractOCRProvider
from backend.app.extraction.video.sampler import sample_timestamps
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
                    select(Artifact).where(Artifact.evidence_id == stored.id)
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


def make_text_pdf() -> bytes:
    """Build a small native-text PDF without external document tooling."""

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
        {
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        }
    )
    content = DecodedStreamObject()
    content.set_data(
        b"BT /F1 12 Tf 72 700 Td (Invoice No: 12345 Date: 31/08/2026) Tj ET"
    )
    page[NameObject("/Contents")] = writer._add_object(content)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


async def process_and_extract(
    client: httpx.AsyncClient,
    case_id: object,
    filename: str,
    content: bytes,
    mime_type: str,
) -> dict[str, object]:
    """Upload, process, and extract one test evidence item."""

    uploaded = await client.post(
        f"/api/v1/cases/{case_id}/evidence",
        files={"file": (filename, content, mime_type)},
    )
    assert uploaded.status_code == 201
    evidence = uploaded.json()["data"]
    processed = await client.post(f"/api/v1/evidence/{evidence['id']}/process")
    assert processed.status_code == 202
    extracted = await client.post(f"/api/v1/evidence/{evidence['id']}/extract")
    assert extracted.status_code == 202
    return cast(dict[str, object], evidence)


@pytest.mark.asyncio
async def test_image_extraction_and_empty_regions_are_truthful(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """Image dimensions are extracted while unsupported regions stay empty."""

    client, _, _, _ = phase4_client
    case = await create_case(client)
    image = io.BytesIO()
    Image.new("RGB", (40, 20), color=(10, 20, 30)).save(image, format="PNG")
    evidence = await process_and_extract(
        client,
        case["id"],
        "scene.png",
        image.getvalue(),
        "image/png",
    )

    extractions = await client.get(f"/api/v1/evidence/{evidence['id']}/extractions")
    assert extractions.json()["data"]["status"] == "SUCCEEDED"
    metadata = extractions.json()["data"]["items"][0]
    assert metadata["metadata"]["width"] == 40
    assert metadata["metadata"]["height"] == 20
    regions = await client.get(f"/api/v1/evidence/{evidence['id']}/regions")
    assert regions.json()["data"]["total"] == 0
    artifacts = await client.get(
        f"/api/v1/evidence/{evidence['id']}/extraction-artifacts"
    )
    assert artifacts.json()["data"]["total"] == 1
    assert artifacts.json()["data"]["items"][0]["artifact_type"] == "IMAGE_REGIONS"


@pytest.mark.asyncio
async def test_pdf_text_extraction_preserves_page_provenance(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """Native PDF text includes its page and deliberately has no fake box."""

    client, _, _, _ = phase4_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "invoice.pdf",
        make_text_pdf(),
        "application/pdf",
    )

    extractions = await client.get(f"/api/v1/evidence/{evidence['id']}/extractions")
    items = extractions.json()["data"]["items"]
    text = next(item for item in items if item["extraction_type"] == "TEXT")
    assert "Invoice No: 12345" in text["content"]
    assert text["page_number"] == 1
    assert text["location"] is None
    assert text["source_identifier"] == "invoice.pdf"
    assert text["method"] == "pdf_text"
    assert any(item["extraction_type"] == "NUMBER" for item in items)
    date = next(item for item in items if item["extraction_type"] == "DATE")
    assert date["content"] == "31/08/2026"
    assert date["metadata"]["normalized_value"] == "2026-08-31"
    assert any(
        item["artifact_type"] == "DOCUMENT_STRUCTURE"
        for item in (
            await client.get(f"/api/v1/evidence/{evidence['id']}/extraction-artifacts")
        ).json()["data"]["items"]
    )


@pytest.mark.asyncio
async def test_wav_audio_extraction_is_bounded_and_repeatable(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """WAV metadata uses stdlib parsing and equivalent reruns reuse the job."""

    client, _, _, _ = phase4_client
    case = await create_case(client)
    audio = io.BytesIO()
    with wave.open(audio, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(8_000)
        stream.writeframes(b"\x00\x00" * 8_000)
    evidence = await process_and_extract(
        client,
        case["id"],
        "sample.wav",
        audio.getvalue(),
        "audio/wav",
    )

    extractions = await client.get(f"/api/v1/evidence/{evidence['id']}/extractions")
    item = extractions.json()["data"]["items"][0]
    assert item["extraction_type"] == "AUDIO_STREAM"
    assert item["metadata"]["sample_rate"] == 8_000
    first_job = (
        await client.get(f"/api/v1/evidence/{evidence['id']}/processing")
    ).json()["data"]["items"][0]
    repeated = await client.post(f"/api/v1/evidence/{evidence['id']}/extract")
    assert repeated.status_code == 202
    assert repeated.json()["data"]["id"] == first_job["id"]


@pytest.mark.asyncio
async def test_video_extraction_reports_missing_optional_capability(
    phase4_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        object,
        object,
    ],
) -> None:
    """A missing ffprobe is visible as unavailable rather than fabricated data."""

    client, _, _, _ = phase4_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "clip.mp4",
        b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32,
        "video/mp4",
    )
    extractions = await client.get(f"/api/v1/evidence/{evidence['id']}/extractions")
    data = extractions.json()["data"]
    assert data["status"] == "UNAVAILABLE"
    assert data["error_code"] == "MEDIA_PARSER_UNAVAILABLE"
    assert data["items"] == []


@pytest.mark.asyncio
async def test_ocr_unavailable_and_normalized_boxes_are_explicit() -> None:
    """OCR availability and normalized-coordinate validation are deterministic."""

    provider = TesseractOCRProvider(True, "missing-tesseract-for-test")
    with pytest.raises(ExtractionCapabilityUnavailableError):
        await provider.extract_words(object())

    normalized = normalize_bbox(BoundingBox(10, 5, 20, 10), 100, 100)
    assert normalized == BoundingBox(0.1, 0.05, 0.2, 0.1)
    with pytest.raises(ValueError):
        normalize_bbox(BoundingBox(90, 0, 20, 10), 100, 100)


def test_frame_sampler_is_deterministic_and_bounded() -> None:
    """Sampling schedules are conservative and never exceed max_frames."""

    assert sample_timestamps(12, 5, 10) == (0, 5000, 10000)
    assert sample_timestamps(120, 1, 3) == (0, 1000, 2000)
