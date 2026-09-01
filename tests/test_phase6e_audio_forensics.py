"""Tests for Phase 6E AI audio forensic analysis."""

from __future__ import annotations

import hashlib
import io
import wave
from collections.abc import AsyncIterator
from uuid import UUID

import httpx
import numpy as np
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

from backend.app.ai.audio.bootstrap import build_audio_analysis_stack
from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.audio.detectors._utils import verify_model_hash
from backend.app.ai.audio.detectors.deepfake_voice import DeepfakeVoiceDetector
from backend.app.ai.audio.detectors.synthetic_audio import SyntheticAudioDetector
from backend.app.ai.audio.engine import AudioAnalysisEngine
from backend.app.ai.audio.exceptions import ModelIntegrityError
from backend.app.ai.audio.features.waveform import (
    rms_energy,
    simplified_mfcc,
    spectral_centroid,
    zero_crossing_rate,
)
from backend.app.ai.audio.models import AudioAnalysisContext
from backend.app.ai.audio.postprocessing.aggregation import (
    build_segments,
    build_timeline,
)
from backend.app.ai.audio.preprocessing.audio import (
    build_feature_summary,
    load_wav_bytes,
)
from backend.app.ai.audio.registry import AudioDetectorRegistry
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.domain.processing import EvidenceClassification
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from tests.test_phase4_processing import create_case, process_and_extract


def make_test_wav(
    *,
    sample_rate: int = 16_000,
    seconds: float = 1.0,
    frequency: float = 440.0,
    splice_at: float | None = None,
) -> bytes:
    frame_count = int(sample_rate * seconds)
    t = np.linspace(0, seconds, frame_count, endpoint=False)
    signal = (0.3 * np.sin(2 * np.pi * frequency * t)).astype(np.float32)
    if splice_at is not None:
        split = int(sample_rate * splice_at)
        signal[split:] = 0.05 * np.sin(2 * np.pi * 880.0 * t[split:])
    pcm = np.clip(signal * 32767, -32768, 32767).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(sample_rate)
        stream.writeframes(pcm.tobytes())
    return buffer.getvalue()


@pytest_asyncio.fixture
async def phase6e_client(
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
    registry, _, _ = build_audio_analysis_stack()
    names = set(registry.names())
    assert names == {
        "compression",
        "deepfake_voice",
        "metadata",
        "noise_consistency",
        "silence",
        "speaker_consistency",
        "spectral",
        "splicing",
        "synthetic_audio",
        "voice_clone",
        "waveform",
    }


def test_load_wav_bytes_and_feature_summary() -> None:
    data = make_test_wav(sample_rate=16_000, seconds=0.5)
    loaded = load_wav_bytes(data, max_samples=100_000, target_sample_rate=16_000)
    assert loaded is not None
    assert loaded.sample_rate == 16_000
    assert loaded.samples.size > 0
    summary = build_feature_summary(
        loaded,
        window_seconds=0.25,
        hop_seconds=0.125,
    )
    assert summary.sample_rate == 16_000
    assert summary.rms_energy > 0
    assert summary.window_count >= 1


def test_waveform_features_are_deterministic() -> None:
    data = make_test_wav()
    loaded = load_wav_bytes(data, max_samples=100_000, target_sample_rate=16_000)
    assert loaded is not None
    first = (
        rms_energy(loaded.samples),
        zero_crossing_rate(loaded.samples),
        spectral_centroid(loaded.samples, loaded.sample_rate),
        tuple(simplified_mfcc(loaded.samples, loaded.sample_rate)),
    )
    second = (
        rms_energy(loaded.samples),
        zero_crossing_rate(loaded.samples),
        spectral_centroid(loaded.samples, loaded.sample_rate),
        tuple(simplified_mfcc(loaded.samples, loaded.sample_rate)),
    )
    assert first == second


@pytest.mark.asyncio
async def test_synthetic_detector_unavailable_without_model() -> None:
    detector = SyntheticAudioDetector(AudioAISettings())
    detector.load(device="cpu")
    context = AudioAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000001"),
        case_id=UUID("00000000-0000-0000-0000-000000000002"),
        original_filename="clip.wav",
        mime_type="audio/wav",
        storage_key="evidence/clip.wav",
        classification=EvidenceClassification.AUDIO,
        source_sha256="a" * 64,
        storage=None,
        settings=None,
        audio_settings=AudioAISettings(),
    )
    output = await detector.predict(context)
    assert len(output.findings) == 1
    assert output.findings[0].confidence is None
    assert output.findings[0].metadata["reason"] == "model_not_configured"


