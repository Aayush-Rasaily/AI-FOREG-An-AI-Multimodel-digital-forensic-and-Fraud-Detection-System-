"""Queue abstraction for local and distributed job execution (Phase 10E)."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from backend.app.scaling.workers import WorkerPoolConfig, pool_for_task

logger = logging.getLogger(__name__)

QueueMode = Literal["local", "redis", "celery"]
JobRunner = Callable[[UUID], Awaitable[Any]]


@dataclass(frozen=True, slots=True)
class QueuedJob:
    job_id: UUID
    task_kind: str
    pool: WorkerPoolConfig
    mode: QueueMode


class JobQueue:
    """Enqueue work without changing forensic/business processors."""

    def __init__(self, *, mode: QueueMode = "local") -> None:
        self.mode = mode

    async def enqueue(
        self,
        job_id: UUID,
        *,
        task_kind: str = "default",
        local_runner: JobRunner | None = None,
        background_add: Callable[[Any], None] | None = None,
    ) -> QueuedJob:
        """Dispatch a job to the configured backend.

        Single-node default (`local`) preserves today's BackgroundTasks path.
        """

        pool = pool_for_task(task_kind)
        if self.mode == "local":
            if local_runner is None:
                raise RuntimeError("local_runner is required for local queue mode.")
            if background_add is not None:
                background_add(local_runner(job_id))
            else:
                await local_runner(job_id)
            return QueuedJob(job_id, task_kind, pool, "local")

        if self.mode in {"redis", "celery"}:
            self._enqueue_celery(job_id, task_kind=task_kind, pool=pool)
            return QueuedJob(job_id, task_kind, pool, self.mode)

        raise ValueError(f"Unsupported queue mode: {self.mode}")

    def _enqueue_celery(
        self,
        job_id: UUID,
        *,
        task_kind: str,
        pool: WorkerPoolConfig,
    ) -> None:
        from backend.app.scaling.tasks import dispatch_processing_job

        dispatch_processing_job.apply_async(
            args=[str(job_id), task_kind],
            queue=pool.queue,
        )
        logger.info(
            "Enqueued distributed job",
            extra={
                "job_id": str(job_id),
                "task_kind": task_kind,
                "queue": pool.queue,
            },
        )
