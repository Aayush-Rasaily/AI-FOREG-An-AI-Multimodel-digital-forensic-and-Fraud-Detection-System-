"""Configurable background worker pool definitions (Phase 10E)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class WorkerPoolName(StrEnum):
    EXTRACTION = "extraction"
    OCR = "ocr"
    IMAGE_AI = "image_ai"
    DOCUMENT_AI = "document_ai"
    SIGNATURE_AI = "signature_ai"
    VIDEO_AI = "video_ai"
    AUDIO_AI = "audio_ai"
    FUSION = "fusion"
    CORRELATION = "correlation"
    REPORTING = "reporting"
    DEFAULT = "default"


@dataclass(frozen=True, slots=True)
class WorkerPoolConfig:
    """Declarative pool sizing for one workload class."""

    name: WorkerPoolName
    queue: str
    concurrency: int
    prefetch: int = 1
    soft_time_limit_seconds: int = 1800
    hard_time_limit_seconds: int = 2100


WORKER_POOLS: dict[WorkerPoolName, WorkerPoolConfig] = {
    WorkerPoolName.EXTRACTION: WorkerPoolConfig(
        WorkerPoolName.EXTRACTION, "ai-forge.extraction", concurrency=4
    ),
    WorkerPoolName.OCR: WorkerPoolConfig(
        WorkerPoolName.OCR, "ai-forge.ocr", concurrency=2
    ),
    WorkerPoolName.IMAGE_AI: WorkerPoolConfig(
        WorkerPoolName.IMAGE_AI, "ai-forge.image-ai", concurrency=2
    ),
    WorkerPoolName.DOCUMENT_AI: WorkerPoolConfig(
        WorkerPoolName.DOCUMENT_AI, "ai-forge.document-ai", concurrency=2
    ),
    WorkerPoolName.SIGNATURE_AI: WorkerPoolConfig(
        WorkerPoolName.SIGNATURE_AI, "ai-forge.signature-ai", concurrency=2
    ),
    WorkerPoolName.VIDEO_AI: WorkerPoolConfig(
        WorkerPoolName.VIDEO_AI, "ai-forge.video-ai", concurrency=1
    ),
    WorkerPoolName.AUDIO_AI: WorkerPoolConfig(
        WorkerPoolName.AUDIO_AI, "ai-forge.audio-ai", concurrency=2
    ),
    WorkerPoolName.FUSION: WorkerPoolConfig(
        WorkerPoolName.FUSION, "ai-forge.fusion", concurrency=2
    ),
    WorkerPoolName.CORRELATION: WorkerPoolConfig(
        WorkerPoolName.CORRELATION, "ai-forge.correlation", concurrency=2
    ),
    WorkerPoolName.REPORTING: WorkerPoolConfig(
        WorkerPoolName.REPORTING, "ai-forge.reporting", concurrency=2
    ),
    WorkerPoolName.DEFAULT: WorkerPoolConfig(
        WorkerPoolName.DEFAULT, "ai-forge.default", concurrency=4
    ),
}


QueueBackend = Literal["local", "redis", "celery"]


def pool_for_task(task_kind: str) -> WorkerPoolConfig:
    """Map a logical task kind onto a configured pool."""

    normalized = task_kind.lower().replace("-", "_")
    try:
        name = WorkerPoolName(normalized)
    except ValueError:
        name = WorkerPoolName.DEFAULT
    return WORKER_POOLS[name]


def celery_queue_routes() -> dict[str, dict[str, str]]:
    """Return Celery task_routes keyed by symbolic task name."""

    return {
        f"backend.app.scaling.tasks.{pool.name.value}": {"queue": pool.queue}
        for pool in WORKER_POOLS.values()
    }
