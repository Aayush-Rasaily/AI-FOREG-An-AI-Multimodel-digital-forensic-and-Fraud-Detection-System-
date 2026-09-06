"""Redis JSON cache facade for short-TTL read caching (Phase 10C)."""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.core.config import Settings, get_settings
from backend.app.infrastructure.cache.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# Namespace separates HTTP cache keys from Celery result backend data.
CACHE_KEY_PREFIX = "ai_forge:cache:"


def cache_key(*parts: str) -> str:
    return CACHE_KEY_PREFIX + ":".join(parts)


async def cache_get_json(key: str) -> Any | None:
    """Return a JSON-decoded cache entry, or None on miss/error."""

    try:
        client = get_redis_client()
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:  # noqa: BLE001 — cache must never break requests
        logger.debug("Redis cache get failed for %s", key, exc_info=True)
        return None


async def cache_set_json(
    key: str,
    value: Any,
    *,
    ttl_seconds: int = 15,
) -> None:
    """Store a JSON-encoded cache entry with TTL."""

    try:
        client = get_redis_client()
        await client.set(key, json.dumps(value, default=str), ex=max(1, ttl_seconds))
    except Exception:  # noqa: BLE001
        logger.debug("Redis cache set failed for %s", key, exc_info=True)


async def cache_delete(*keys: str) -> None:
    """Best-effort delete of one or more cache keys."""

    if not keys:
        return
    try:
        client = get_redis_client()
        await client.delete(*keys)
    except Exception:  # noqa: BLE001
        logger.debug("Redis cache delete failed", exc_info=True)


def default_cache_ttl(settings: Settings | None = None) -> int:
    runtime = settings or get_settings()
    if runtime.app_env == "production":
        return 20
    if runtime.app_env in {"staging"}:
        return 15
    return 10
