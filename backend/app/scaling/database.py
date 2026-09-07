"""Database scaling helpers: replicas, retries, timeouts (Phase 10E)."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.exc import DBAPIError, OperationalError

from backend.app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def resolve_database_url(
    settings: Settings | None = None,
    *,
    prefer_read: bool = False,
) -> str:
    """Return write URL, or configured read-replica URL when requested."""

    runtime = settings or get_settings()
    if prefer_read:
        read_url = getattr(runtime, "database_read_url", None)
        if read_url:
            return str(read_url)
    return runtime.database_url


def pool_kwargs(settings: Settings | None = None) -> dict[str, object]:
    """Connection pool options shared by write/read engines."""

    runtime = settings or get_settings()
    if runtime.database_url.startswith("sqlite"):
        return {"pool_pre_ping": True}
    return {
        "pool_pre_ping": True,
        "pool_size": runtime.db_pool_size,
        "max_overflow": runtime.db_max_overflow,
        "pool_timeout": runtime.db_pool_timeout,
        "pool_recycle": runtime.db_pool_recycle,
    }


async def with_db_retry[T](
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int | None = None,
    timeout_seconds: float | None = None,
    settings: Settings | None = None,
) -> T:
    """Retry transient DB failures with optional overall timeout."""

    runtime = settings or get_settings()
    max_attempts = int(attempts or getattr(runtime, "db_retry_attempts", 3) or 3)
    timeout = timeout_seconds
    if timeout is None:
        timeout = float(getattr(runtime, "db_statement_timeout_seconds", 0) or 0)

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            if timeout and timeout > 0:
                return await asyncio.wait_for(operation(), timeout=timeout)
            return await operation()
        except (TimeoutError, OperationalError, DBAPIError) as exc:
            last_error = exc
            logger.warning(
                "Database operation failed; retrying",
                extra={"attempt": attempt, "error": type(exc).__name__},
            )
            await asyncio.sleep(min(0.05 * (2 ** (attempt - 1)), 1.0))
    assert last_error is not None
    raise last_error
