"""Job dispatcher selecting local vs distributed execution (Phase 10E)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks

from backend.app.core.config import Settings, get_settings
from backend.app.scaling.queues import JobQueue, QueuedJob, QueueMode
from backend.app.scaling.workers import pool_for_task


class JobDispatcher:
    """Thin façade so API endpoints stay backend-agnostic."""

    def __init__(self, settings: Settings | None = None) -> None:
        runtime = settings or get_settings()
        mode = getattr(runtime, "job_queue_mode", "local")
        if mode not in {"local", "redis", "celery"}:
            mode = "local"
        self.settings = runtime
        self.queue = JobQueue(mode=mode)  # type: ignore[arg-type]

    @property
    def mode(self) -> QueueMode:
        return self.queue.mode

    async def dispatch_processing(
        self,
        job_id: UUID,
        *,
        runner: Callable[[UUID], Awaitable[Any]],
        background_tasks: BackgroundTasks | None = None,
        task_kind: str = "default",
    ) -> QueuedJob:
        """Queue processing while keeping single-node behavior by default."""

        if self.mode == "local":
            if background_tasks is not None:
                background_tasks.add_task(runner, job_id)
            else:
                await runner(job_id)
            return QueuedJob(job_id, task_kind, pool_for_task(task_kind), "local")

        return await self.queue.enqueue(
            job_id,
            task_kind=task_kind,
            local_runner=runner,
        )


def get_job_dispatcher(settings: Settings | None = None) -> JobDispatcher:
    return JobDispatcher(settings=settings)
