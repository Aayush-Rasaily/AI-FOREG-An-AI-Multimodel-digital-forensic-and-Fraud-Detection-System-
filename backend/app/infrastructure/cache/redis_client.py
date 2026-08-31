"""Redis client factory."""

from functools import lru_cache

from redis.asyncio import Redis

from backend.app.core.config import Settings, get_settings


def create_redis_client(settings: Settings) -> Redis:
    """Create a bounded, lazy Redis client from explicit settings."""

    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        health_check_interval=30,
        max_connections=settings.redis_max_connections,
    )


@lru_cache
def get_redis_client() -> Redis:
    """Return one lazy, connection-pooled Redis client per process."""

    return create_redis_client(get_settings())


async def close_redis_client() -> None:
    """Close the cached Redis pool during application shutdown if initialized."""

    if get_redis_client.cache_info().currsize:
        await get_redis_client().aclose()
        get_redis_client.cache_clear()
