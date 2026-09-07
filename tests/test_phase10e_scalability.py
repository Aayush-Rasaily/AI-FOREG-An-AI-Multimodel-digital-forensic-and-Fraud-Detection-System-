"""Tests for Phase 10E scalability and high availability."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from backend.app.core.config import Settings
from backend.app.infrastructure.storage.local import LocalStorage
from backend.app.scaling.balancing import (
    balancing_guidance,
    recommend_sticky_sessions,
)
from backend.app.scaling.cache import CacheNamespace, CacheTTL, namespaced_key, ttl_for
from backend.app.scaling.database import pool_kwargs, resolve_database_url
from backend.app.scaling.dispatcher import JobDispatcher
from backend.app.scaling.queues import JobQueue
from backend.app.scaling.scheduler import worker_pool_summary
from backend.app.scaling.storage_factory import create_storage_service
from backend.app.scaling.workers import WORKER_POOLS, WorkerPoolName, pool_for_task

REPO_ROOT = Path(__file__).resolve().parents[1]
K8S = REPO_ROOT / "deployment" / "k8s"


class TestWorkerPools:
    def test_required_pools_present(self) -> None:
        required = {
            WorkerPoolName.EXTRACTION,
            WorkerPoolName.OCR,
            WorkerPoolName.IMAGE_AI,
            WorkerPoolName.DOCUMENT_AI,
            WorkerPoolName.SIGNATURE_AI,
            WorkerPoolName.VIDEO_AI,
            WorkerPoolName.AUDIO_AI,
            WorkerPoolName.FUSION,
            WorkerPoolName.CORRELATION,
            WorkerPoolName.REPORTING,
        }
        assert required.issubset(set(WORKER_POOLS))
        assert pool_for_task("image-ai").queue == "ai-forge.image-ai"
        assert worker_pool_summary()


class TestDispatcherLocalParity:
    @pytest.mark.asyncio
    async def test_local_dispatch_invokes_runner(self) -> None:
        called: list[str] = []

        async def runner(job_id):  # type: ignore[no-untyped-def]
            called.append(str(job_id))

        settings = Settings(job_queue_mode="local")
        dispatcher = JobDispatcher(settings)
        job_id = uuid4()
        queued = await dispatcher.dispatch_processing(job_id, runner=runner)
        assert queued.mode == "local"
        assert called == [str(job_id)]

    @pytest.mark.asyncio
    async def test_local_queue_requires_runner(self) -> None:
        queue = JobQueue(mode="local")
        with pytest.raises(RuntimeError):
            await queue.enqueue(uuid4())


class TestCacheAndDatabase:
    def test_namespaced_keys_and_ttl(self) -> None:
        key = namespaced_key(CacheNamespace.HTTP, "models", "50")
        assert key.startswith("ai_forge:cache:http:")
        assert ttl_for(CacheTTL.SHORT) == 15

    def test_read_replica_url_optional(self) -> None:
        settings = Settings(
            database_url="postgresql+psycopg://write/db",
            database_read_url="postgresql+psycopg://read/db",
        )
        assert resolve_database_url(settings, prefer_read=False).endswith("write/db")
        assert resolve_database_url(settings, prefer_read=True).endswith("read/db")
        assert "pool_size" in pool_kwargs(
            Settings(database_url="postgresql+psycopg://localhost/db")
        )


class TestStorageFactory:
    def test_local_default(self, tmp_path: Path) -> None:
        settings = Settings(storage_backend="local", storage_root=tmp_path / "data")
        storage = create_storage_service(settings)
        assert isinstance(storage, LocalStorage)

    def test_s3_adapter_constructs(self) -> None:
        settings = Settings(
            storage_backend="s3",
            object_storage_bucket="bucket",
            object_storage_endpoint="http://localhost:9000",
        )
        storage = create_storage_service(settings)
        assert storage.temporary_key().startswith(".tmp/")


class TestBalancingAndArtifacts:
    def test_sticky_only_for_local_storage(self) -> None:
        assert recommend_sticky_sessions(uses_local_storage=True) == "cookie"
        assert recommend_sticky_sessions(uses_local_storage=False) == "none"
        guidance = balancing_guidance()
        assert guidance["stateless_api"] is True

    def test_docs_and_k8s_manifests(self) -> None:
        assert (REPO_ROOT / "docs" / "scalability.md").is_file()
        for name in (
            "hpa-pdb.yaml",
            "worker-deployment.yaml",
            "backend-deployment.yaml",
        ):
            path = K8S / name
            assert path.is_file()
            docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            assert docs
        backend = yaml.safe_load_all(
            (K8S / "backend-deployment.yaml").read_text(encoding="utf-8")
        )
        deployment = next(backend)
        assert deployment["spec"]["strategy"]["type"] == "RollingUpdate"
        hpa_docs = list(
            yaml.safe_load_all((K8S / "hpa-pdb.yaml").read_text(encoding="utf-8"))
        )
        kinds = {doc["kind"] for doc in hpa_docs}
        assert "HorizontalPodAutoscaler" in kinds
        assert "PodDisruptionBudget" in kinds
