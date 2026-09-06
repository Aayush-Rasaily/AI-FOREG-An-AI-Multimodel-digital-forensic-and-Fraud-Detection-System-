"""Bounded concurrency helpers for CPU/IO offload (Phase 10C)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

_DEFAULT_WORKERS = 8


@lru_cache
def get_thread_pool(*, max_workers: int = _DEFAULT_WORKERS) -> ThreadPoolExecutor:
    """Return a process-wide bounded thread pool."""

    return ThreadPoolExecutor(
        max_workers=max_workers,
        thread_name_prefix="ai-forge-worker",
    )


async def run_in_thread[**P, T](
    func: Callable[P, T],
    /,
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """Run a blocking callable on the bounded thread pool."""

    loop = asyncio.get_running_loop()
    pool = get_thread_pool()
    return await loop.run_in_executor(
        pool,
        lambda: func(*args, **kwargs),
    )


async def run_parallel[T](*awaitables: Awaitable[T]) -> list[T]:
    """Await independent coroutines concurrently."""

    return list(await asyncio.gather(*awaitables))


def configure_default_executor(*, max_workers: int = _DEFAULT_WORKERS) -> None:
    """Install the bounded pool as the asyncio default executor when possible."""

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.set_default_executor(get_thread_pool(max_workers=max_workers))


def shutdown_thread_pool(*, wait: bool = False) -> None:
    """Shut down the process thread pool during graceful process exit."""

    if get_thread_pool.cache_info().currsize:
        get_thread_pool().shutdown(wait=wait, cancel_futures=True)
        get_thread_pool.cache_clear()
