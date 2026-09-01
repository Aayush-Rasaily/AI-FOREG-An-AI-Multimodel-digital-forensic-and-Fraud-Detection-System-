"""Tests for Phase 6D AI video forensic analysis."""

import hashlib
from collections.abc import AsyncIterator
from uuid import UUID

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

from backend.app.ai.video.bootstrap import build_video_analysis_stack
from backend.app.ai.video.config import VideoAISettings
from backend.app.ai.video.detectors._utils import verify_model_hash
from backend.app.ai.video.detectors.deepfake import DeepfakeVideoDetector
from backend.app.ai.video.detectors.synthetic_video import SyntheticVideoDetector
from backend.app.ai.video.exceptions import ModelIntegrityError
from backend.app.ai.video.models.context import VideoAnalysisContext
from backend.app.ai.video.preprocessing.frames import (
    build_frame_schedule,
    frame_identifier,
    schedule_from_frame_index,
)
from backend.app.ai.video.registry import VideoDetectorRegistry
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.domain.processing import EvidenceClassification
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from tests.test_phase4_processing import create_case, process_and_extract


@pytest_asyncio.fixture
async def phase6d_client(
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


def test_registry_registers_all_detectors() -> None:
    registry, _, _ = build_video_analysis_stack()
    names = set(registry.names())
    assert names == {
        "compression",
        "deepfake",
        "face_consistency",
        "frame_manipulation",
        "metadata",
        "synthetic_video",
        "temporal",
    }


def test_frame_identifier_is_deterministic() -> None:
    first = frame_identifier("abc123", 0, 5000)
    second = frame_identifier("abc123", 0, 5000)
    third = frame_identifier("abc123", 1, 5000)
    assert first == second
    assert first != third
    assert len(first) == 64


def test_build_frame_schedule_respects_bounds() -> None:
    frames = build_frame_schedule(
        duration_seconds=60.0,
        interval_seconds=5.0,
        max_frames=10,
        source_sha256="deadbeef",
    )
    assert len(frames) == 10
    assert frames[0].timestamp_ms == 0
    assert frames[0].frame_id == frame_identifier("deadbeef", 0, 0)


def test_schedule_from_frame_index_uses_requested_frames() -> None:
    frame_index = {
        "requested_frames": [
            {"frame_number": 1, "timestamp_ms": 0},
            {"frame_number": 2, "timestamp_ms": 5000},
        ]
    }
    frames = schedule_from_frame_index(
        frame_index,
        source_sha256="hash",
        interval_seconds=5.0,
        max_frames=120,
        duration_seconds=10.0,
    )
    assert len(frames) == 2
    assert frames[1].timestamp_ms == 5000


@pytest.mark.asyncio
async def test_deepfake_detector_unavailable_without_model() -> None:
    detector = DeepfakeVideoDetector(VideoAISettings())
    detector.load(device="cpu")
    context = VideoAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000001"),
        case_id=UUID("00000000-0000-0000-0000-000000000002"),
        original_filename="clip.mp4",
        mime_type="video/mp4",
        storage_key="evidence/clip.mp4",
        classification=EvidenceClassification.VIDEO,
        source_sha256="a" * 64,
        storage=None,
        settings=None,
        video_settings=VideoAISettings(),
    )
    output = await detector.predict(context)
    assert len(output.findings) == 1
    finding = output.findings[0]
    assert finding.confidence is None
    assert finding.metadata["reason"] == "model_not_configured"


@pytest.mark.asyncio
async def test_synthetic_detector_unavailable_without_model() -> None:
    detector = SyntheticVideoDetector(VideoAISettings())
    detector.load(device="cpu")
    context = VideoAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000001"),
        case_id=UUID("00000000-0000-0000-0000-000000000002"),
        original_filename="clip.mp4",
        mime_type="video/mp4",
        storage_key="evidence/clip.mp4",
        classification=EvidenceClassification.VIDEO,
        source_sha256="a" * 64,
        storage=None,
        settings=None,
        video_settings=VideoAISettings(),
    )
    output = await detector.predict(context)
    assert output.findings[0].confidence is None


def test_model_hash_validation_raises_on_mismatch(tmp_path) -> None:
    model_file = tmp_path / "model.bin"
    model_file.write_bytes(b"weights")
    expected = hashlib.sha256(b"other").hexdigest()
    with pytest.raises(ModelIntegrityError):
        verify_model_hash(model_file, expected)


@pytest.mark.asyncio
async def test_video_analysis_api_queues_and_returns_findings(
    phase6d_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, _, _, _ = phase6d_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "clip.mp4",
        b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32,
        "video/mp4",
    )
    original_hash = evidence["sha256_hash"]
    queued = await client.post(
        f"/api/v1/evidence/{evidence['id']}/video-analysis",
    )
    assert queued.status_code == 202

    runs = await client.get(
        f"/api/v1/evidence/{evidence['id']}/video-analysis",
    )
    assert runs.status_code == 200
    assert runs.json()["data"]["total"] >= 0

    findings = await client.get(
        f"/api/v1/evidence/{evidence['id']}/video-findings",
    )
    assert findings.status_code == 200

    refreshed = await client.get(f"/api/v1/evidence/{evidence['id']}")
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["sha256_hash"] == original_hash


@pytest.mark.asyncio
async def test_dependency_injection_exposes_video_stack(
    phase6d_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, _, _, application = phase6d_client
    stack = application.state.video_ai_stack
    assert "registry" in stack
    assert "engine" in stack
    assert isinstance(stack["registry"], VideoDetectorRegistry)
