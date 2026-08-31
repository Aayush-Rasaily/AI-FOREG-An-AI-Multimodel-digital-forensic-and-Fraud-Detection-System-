"""FastAPI application factory and process entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import router as api_v1_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.logging import configure_logging
from backend.app.core.middleware import (
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from backend.app.infrastructure.cache.redis_client import close_redis_client
from backend.app.infrastructure.database.session import dispose_engine


@asynccontextmanager
async def application_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Provide a lifecycle boundary for future resource initialization."""

    try:
        yield
    finally:
        await dispose_engine()
        await close_redis_client()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the API application with explicit configuration injection."""

    runtime_settings = settings or get_settings()
    configure_logging(runtime_settings)

    app = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.app_version,
        debug=runtime_settings.debug,
        docs_url="/docs" if runtime_settings.debug else None,
        redoc_url="/redoc" if runtime_settings.debug else None,
        openapi_url="/openapi.json" if runtime_settings.debug else None,
        lifespan=application_lifespan,
    )
    app.state.settings = runtime_settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    register_exception_handlers(app)
    app.include_router(api_v1_router, prefix=runtime_settings.api_v1_prefix)
    return app


app = create_app()
