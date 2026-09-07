"""Namespaced Redis cache, TTL policies, invalidation, and locks (Phase 10E)."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Any

from backend.app.infrastructure.cache.json_cache import (
    cache_delete,
    cache_get_json,
    cache_set_json,
)
from backend.app.infrastructure.cache.json_cache import (
    cache_key as base_cache_key,
)
from backend.app.infrastructure.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class CacheNamespace(StrEnum):
    HTTP = "http"
    AI_META = "ai_meta"
    WORKER = "worker"
    LOCK = "lock"
    COORD = "coord"


class CacheTTL(StrEnum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


TTL_SECONDS: dict[CacheTTL, int] = {
    CacheTTL.SHORT: 15,
    CacheTTL.MEDIUM: 60,
    CacheTTL.LONG: 300,
}

LOCK_PREFIX = "ai_forge:lock:"


def namespaced_key(namespace: CacheNamespace, *parts: str) -> str:
    return base_cache_key(namespace.value, *parts)


def ttl_for(policy: CacheTTL) -> int:
    return TTL_SECONDS[policy]


async def cache_get(namespace: CacheNamespace, *parts: str) -> Any | None:
    return await cache_get_json(namespaced_key(namespace, *parts))


async def cache_set(
    namespace: CacheNamespace,
    *parts: str,
    value: Any,
    policy: CacheTTL = CacheTTL.SHORT,
) -> None:
    await cache_set_json(
        namespaced_key(namespace, *parts),
        value,
        ttl_seconds=ttl_for(policy),
    )


async def invalidate(namespace: CacheNamespace, *parts: str) -> None:
    await cache_delete(namespaced_key(namespace, *parts))


async def invalidate_prefix(namespace: CacheNamespace, prefix: str) -> int:
    """Best-effort SCAN + DELETE for a namespace prefix (never raises)."""

    pattern = namespaced_key(namespace, prefix) + "*"
    deleted = 0
    try:
        client = get_redis_client()
        async for key in client.scan_iter(match=pattern, count=100):
            await client.delete(key)
            deleted += 1
    except Exception:  # noqa: BLE001
        logger.debug("Cache prefix invalidation failed", exc_info=True)
    return deleted


@asynccontextmanager
async def distributed_lock(
    name: str,
    *,
    ttl_seconds: int = 30,
) -> AsyncIterator[bool]:
    """Acquire a Redis lock for worker coordination; yields False on miss."""

    token = uuid.uuid4().hex
    key = f"{LOCK_PREFIX}{name}"
    acquired = False
    try:
        client = get_redis_client()
        acquired = bool(
            await client.set(key, token, nx=True, ex=max(1, ttl_seconds))
        )
    except Exception:  # noqa: BLE001
        logger.debug("Distributed lock unavailable for %s", name, exc_info=True)
        acquired = False
    try:
        yield acquired
    finally:
        if acquired:
            try:
                client = get_redis_client()
                current = await client.get(key)
                if current == token:
                    await client.delete(key)
            except Exception:  # noqa: BLE001
                logger.debug(
                    "Distributed unlock failed for %s",
                    name,
                    exc_info=True,
                )


async def worker_heartbeat(worker_id: str, *, ttl_seconds: int = 60) -> None:
    """Publish worker liveness for coordination dashboards."""

    await cache_set(
        CacheNamespace.COORD,
        "heartbeat",
        worker_id,
        value={"worker_id": worker_id, "status": "alive"},
        policy=CacheTTL.MEDIUM if ttl_seconds >= 60 else CacheTTL.SHORT,
    )
