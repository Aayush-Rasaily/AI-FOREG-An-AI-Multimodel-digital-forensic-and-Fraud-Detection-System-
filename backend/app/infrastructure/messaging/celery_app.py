"""Celery application factory for distributed background processing."""

from celery import Celery

from backend.app.core.config import Settings, get_settings
from backend.app.scaling.workers import WORKER_POOLS, celery_queue_routes


def create_celery_app(settings: Settings | None = None) -> Celery:
    """Create a configured Celery application with Phase 10E queue routes."""

    runtime_settings = settings or get_settings()
    celery = Celery(
        runtime_settings.app_name,
        broker=runtime_settings.celery_broker_url,
        backend=runtime_settings.celery_result_backend,
        include=["backend.app.scaling.tasks"],
    )
    queues = {pool.queue for pool in WORKER_POOLS.values()}
    celery.conf.update(
        task_default_queue="ai-forge.default",
        task_queues=None,
        task_routes=celery_queue_routes(),
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        result_expires=3600,
        broker_connection_retry_on_startup=True,
        task_time_limit=3600,
        task_soft_time_limit=3300,
        timezone="UTC",
        enable_utc=True,
        # Documented queue set for worker CLI `-Q` flags.
        worker_direct=False,
    )
    celery.conf.task_create_missing_queues = True
    celery.conf.update(ai_forge_worker_queues=sorted(queues))
    return celery


celery_app = create_celery_app()
