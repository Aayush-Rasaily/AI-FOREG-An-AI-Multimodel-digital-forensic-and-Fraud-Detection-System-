"""Application-level health checks for optional infrastructure dependencies."""

import asyncio

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


async def check_database_health(
    session: AsyncSession,
    *,
    timeout_seconds: float,
) -> bool:
    """Check PostgreSQL without making startup dependent on its availability."""

    try:
        await asyncio.wait_for(
            session.execute(text("SELECT 1")),
            timeout=timeout_seconds,
        )
    except (OSError, SQLAlchemyError, TimeoutError):
        return False
    return True
