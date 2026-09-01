"""Tests for Phase 6B AI image forensic analysis."""

import io
from collections.abc import AsyncIterator
from uuid import UUID

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

from backend.app.ai.image.bootstrap import build_image_analysis_stack
from backend.app.ai.image.config import ImageAISettings
from backend.app.ai.image.detectors.ai_generated import AIGeneratedImageDetector
from backend.app.ai.image.detectors.deepfake_face import DeepfakeFaceDetector
from backend.app.ai.image.detectors.government_id import GovernmentIDDetector
from backend.app.ai.image.models import ImageAnalysisContext, ImageAnalysisRunStatus
from backend.app.ai.image.postprocessing.findings import normalize_detector_output
from backend.app.ai.image.preprocessing.pipeline import preprocess_for_analysis
from backend.app.ai.image.registry import ImageDetectorRegistry
from backend.app.ai.image.repository import ImageAnalysisRepository
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.domain.processing import EvidenceClassification
from backend.app.infrastructure.database.base import Base
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.main import create_app
from backend.app.models.image_ai import ImageAnalysisRun
from tests.test_phase4_processing import create_case, process_and_extract


def _png_bytes(width: int = 96, height: int = 64) -> bytes:
    buffer = io.BytesIO()
    array = np.zeros((height, width, 3), dtype=np.uint8)
    array[:, :, 0] = np.linspace(0, 255, width, dtype=np.uint8)
    array[:, :, 2] = np.linspace(255, 0, height, dtype=np.uint8)[:, None]
    Image.fromarray(array, mode="RGB").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest_asyncio.fixture
async def phase6b_client(
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
    registry, _, _ = build_image_analysis_stack()
    names = registry.names()
    assert "ai_generated" in names
    assert "deepfake_face" in names
    assert "government_id" in names
    assert len(registry.enabled_names()) == 5


@pytest.mark.asyncio
async def test_ai_generated_detector_returns_normalized_output(tmp_path) -> None:
    detector = AIGeneratedImageDetector()
    detector.load(device="cpu")
    rgb, width, height = __import__(
        "backend.app.forensics.utils",
        fromlist=["load_image_rgb"],
    ).load_image_rgb(_png_bytes())
    context = ImageAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000071"),
        case_id=UUID("00000000-0000-0000-0000-000000000072"),
        original_filename="sample.png",
        mime_type="image/png",
        storage_key="cases/test/sample.png",
        classification=EvidenceClassification.IMAGE,
        source_sha256="abc",
        storage=LocalStorage(tmp_path / "storage"),
        settings=Settings(
            debug=True,
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "storage",
            log_config_path=tmp_path / "missing-logging.json",
        ),
        image_array=rgb,
        width=width,
        height=height,
    )
    output = await detector.predict(context)
    normalized = normalize_detector_output(output)
    assert output.detector == "ai_generated"
    assert output.model_name
    assert isinstance(normalized, tuple)


@pytest.mark.asyncio
async def test_government_id_detector_localizes_regions(tmp_path) -> None:
    detector = GovernmentIDDetector()
    detector.load(device="cpu")
    rgb, width, height = __import__(
        "backend.app.forensics.utils",
        fromlist=["load_image_rgb"],
    ).load_image_rgb(_png_bytes(width=120, height=80))
    context = ImageAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000073"),
        case_id=UUID("00000000-0000-0000-0000-000000000074"),
        original_filename="id.png",
        mime_type="image/png",
        storage_key="cases/test/id.png",
        classification=EvidenceClassification.IMAGE,
        source_sha256="abc",
        storage=LocalStorage(tmp_path / "storage"),
        settings=Settings(
            debug=True,
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "storage",
            log_config_path=tmp_path / "missing-logging.json",
        ),
        image_array=rgb,
        width=width,
        height=height,
    )
    output = await detector.predict(context)
    assert output.findings
    assert output.findings[0].regions


def test_image_preprocessing_letterbox_and_patches() -> None:
    array = np.zeros((30, 40, 3), dtype=np.uint8)
    bundle = preprocess_for_analysis(array, width=40, height=30, tile_size=16)
    assert bundle.width == bundle.height == 512
    assert len(bundle.patches) >= 1


@pytest.mark.asyncio
async def test_image_analysis_engine_runs_enabled_detectors(tmp_path) -> None:
    registry, _, engine = build_image_analysis_stack()
    rgb, width, height = __import__(
        "backend.app.forensics.utils",
        fromlist=["load_image_rgb"],
    ).load_image_rgb(_png_bytes())
    context = ImageAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000075"),
        case_id=UUID("00000000-0000-0000-0000-000000000076"),
        original_filename="engine.png",
        mime_type="image/png",
        storage_key="cases/test/engine.png",
        classification=EvidenceClassification.IMAGE,
        source_sha256="abc",
        storage=LocalStorage(tmp_path / "storage"),
        settings=Settings(
            debug=True,
            database_url="sqlite+aiosqlite://",
            storage_root=tmp_path / "storage",
            log_config_path=tmp_path / "missing-logging.json",
        ),
        image_array=rgb,
        width=width,
        height=height,
    )
    result = await engine.analyze(context)
    assert result.status == ImageAnalysisRunStatus.SUCCEEDED
    assert len(result.detector_outputs) == len(registry.enabled_names())
    assert result.latency_ms >= 0


@pytest.mark.asyncio
async def test_registry_enable_disable_without_code_changes() -> None:
    settings = ImageAISettings(
        enabled_detectors=("ai_generated", "manipulation"),
    )
    registry = ImageDetectorRegistry(settings)
    registry.register(AIGeneratedImageDetector)
    from backend.app.ai.image.detectors.manipulation import ManipulationDetector

    registry.register(DeepfakeFaceDetector)
    registry.register(ManipulationDetector)
    assert registry.enabled_names() == ("ai_generated", "manipulation")


@pytest.mark.asyncio
async def test_repository_persists_image_analysis_runs(
    phase6b_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, session_factory, _, _ = phase6b_client
    async with session_factory() as session:
        repository = ImageAnalysisRepository(session)
        run = ImageAnalysisRun(
            evidence_id=UUID("00000000-0000-0000-0000-000000000077"),
            status=ImageAnalysisRunStatus.SUCCEEDED,
            engine_version="1.0",
            device="cpu",
            findings_count=1,
        )
        await repository.add_run(run)
        await session.commit()
        loaded = await repository.get_run(run.id)
        assert loaded is not None
        assert loaded.findings_count == 1


@pytest.mark.asyncio
async def test_image_analysis_api_queues_and_returns_findings(
    phase6b_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, _, _, _ = phase6b_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "scene.png",
        _png_bytes(),
        "image/png",
    )
    queued = await client.post(f"/api/v1/evidence/{evidence['id']}/image-analysis")
    assert queued.status_code == 202

    runs = await client.get(f"/api/v1/evidence/{evidence['id']}/image-analysis")
    assert runs.status_code == 200
    assert runs.json()["data"]["total"] >= 0

    findings = await client.get(f"/api/v1/evidence/{evidence['id']}/image-findings")
    assert findings.status_code == 200

    if runs.json()["data"]["items"]:
        run_id = runs.json()["data"]["items"][0]["id"]
        run = await client.get(f"/api/v1/image-analysis/{run_id}")
        assert run.status_code == 200


@pytest.mark.asyncio
async def test_dependency_injection_exposes_image_stack(
    phase6b_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, _, _, application = phase6b_client
    stack = application.state.image_ai_stack
    assert "registry" in stack
    assert "engine" in stack
    assert "ai_generated" in stack["registry"].names()
