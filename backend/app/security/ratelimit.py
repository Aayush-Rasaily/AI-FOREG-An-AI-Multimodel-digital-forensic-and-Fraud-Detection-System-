"""Redis-backed rate limiting with in-memory fallback (Phase 10D)."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
from typing import Literal

from starlette.requests import Request

logger = logging.getLogger(__name__)

RateCategory = Literal[
    "auth",
    "upload",
    "ai",
    "report",
    "search",
    "export",
]


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """Burst + sustained windows for one traffic category."""

    burst_limit: int
    burst_window_seconds: int
    sustained_limit: int
    sustained_window_seconds: int


DEFAULT_RULES: dict[RateCategory, RateLimitRule] = {
    "auth": RateLimitRule(10, 60, 60, 3600),
    "upload": RateLimitRule(20, 60, 200, 3600),
    "ai": RateLimitRule(30, 60, 300, 3600),
    "report": RateLimitRule(10, 60, 100, 3600),
    "search": RateLimitRule(60, 60, 600, 3600),
    "export": RateLimitRule(10, 60, 50, 3600),
}


_memory_buckets: dict[str, deque[float]] = defaultdict(deque)
_memory_lock = Lock()


def classify_request(method: str, path: str) -> RateCategory | None:
    """Map an HTTP request to a rate-limit category, or None if unlimited."""

    if method.upper() == "OPTIONS":
        return None
    normalized = path.lower()
    if normalized.endswith("/metrics") or "/health" in normalized:
        return None
    if "/auth/" in normalized or normalized.endswith("/login"):
        return "auth"
    if "/evidence" in normalized and method.upper() in {"POST", "PUT", "PATCH"}:
        return "upload"
    if (
        any(
            fragment in normalized
            for fragment in (
                "/ai/",
                "/models",
                "/image-ai",
                "/document-ai",
                "/video-ai",
                "/audio-ai",
                "/signature",
                "/forensics",
                "/fusion",
            )
        )
        and method.upper() == "POST"
    ):
        return "ai"
    if "/reports" in normalized and method.upper() == "POST":
        return "report"
    if "/search" in normalized or normalized.endswith("/query"):
        return "search"
    if "/export" in normalized or "/interoperability" in normalized:
        if method.upper() in {"GET", "POST"}:
            return "export"
    return None


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",", 1)[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def identity_keys(request: Request) -> tuple[str, str | None]:
    """Return (ip_key, user_key) dimensions for limiting."""

    ip = client_ip(request)
    auth = request.headers.get("authorization") or ""
    user_key = None
    if auth:
        user_key = hashlib.sha256(auth.encode("utf-8")).hexdigest()[:24]
    return ip, user_key


def _memory_allow(key: str, limit: int, window_seconds: int) -> bool:
    now = time.monotonic()
    with _memory_lock:
        bucket = _memory_buckets[key]
        cutoff = now - window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


async def _redis_allow(key: str, limit: int, window_seconds: int) -> bool | None:
    """Return True/False when Redis works, or None to signal fallback."""

    try:
        from backend.app.infrastructure.cache.redis_client import get_redis_client

        client = get_redis_client()
        pipe_key = f"ai_forge:ratelimit:{key}"
        count = await client.incr(pipe_key)
        if count == 1:
            await client.expire(pipe_key, window_seconds)
        return int(count) <= limit
    except Exception:  # noqa: BLE001 — never break requests for limiter backend
        logger.debug("Redis rate limit backend unavailable", exc_info=True)
        return None


async def allow_request(
    *,
    category: RateCategory,
    ip: str,
    user_key: str | None,
    rule: RateLimitRule | None = None,
    use_redis: bool = True,
) -> bool:
    """Enforce burst + sustained limits for IP and optional user identity."""

    policy = rule or DEFAULT_RULES[category]
    dimensions = [f"ip:{ip}"]
    if user_key:
        dimensions.append(f"user:{user_key}")

    for dimension in dimensions:
        for suffix, limit, window in (
            ("burst", policy.burst_limit, policy.burst_window_seconds),
            ("sustained", policy.sustained_limit, policy.sustained_window_seconds),
        ):
            key = f"{category}:{dimension}:{suffix}"
            allowed: bool | None = None
            if use_redis:
                try:
                    allowed = await asyncio.wait_for(
                        _redis_allow(key, limit, window),
                        timeout=0.15,
                    )
                except TimeoutError:
                    allowed = None
            if allowed is None:
                allowed = _memory_allow(key, limit, window)
            if not allowed:
                return False
    return True