@pytest.mark.asyncio
async def test_deepfake_voice_detector_unavailable_without_model() -> None:
    detector = DeepfakeVoiceDetector(AudioAISettings())
    detector.load(device="cpu")
    context = AudioAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000001"),
        case_id=UUID("00000000-0000-0000-0000-000000000002"),
        original_filename="clip.wav",
        mime_type="audio/wav",
        storage_key="evidence/clip.wav",
        classification=EvidenceClassification.AUDIO,
        source_sha256="a" * 64,
        storage=None,
        settings=None,
        audio_settings=AudioAISettings(),
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
async def test_engine_analyzes_wav_deterministically(tmp_path) -> None:
    from backend.app.core.config import Settings
    from backend.app.infrastructure.storage.local import LocalStorage

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    wav = make_test_wav(splice_at=0.5)
    key = "evidence/test.wav"
    await storage.save_stream(
        io.BytesIO(wav),
        key,
        max_bytes=10_000_000,
        chunk_size=1024,
    )
    _, _, engine = build_audio_analysis_stack()
    context = AudioAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000011"),
        case_id=UUID("00000000-0000-0000-0000-000000000012"),
        original_filename="test.wav",
        mime_type="audio/wav",
        storage_key=key,
        classification=EvidenceClassification.AUDIO,
        source_sha256=hashlib.sha256(wav).hexdigest(),
        storage=storage,
        settings=settings,
        audio_settings=AudioAISettings(),
        codec="wav",
        sample_rate=16_000,
        channels=1,
    )
    first = await engine.analyze(context)
    second = await engine.analyze(context)
    assert first.status.value == "SUCCEEDED"
    assert second.status.value == "SUCCEEDED"
    assert len(first.findings) == len(second.findings)
    assert [item.description for item in first.findings] == [
        item.description for item in second.findings
    ]


def test_timeline_localization_from_findings() -> None:
    from backend.app.ai.audio.models import (
        AudioAIFindingItem,
        AudioFindingCategory,
        DetectionMethod,
        TemporalEvidence,
    )
    from backend.app.forensics.models import Severity

    finding = AudioAIFindingItem(
        detector="waveform",
        category=AudioFindingCategory.WAVEFORM,
        severity=Severity.LOW,
        description="Amplitude discontinuity observed.",
        explanation="test",
        method=DetectionMethod.CLASSICAL,
        confidence=0.5,
        temporal=TemporalEvidence(
            start_time_ms=4200,
            end_time_ms=5100,
            duration_ms=900,
        ),
    )
    timeline = build_timeline((finding,))
    segments = build_segments((finding,))
    assert timeline[0]["start_time_ms"] == 4200
    assert segments[0]["segment_id"] == "waveform:0"


@pytest.mark.asyncio
async def test_reference_voice_comparison(tmp_path) -> None:
    from backend.app.core.config import Settings
    from backend.app.infrastructure.storage.local import LocalStorage

    settings = Settings(
        debug=True,
        database_url="sqlite+aiosqlite://",
        storage_root=tmp_path / "data",
        log_config_path=tmp_path / "missing-logging.json",
    )
    storage = LocalStorage(settings.storage_root)
    questioned = make_test_wav(frequency=440.0)
    reference = make_test_wav(frequency=440.0)
    key = "evidence/q.wav"
    ref_key = "evidence/r.wav"
    for payload, storage_key in ((questioned, key), (reference, ref_key)):
        await storage.save_stream(
            io.BytesIO(payload),
            storage_key,
            max_bytes=10_000_000,
            chunk_size=1024,
        )
    loaded_ref = load_wav_bytes(
        reference,
        max_samples=100_000,
        target_sample_rate=16_000,
    )
    assert loaded_ref is not None
    _, _, engine = build_audio_analysis_stack()
    context = AudioAnalysisContext(
        evidence_id=UUID("00000000-0000-0000-0000-000000000021"),
        case_id=UUID("00000000-0000-0000-0000-000000000022"),
        original_filename="q.wav",
        mime_type="audio/wav",
        storage_key=key,
        classification=EvidenceClassification.AUDIO,
        source_sha256=hashlib.sha256(questioned).hexdigest(),
        storage=storage,
        settings=settings,
        audio_settings=AudioAISettings(),
        reference_evidence_id=UUID("00000000-0000-0000-0000-000000000023"),
        reference_samples=loaded_ref.samples,
        reference_sample_rate=loaded_ref.sample_rate,
    )
    result = await engine.analyze(context)
    categories = {item.category.value for item in result.findings}
    assert "REFERENCE_MISMATCH" in categories


