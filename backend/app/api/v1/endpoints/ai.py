"""Version-one AI infrastructure endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.ai.schemas import (
    AIModelListResponse,
    AIModelResponse,
    InferenceJobListResponse,
    InferenceJobResponse,
    ModelReloadRequest,
)
from backend.app.ai.service import AIService
from backend.app.api.dependencies import get_ai_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["ai"])
AIServiceDependency = Annotated[AIService, Depends(get_ai_service)]


@router.get(
    "/models",
    response_model=ApiResponse[AIModelListResponse],
    summary="List registered AI models",
)
async def list_models(
    service: AIServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[AIModelListResponse]:
    """Return registered models with cache and device state."""

    return ApiResponse(
        data=await service.list_models(limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/models/{model_id}",
    response_model=ApiResponse[AIModelResponse],
    summary="Retrieve one AI model",
)
async def get_model(
    model_id: UUID,
    service: AIServiceDependency,
) -> ApiResponse[AIModelResponse]:
    """Return one registered AI model."""

    return ApiResponse(
        data=await service.get_model(model_id),
        request_id=get_request_id(),
    )


@router.post(
    "/models/reload",
    response_model=ApiResponse[AIModelResponse],
    summary="Reload one AI model",
)
async def reload_model(
    payload: ModelReloadRequest,
    service: AIServiceDependency,
) -> ApiResponse[AIModelResponse]:
    """Reload a model, run warmup inference, and persist job metrics."""

    return ApiResponse(
        data=await service.reload_model(payload.model_name),
        request_id=get_request_id(),
    )


@router.get(
    "/inference/jobs",
    response_model=ApiResponse[InferenceJobListResponse],
    summary="List inference jobs",
)
async def list_inference_jobs(
    service: AIServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[InferenceJobListResponse]:
    """Return tracked inference job history."""

    return ApiResponse(
        data=await service.list_jobs(limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/inference/jobs/{job_id}",
    response_model=ApiResponse[InferenceJobResponse],
    summary="Retrieve one inference job",
)
async def get_inference_job(
    job_id: UUID,
    service: AIServiceDependency,
) -> ApiResponse[InferenceJobResponse]:
    """Return one inference job with logs."""

    return ApiResponse(
        data=await service.get_job(job_id),
        request_id=get_request_id(),
    )
