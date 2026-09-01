"""FastAPI application factory and process entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.ai.audio.bootstrap import build_audio_analysis_stack
from backend.app.ai.audio.config import AudioAISettings
from backend.app.ai.bootstrap import build_ai_stack
from backend.app.ai.config.settings import AISettings
from backend.app.ai.document.bootstrap import build_document_analysis_stack
from backend.app.ai.document.config import DocumentAISettings
from backend.app.ai.image.bootstrap import build_image_analysis_stack
from backend.app.ai.image.config import ImageAISettings
from backend.app.ai.video.bootstrap import build_video_analysis_stack
from backend.app.ai.video.config import VideoAISettings
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
    ai_settings = AISettings()
    image_settings = ImageAISettings()
    document_settings = DocumentAISettings()
    video_settings = VideoAISettings()
    audio_settings = AudioAISettings()

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
    registry, loader, cache, device_manager, engine = build_ai_stack(ai_settings)
    image_registry, image_device_manager, image_engine = build_image_analysis_stack(
        image_settings
    )
    (
        document_registry,
        document_device_manager,
        document_engine,
    ) = build_document_analysis_stack(document_settings)
    video_registry, video_device_manager, video_engine = build_video_analysis_stack(
        video_settings
    )
    audio_registry, audio_device_manager, audio_engine = build_audio_analysis_stack(
        audio_settings
    )
    app.state.ai_stack = {
        "registry": registry,
        "loader": loader,
        "cache": cache,
        "device_manager": device_manager,
        "engine": engine,
        "settings": ai_settings,
    }
    app.state.image_ai_stack = {
        "registry": image_registry,
        "device_manager": image_device_manager,
        "engine": image_engine,
        "settings": image_settings,
    }
    app.state.document_ai_stack = {
        "registry": document_registry,
        "device_manager": document_device_manager,
        "engine": document_engine,
        "settings": document_settings,
    }
    app.state.video_ai_stack = {
        "registry": video_registry,
        "device_manager": video_device_manager,
        "engine": video_engine,
        "settings": video_settings,
    }
    app.state.audio_ai_stack = {
        "registry": audio_registry,
        "device_manager": audio_device_manager,
        "engine": audio_engine,
        "settings": audio_settings,
    }
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
