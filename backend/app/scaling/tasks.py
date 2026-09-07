"""Celery tasks that wrap existing orchestrators without logic changes."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from backend.app.infrastructure.messaging.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


@celery_app.task(name="backend.app.scaling.tasks.dispatch_processing_job")
def dispatch_processing_job(job_id: str, task_kind: str = "default") -> str:
    """Execute ProcessingOrchestrator.run(job_id) on a worker process."""

    async def _inner() -> str:
        from backend.app.application.services.hashing import HashService
        from backend.app.application.services.processing_service import (
            ProcessingOrchestrator,
        )
        from backend.app.core.config import get_settings
        from backend.app.infrastructure.database.session import get_session_factory
        from backend.app.scaling.storage_factory import create_storage_service

        settings = get_settings()
        session_factory = get_session_factory()
        async with session_factory() as session:
            storage = create_storage_service(settings)
            orchestrator = ProcessingOrchestrator(
                session=session,
                storage=storage,
                hash_service=HashService(),
                settings=settings,
            )
            await orchestrator.run(UUID(job_id))
        logger.info(
            "Distributed processing job completed",
            extra={"job_id": job_id, "task_kind": task_kind},
        )
        return job_id

    return _run_async(_inner())
