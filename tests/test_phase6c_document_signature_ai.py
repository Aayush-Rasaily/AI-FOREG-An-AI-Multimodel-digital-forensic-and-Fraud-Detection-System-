"""Tests for Phase 6C document AI and signature verification."""

import hashlib
import io
from collections.abc import AsyncIterator
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from PIL import Image
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from backend.app.ai.document.bootstrap import build_document_analysis_stack
from backend.app.ai.document.detectors.text_consistency import TextConsistencyDetector
from backend.app.ai.document.models.context import DocumentAnalysisContext
from backend.app.ai.document.preprocessing.document import (
    extract_document_text,
    extract_page_info,
)
from backend.app.ai.document.signature.config import SignatureAISettings
from backend.app.ai.document.signature.model import (
    ModelIntegrityError,
    SiameseSignatureModel,
)
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.domain.processing import EvidenceClassification
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.evidence import Evidence
from tests.test_phase4_processing import create_case, make_text_pdf, process_and_extract


def _png_bytes(width: int = 96, height: int = 64) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color=(255, 255, 255)).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest_asyncio.fixture
async def phase6c_client(
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
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client, session_factory, engine, application
    application.dependency_overrides.clear()
    await engine.dispose()


def test_registry_registers_all_detectors() -> None:
    registry, _, _ = build_document_analysis_stack()
    names = registry.names()
    assert "tampering" in names
    assert "text_consistency" in names
    assert "font_consistency" in names
    assert "layout_consistency" in names
    assert "logo" in names
    assert "metadata" in names
    assert "region_anomaly" in names
    assert len(registry.enabled_names()) == 7


def test_document_preprocessing_extracts_pdf_text_and_pages() -> None:
    pdf = make_text_pdf()
    text = extract_document_text(pdf, "invoice.pdf")
    pages = extract_page_info(pdf, "invoice.pdf")
    assert "Invoice" in text
    assert len(pages) == 1
    assert pages[0].page_number == 1
    assert pages[0].text_length > 0


@pytest.mark.asyncio
async def test_text_consistency_no_fake_confidence_without_word_data(
    tmp_path,
) -> None:
    detector = TextConsistencyDetector()
    detector.load(device="cpu")
    context = DocumentAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000091"),
        case_id=UUID("00000000-0000-0000-0000-000000000092"),
        original_filename="invoice.pdf",
        mime_type="application/pdf",
        storage_key="cases/test/invoice.pdf",
        classification=EvidenceClassification.DOCUMENT,
        source_sha256="abc",
        storage=LocalStorage(tmp_path / "storage"),
        settings=Settings(
            debug=True,
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "storage",
            log_config_path=tmp_path / "missing-logging.json",
        ),
        extraction_records=(),
    )
    output = await detector.predict(context)
    assert output.findings == ()


def test_signature_model_unavailable_without_model_path() -> None:
    model = SiameseSignatureModel(
        SignatureAISettings(enabled=True, model_path=None),
    )
    model.load(device="cpu")
    assert not model.is_loaded
    assert model.health()["status"] == "unavailable"
    assert "SIGNATURE_MODEL_PATH" in str(model.health()["reason"])


def test_signature_verdict_logic() -> None:
    model = SiameseSignatureModel(
        SignatureAISettings(threshold=0.80, inconclusive_margin=0.05),
    )
    assert model._verdict(0.85) == "MATCH"
    assert model._verdict(0.80) == "MATCH"
    assert model._verdict(0.70) == "NON_MATCH"
    assert model._verdict(0.76) == "INCONCLUSIVE"


def test_model_hash_validation_raises_on_mismatch(tmp_path) -> None:
    weights = tmp_path / "signature.pt"
    weights.write_bytes(b"fake-weights")
    actual_hash = hashlib.sha256(weights.read_bytes()).hexdigest()
    wrong_hash = "0" * 64
    assert actual_hash != wrong_hash
    model = SiameseSignatureModel(
        SignatureAISettings(
            enabled=True,
            model_path=str(weights),
            model_sha256=wrong_hash,
        ),
    )
    with pytest.raises(ModelIntegrityError):
        model.load(device="cpu")


@pytest.mark.asyncio
async def test_document_analysis_api_queues_and_returns_findings(
    phase6c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, _, _, _ = phase6c_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "invoice.pdf",
        make_text_pdf(),
        "application/pdf",
    )
    original_hash = evidence["sha256_hash"]
    queued = await client.post(
        f"/api/v1/evidence/{evidence['id']}/document-analysis",
    )
    assert queued.status_code == 202

    runs = await client.get(
        f"/api/v1/evidence/{evidence['id']}/document-analysis",
    )
    assert runs.status_code == 200
    assert runs.json()["data"]["total"] >= 0

    findings = await client.get(
        f"/api/v1/evidence/{evidence['id']}/document-findings",
    )
    assert findings.status_code == 200

    refreshed = await client.get(f"/api/v1/evidence/{evidence['id']}")
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["sha256_hash"] == original_hash


@pytest.mark.asyncio
async def test_signature_verify_api_unavailable_state(
    phase6c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SIGNATURE_MODEL_PATH", raising=False)
    client, _, _, _ = phase6c_client
    reference = _png_bytes()
    questioned = _png_bytes()
    response = await client.post(
        "/api/v1/signature/verify",
        files={
            "reference_file": ("reference.png", reference, "image/png"),
            "questioned_file": ("questioned.png", questioned, "image/png"),
        },
    )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["verdict"] == "UNAVAILABLE"
    assert payload["similarity"] is None
    assert payload["reference_hash"] == hashlib.sha256(reference).hexdigest()
    assert payload["questioned_hash"] == hashlib.sha256(questioned).hexdigest()


@pytest.mark.asyncio
async def test_original_hash_preserved_after_document_analysis(
    phase6c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, session_factory, _, _ = phase6c_client
    case = await create_case(client)
    pdf = make_text_pdf()
    evidence = await process_and_extract(
        client,
        case["id"],
        "invoice.pdf",
        pdf,
        "application/pdf",
    )
    expected_hash = hashlib.sha256(pdf).hexdigest()
    assert evidence["sha256_hash"] == expected_hash

    await client.post(f"/api/v1/evidence/{evidence['id']}/document-analysis")

    async with session_factory() as session:
        record = await session.scalar(
            select(Evidence).where(Evidence.id == UUID(str(evidence["id"]))),
        )
        assert record is not None
        assert record.sha256_hash == expected_hash


@pytest.mark.asyncio
async def test_dependency_injection_exposes_document_stack(
    phase6c_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, _, _, application = phase6c_client
    stack = application.state.document_ai_stack
    assert "registry" in stack
    assert "engine" in stack
    assert "tampering" in stack["registry"].names()
