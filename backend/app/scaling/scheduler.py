"""Periodic / coordinated scheduling helpers (Phase 10E)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from backend.app.scaling.cache import distributed_lock
from backend.app.scaling.workers import WORKER_POOLS, WorkerPoolName

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ScheduleSlot:
    name: str
    interval_seconds: int
    pool: WorkerPoolName


DEFAULT_SCHEDULES: tuple[ScheduleSlot, ...] = (
    ScheduleSlot("worker_heartbeat", 30, WorkerPoolName.DEFAULT),
    ScheduleSlot("cache_compaction_hint", 300, WorkerPoolName.DEFAULT),
    ScheduleSlot("report_queue_drain_hint", 60, WorkerPoolName.REPORTING),
)


async def run_coordinated_tick(
    slot: ScheduleSlot,
    *,
    lock_ttl_seconds: int = 25,
) -> dict[str, Any]:
    """Run a schedule slot under a distributed lock (no-op body by default)."""

    lock_key = f"schedule:{slot.name}"
    async with distributed_lock(lock_key, ttl_seconds=lock_ttl_seconds) as acquired:
        payload = {
            "slot": slot.name,
            "pool": slot.pool.value,
            "acquired": acquired,
            "timestamp": datetime.now(UTC).isoformat(),
            "next_hint": (
                datetime.now(UTC) + timedelta(seconds=slot.interval_seconds)
            ).isoformat(),
        }
        if acquired:
            logger.debug("Schedule tick acquired", extra=payload)
        return payload


def worker_pool_summary() -> list[dict[str, Any]]:
    """Expose configured pools for ops dashboards."""

    return [
        {
            "name": pool.name.value,
            "queue": pool.queue,
            "concurrency": pool.concurrency,
            "prefetch": pool.prefetch,
        }
        for pool in WORKER_POOLS.values()
    ]
