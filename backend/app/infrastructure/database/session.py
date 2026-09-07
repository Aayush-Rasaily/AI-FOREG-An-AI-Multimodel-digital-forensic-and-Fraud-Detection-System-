"""Async SQLAlchemy engine and unit-of-work session providers."""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.core.config import Settings, get_settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Create one configured async engine from explicit settings."""

    from backend.app.scaling.database import pool_kwargs, resolve_database_url

    url = resolve_database_url(settings, prefer_read=False)
    return create_async_engine(url, **pool_kwargs(settings))


def create_read_engine(settings: Settings) -> AsyncEngine:
    """Create a read-replica engine when DATABASE_READ_URL is configured."""

    from backend.app.scaling.database import pool_kwargs, resolve_database_url

    url = resolve_database_url(settings, prefer_read=True)
    return create_async_engine(url, **pool_kwargs(settings))


def create_session_factory(
    settings: Settings,
    *,
    engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory from explicit settings."""

    return async_sessionmaker(
        bind=engine or create_engine(settings),
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@lru_cache
def get_engine() -> AsyncEngine:
    """Create one pooled engine per process."""

    return create_engine(get_settings())


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create the process-wide async session factory."""

    return create_session_factory(get_settings(), engine=get_engine())


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield one request-scoped database session."""

    async with get_session_factory()() as session:
        yield session


async def dispose_engine() -> None:
    """Dispose the cached engine during application shutdown if initialized."""

    if get_engine.cache_info().currsize:
        await get_engine().dispose()
        get_session_factory.cache_clear()
        get_engine.cache_clear()