def test_invalid_audio_returns_none_on_decode() -> None:
    loaded = load_wav_bytes(b"not-wav", max_samples=1000, target_sample_rate=16_000)
    assert loaded is None


@pytest.mark.asyncio
async def test_audio_analysis_api_lifecycle(
    phase6e_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, _, _, _ = phase6e_client
    case = await create_case(client)
    wav = make_test_wav(seconds=0.25)
    evidence = await process_and_extract(
        client,
        case["id"],
        "sample.wav",
        wav,
        "audio/wav",
    )
    original_hash = evidence["sha256_hash"]
    queued = await client.post(
        f"/api/v1/evidence/{evidence['id']}/audio-analysis",
        json={},
    )
    assert queued.status_code == 202

    runs = await client.get(
        f"/api/v1/evidence/{evidence['id']}/audio-analysis",
    )
    assert runs.status_code == 200
    assert runs.json()["data"]["total"] >= 1
    run_id = runs.json()["data"]["items"][0]["id"]

    detail = await client.get(f"/api/v1/audio-analysis/{run_id}")
    assert detail.status_code == 200

    findings = await client.get(
        f"/api/v1/evidence/{evidence['id']}/audio-findings",
    )
    assert findings.status_code == 200

    timeline = await client.get(f"/api/v1/audio-analysis/{run_id}/timeline")
    assert timeline.status_code == 200

    segments = await client.get(f"/api/v1/audio-analysis/{run_id}/segments")
    assert segments.status_code == 200

    features = await client.get(f"/api/v1/audio-analysis/{run_id}/features")
    assert features.status_code == 200

    refreshed = await client.get(f"/api/v1/evidence/{evidence['id']}")
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["sha256_hash"] == original_hash


@pytest.mark.asyncio
async def test_unsupported_evidence_rejected(
    phase6e_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, _, _, _ = phase6e_client
    case = await create_case(client)
    evidence = await process_and_extract(
        client,
        case["id"],
        "clip.mp4",
        b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32,
        "video/mp4",
    )
    response = await client.post(
        f"/api/v1/evidence/{evidence['id']}/audio-analysis",
        json={},
    )
    assert response.status_code == 422 or response.status_code == 400


@pytest.mark.asyncio
async def test_dependency_injection_exposes_audio_stack(
    phase6e_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, _, _, application = phase6e_client
    stack = application.state.audio_ai_stack
    assert "engine" in stack
    assert isinstance(stack["engine"], AudioAnalysisEngine)
    assert isinstance(stack["registry"], AudioDetectorRegistry)


def test_migration_module_and_metadata_tables() -> None:
    import importlib.util
    from pathlib import Path

    migration_path = (
        Path(__file__).resolve().parents[1]
        / "backend"
        / "alembic"
        / "versions"
        / "20260831_0010_add_audio_ai.py"
    )
    spec = importlib.util.spec_from_file_location("migration_0010", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    assert callable(migration.upgrade)
    assert callable(migration.downgrade)
    assert migration.revision == "20260831_0010"
    assert migration.down_revision == "20260831_0009"
    tables = Base.metadata.tables
    assert "audio_analysis_runs" in tables
    assert "audio_ai_findings" in tables
    assert "audio_ai_finding_regions" in tables
