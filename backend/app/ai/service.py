"""Application service for AI model infrastructure."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.ai.cache.manager import CacheManager
from backend.app.ai.config.settings import AISettings
from backend.app.ai.device.manager import DeviceInfo, DeviceManager
from backend.app.ai.inference.engine import AIInferenceEngine
from backend.app.ai.inference.request import InferenceRequest
from backend.app.ai.providers.onnx_provider import ONNXProvider
from backend.app.ai.providers.pytorch_provider import PyTorchProvider
from backend.app.ai.providers.tensorflow_provider import TensorFlowProvider
from backend.app.ai.registry.loader import ModelLoader
from backend.app.ai.registry.registry import ModelRegistry
from backend.app.ai.repository import AIRepository
from backend.app.ai.schemas import (
    AIModelListResponse,
    AIModelResponse,
    InferenceJobListResponse,
    InferenceJobResponse,
    InferenceLogResponse,
)
from backend.app.core.exceptions import ResourceNotFoundError
from backend.app.models.ai import (
    AIModelRecord,
    AIModelStatus,
    InferenceJob,
    InferenceJobStatus,
    InferenceLog,
)

logger = logging.getLogger(__name__)


class AIService:
    """Manage model registry, cache, inference jobs, and persistence."""

    def __init__(
        self,
        session: AsyncSession,
        registry: ModelRegistry,
        loader: ModelLoader,
        cache: CacheManager,
        device_manager: DeviceManager,
        engine: AIInferenceEngine,
        settings: AISettings | None = None,
    ) -> None:
        self.session = session
        self.registry = registry
        self.loader = loader
        self.cache = cache
        self.device_manager = device_manager
        self.engine = engine
        self.settings = settings or AISettings()
        self.repository = AIRepository(session)
        self.providers = (
            PyTorchProvider(),
            ONNXProvider(),
            TensorFlowProvider(),
        )

    async def sync_registry(self) -> None:
        """Persist registry metadata for every registered model."""

        for meta in self.registry.list_metadata():
            existing = await self.repository.get_model_by_name(meta.name)
            if existing is None:
                await self.repository.upsert_model(
                    AIModelRecord(
                        id=uuid4(),
                        name=meta.name,
                        version=meta.version,
                        framework=meta.framework.value,
                        author=meta.author,
                        license=meta.license,
                        input_type=meta.input_type.value,
                        output_type=meta.output_type.value,
                        model_hash=meta.model_hash,
                        required_device=meta.required_device.value,
                        status=AIModelStatus.REGISTERED,
                        metadata_json=meta.to_dict(),
                    )
                )
            else:
                existing.version = meta.version
                existing.framework = meta.framework.value
                existing.metadata_json = meta.to_dict()
        await self.session.commit()

    async def list_models(
        self,
        *,
        limit: int,
        offset: int,
    ) -> AIModelListResponse:
        await self.sync_registry()
        records, total = await self.repository.list_models(limit=limit, offset=offset)
        return AIModelListResponse(
            items=[await self._model_response(record) for record in records],
            total=total,
            limit=limit,
            offset=offset,
            cache_statistics=self.cache.statistics().to_dict(),
            devices=[
                self._device_info(device)
                for device in self.device_manager.list_devices()
            ],
        )

    async def get_model(self, model_id: UUID) -> AIModelResponse:
        record = await self.repository.get_model(model_id)
        if record is None:
            raise ResourceNotFoundError("The requested AI model was not found.")
        return await self._model_response(record)

    async def reload_model(self, model_name: str) -> AIModelResponse:
        if model_name not in self.registry.names():
            raise ResourceNotFoundError("The requested AI model was not found.")
        record = await self.repository.get_model_by_name(model_name)
        if record is None:
            await self.sync_registry()
            record = await self.repository.get_model_by_name(model_name)
        if record is None:
            raise ResourceNotFoundError("The requested AI model was not found.")
        device = self.device_manager.select_device(record.required_device.lower())
        job = InferenceJob(
            id=uuid4(),
            model_record_id=record.id,
            model_name=model_name,
            model_version=record.version,
            task="infrastructure_check",
            device=device,
            status=InferenceJobStatus.RUNNING,
            batch_size=1,
            started_at=datetime.now(UTC),
            metadata_json={"action": "reload"},
        )
        await self.repository.add_job(job)
        await self.repository.add_log(
            InferenceLog(
                id=uuid4(),
                job_id=job.id,
                level="INFO",
                message=f"Reload started for model '{model_name}'.",
            )
        )
        try:
            self.cache.evict(model_name)
            reloaded = self.loader.reload_model(model_name, device=device)
            if self.settings.warmup_on_load:
                reloaded.warmup(batch_size=1)
            self.cache.put(model_name, reloaded, device=device)
            response = await self.engine.run(
                InferenceRequest(
                    model_name=model_name,
                    task="infrastructure_check",
                    payload={"modality": "any", "reload": True},
                    device=device,
                )
            )
            record.status = AIModelStatus.LOADED
            record.current_device = device
            record.last_loaded_at = datetime.now(UTC)
            record.last_latency_ms = response.latency_ms
            record.version = response.model_version
            job.status = InferenceJobStatus.SUCCEEDED
            job.latency_ms = response.latency_ms
            job.finished_at = datetime.now(UTC)
            job.metadata_json = {
                **job.metadata_json,
                "benchmark": response.benchmark,
            }
            await self.repository.add_log(
                InferenceLog(
                    id=uuid4(),
                    job_id=job.id,
                    level="INFO",
                    message="Model reload and warmup inference succeeded.",
                    metadata_json={"latency_ms": response.latency_ms},
                )
            )
            await self.session.commit()
            await self.session.refresh(record)
            return await self._model_response(record)
        except Exception as exc:
            job.status = InferenceJobStatus.FAILED
            job.error_code = "RELOAD_FAILED"
            job.error_message = str(exc)
            job.finished_at = datetime.now(UTC)
            record.status = AIModelStatus.FAILED
            await self.repository.add_log(
                InferenceLog(
                    id=uuid4(),
                    job_id=job.id,
                    level="ERROR",
                    message="Model reload failed.",
                    metadata_json={"error": str(exc)},
                )
            )
            await self.session.commit()
            logger.exception("Model reload failed", extra={"model": model_name})
            raise

    async def list_jobs(
        self,
        *,
        limit: int,
        offset: int,
    ) -> InferenceJobListResponse:
        jobs, total = await self.repository.list_jobs(limit=limit, offset=offset)
        return InferenceJobListResponse(
            items=[self._job_response(job) for job in jobs],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_job(self, job_id: UUID) -> InferenceJobResponse:
        job = await self.repository.get_job(job_id)
        if job is None:
            raise ResourceNotFoundError("The requested inference job was not found.")
        return self._job_response(job)

    async def _model_response(self, record: AIModelRecord) -> AIModelResponse:
        status_value = (
            record.status.value if hasattr(record.status, "value") else record.status
        )
        health: dict[str, object] = {"status": status_value}
        cache_state = self.cache.state(record.name)
        if record.name in self.registry.names():
            try:
                model = self.registry.lookup(record.name)
                health = model.health()
            except KeyError:
                pass
        meta = record.metadata_json
        supported_tasks = meta.get("supported_tasks", [])
        if not isinstance(supported_tasks, list):
            supported_tasks = []
        return AIModelResponse(
            id=record.id,
            name=record.name,
            version=record.version,
            framework=record.framework,
            author=record.author,
            license=record.license,
            input_type=record.input_type,
            output_type=record.output_type,
            model_hash=record.model_hash,
            required_device=record.required_device,
            status=record.status.value,
            current_device=record.current_device,
            last_loaded_at=record.last_loaded_at,
            last_latency_ms=record.last_latency_ms,
            supported_tasks=[str(task) for task in supported_tasks],
            cache_state=cache_state,
            health=health,
            metadata=meta,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    @staticmethod
    def _job_response(job: InferenceJob) -> InferenceJobResponse:
        return InferenceJobResponse(
            id=job.id,
            model_record_id=job.model_record_id,
            model_name=job.model_name,
            model_version=job.model_version,
            task=job.task,
            device=job.device,
            status=job.status.value,
            latency_ms=job.latency_ms,
            batch_size=job.batch_size,
            error_code=job.error_code,
            error_message=job.error_message,
            metadata=job.metadata_json,
            started_at=job.started_at,
            finished_at=job.finished_at,
            created_at=job.created_at,
            logs=[
                InferenceLogResponse(
                    id=log.id,
                    level=log.level,
                    message=log.message,
                    metadata=log.metadata_json,
                    created_at=log.created_at,
                )
                for log in job.logs
            ],
        )

    @staticmethod
    def _device_info(device: DeviceInfo) -> dict[str, object]:
        return {
            "device_type": device.device_type.value,
            "name": device.name,
            "available": device.available,
            "total_memory_mb": device.total_memory_mb,
            "free_memory_mb": device.free_memory_mb,
            "metadata": device.metadata,
        }
