"""Tests for Phase 6A AI inference infrastructure."""

from collections.abc import AsyncIterator

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

from backend.app.ai.bootstrap import build_ai_stack, build_registry
from backend.app.ai.cache.manager import CacheManager
from backend.app.ai.device.manager import DeviceManager
from backend.app.ai.inference.request import InferenceRequest
from backend.app.ai.models.dummy import DummyModel
from backend.app.ai.postprocessing.findings import normalize_raw_output
from backend.app.ai.preprocessing.audio import preprocess_audio, resample_audio
from backend.app.ai.preprocessing.document import preprocess_document
from backend.app.ai.preprocessing.image import ImagePreprocessConfig, preprocess_image
from backend.app.ai.preprocessing.video import preprocess_video
from backend.app.ai.providers.onnx_provider import ONNXProvider
from backend.app.ai.providers.pytorch_provider import PyTorchProvider
from backend.app.ai.providers.tensorflow_provider import TensorFlowProvider
from backend.app.ai.repository import AIRepository
from backend.app.api.dependencies import get_db_session
from backend.app.core.config import Settings
from backend.app.infrastructure.database.base import Base
from backend.app.main import create_app
from backend.app.models.ai import AIModelRecord


@pytest_asyncio.fixture
async def phase6a_client(
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


def test_registry_registers_and_discovers_models() -> None:
    registry = build_registry()
    assert "dummy" in registry.names()
    capabilities = registry.discover_capabilities()
    assert "infrastructure_check" in capabilities["dummy"]


@pytest.mark.asyncio
async def test_dummy_model_is_deterministic() -> None:
    model = DummyModel()
    model.load(device="cpu")
    first = await model.predict({"value": 42})
    second = await model.predict({"value": 42})
    assert first["deterministic_value"] == second["deterministic_value"]
    assert first["infrastructure_check"] == "passed"
    model.unload()


def test_device_manager_selects_cpu_without_gpu() -> None:
    manager = DeviceManager(prefer_gpu=False)
    assert manager.select_device("any") == "cpu"
    devices = manager.list_devices()
    assert any(device.device_type.value == "cpu" for device in devices)


def test_cache_manager_tracks_hits_and_evictions() -> None:
    cache = CacheManager(max_models=1, ttl_seconds=3600)
    model = DummyModel()
    model.load(device="cpu")
    cache.put("dummy", model, device="cpu")
    assert cache.get("dummy") is model
    stats = cache.statistics()
    assert stats.hits == 1
    other = DummyModel()
    other.load(device="cpu")
    cache.put("other", other, device="cpu")
    assert cache.get("dummy") is None
    assert cache.statistics().evictions == 1


def test_provider_interfaces_initialize() -> None:
    for provider in (PyTorchProvider(), ONNXProvider(), TensorFlowProvider()):
        status = provider.initialize()
        assert status.name
        assert isinstance(status.available, bool)


def test_image_preprocessing_resize_and_normalize() -> None:
    array = np.zeros((10, 20, 3), dtype=np.uint8)
    result = preprocess_image(
        array,
        ImagePreprocessConfig(target_width=20, target_height=10, normalize=True),
    )
    assert result["array"].shape == (10, 20, 3)
    assert float(result["array"].max()) <= 1.0


def test_document_video_audio_preprocessing() -> None:
    document = preprocess_document(
        {"mime_type": "application/pdf", "page_count": 2},
    )
    video = preprocess_video({"duration_ms": 1000, "fps": 25, "max_frames": 4})
    audio = preprocess_audio(
        {"sample_rate": 44100, "target_rate": 16000, "samples": [1.0, 2.0]},
    )
    assert document["page_count"] == 2
    assert len(video["samples"]) == 4
    assert audio["sample_rate"] == 16000
    assert resample_audio(
        (1.0, 2.0, 3.0),
        source_rate=3,
        target_rate=3,
    ) == (1.0, 2.0, 3.0)


def test_postprocessing_normalizes_output() -> None:
    normalized = normalize_raw_output(
        model_name="dummy",
        model_version="1.0.0",
        framework="NATIVE",
        task="infrastructure_check",
        raw_output={"infrastructure_check": "passed", "deterministic_value": 123},
    )
    assert normalized.model_name == "dummy"
    assert any(item.name == "infrastructure_check" for item in normalized.items)


@pytest.mark.asyncio
async def test_inference_engine_executes_dummy_model() -> None:
    registry, loader, cache, device_manager, engine = build_ai_stack()
    request = InferenceRequest(
        model_name="dummy",
        task="infrastructure_check",
        payload={"modality": "any", "probe": True},
    )
    response = await engine.run(request)
    assert response.model_name == "dummy"
    assert response.output.task == "infrastructure_check"
    assert response.latency_ms >= 0


@pytest.mark.asyncio
async def test_repository_persists_model_records(
    phase6a_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, session_factory, _, _ = phase6a_client
    async with session_factory() as session:
        repository = AIRepository(session)
        record = AIModelRecord(
            name="dummy",
            version="1.0.0",
            framework="NATIVE",
            author="test",
            license="Proprietary",
            input_type="ANY",
            output_type="INFRASTRUCTURE",
            model_hash="abc",
            required_device="ANY",
        )
        await repository.upsert_model(record)
        await session.commit()
        loaded = await repository.get_model_by_name("dummy")
        assert loaded is not None
        assert loaded.version == "1.0.0"


@pytest.mark.asyncio
async def test_ai_api_lists_models_and_jobs(
    phase6a_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    client, _, _, _ = phase6a_client
    models = await client.get("/api/v1/models")
    assert models.status_code == 200
    body = models.json()["data"]
    assert body["total"] >= 1
    assert any(item["name"] == "dummy" for item in body["items"])

    reload = await client.post(
        "/api/v1/models/reload",
        json={"model_name": "dummy"},
    )
    assert reload.status_code == 200
    assert reload.json()["data"]["status"] == "LOADED"

    jobs = await client.get("/api/v1/inference/jobs")
    assert jobs.status_code == 200
    assert jobs.json()["data"]["total"] >= 1

    job_id = jobs.json()["data"]["items"][0]["id"]
    job = await client.get(f"/api/v1/inference/jobs/{job_id}")
    assert job.status_code == 200
    assert job.json()["data"]["model_name"] == "dummy"


@pytest.mark.asyncio
async def test_dependency_injection_exposes_shared_registry(
    phase6a_client: tuple[
        httpx.AsyncClient,
        async_sessionmaker[AsyncSession],
        AsyncEngine,
        FastAPI,
    ],
) -> None:
    _, _, _, application = phase6a_client
    stack = application.state.ai_stack
    assert "registry" in stack
    assert "dummy" in stack["registry"].names()


def test_benchmark_metrics_track_latency() -> None:
    from backend.app.ai.benchmarking.metrics import BenchmarkMetrics

    metrics = BenchmarkMetrics(batch_size=2, device="cpu")
    metrics.load_time_ms = 12.5
    metrics.cache_hit = True
    payload = metrics.to_dict()
    assert payload["batch_size"] == 2
    assert payload["cache_hit"] is True
