"""Version-one entity resolution endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from backend.app.api.dependencies import get_entity_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.entities.schemas import (
    CanonicalEntityResponse,
    EntityDetailResponse,
    EntityRelationshipResponse,
    EntityRunListResponse,
    EntityRunResponse,
    InvestigationGraphResponse,
)
from backend.app.entities.service import EntityService

router = APIRouter(tags=["entities"])
EntityServiceDependency = Annotated[
    EntityService,
    Depends(get_entity_service),
]


@router.post(
    "/cases/{case_id}/entities",
    response_model=ApiResponse[EntityRunResponse],
    status_code=202,
    summary="Queue entity-resolution analysis",
)
async def create_entities(
    case_id: UUID,
    background_tasks: BackgroundTasks,
    service: EntityServiceDependency,
) -> ApiResponse[EntityRunResponse]:
    """Queue deterministic entity resolution for one case."""

    run = await service.create_analysis(case_id)
    background_tasks.add_task(service.run, run.id)
    return ApiResponse(data=run, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/entities",
    response_model=ApiResponse[EntityRunListResponse],
    summary="List entity-resolution analysis history",
)
async def list_case_entities(
    case_id: UUID,
    service: EntityServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[EntityRunListResponse]:
    """Return entity-resolution analysis history for one case."""

    return ApiResponse(
        data=await service.list_runs(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/entities/latest",
    response_model=ApiResponse[EntityDetailResponse],
    summary="Retrieve latest entity-resolution analysis",
)
async def get_latest_entities(
    case_id: UUID,
    service: EntityServiceDependency,
) -> ApiResponse[EntityDetailResponse]:
    """Return the most recent entity-resolution analysis with graph."""

    return ApiResponse(
        data=await service.get_latest(case_id),
        request_id=get_request_id(),
    )


@router.get(
    "/entities/{entity_id}",
    response_model=ApiResponse[CanonicalEntityResponse],
    summary="Retrieve one canonical entity",
)
async def get_entity(
    entity_id: UUID,
    service: EntityServiceDependency,
) -> ApiResponse[CanonicalEntityResponse]:
    """Return one persisted canonical entity."""

    return ApiResponse(
        data=await service.get_entity(entity_id),
        request_id=get_request_id(),
    )


@router.get(
    "/entities/{entity_id}/graph",
    response_model=ApiResponse[InvestigationGraphResponse],
    summary="Retrieve neighborhood graph for one entity",
)
async def get_entity_graph(
    entity_id: UUID,
    service: EntityServiceDependency,
) -> ApiResponse[InvestigationGraphResponse]:
    """Return the investigation subgraph centered on one entity."""

    return ApiResponse(
        data=await service.get_entity_graph(entity_id),
        request_id=get_request_id(),
    )


@router.get(
    "/entities/{entity_id}/relationships",
    response_model=ApiResponse[list[EntityRelationshipResponse]],
    summary="List relationships for one entity",
)
async def list_entity_relationships(
    entity_id: UUID,
    service: EntityServiceDependency,
) -> ApiResponse[list[EntityRelationshipResponse]]:
    """Return relationships involving one canonical entity."""

    return ApiResponse(
        data=await service.get_entity_relationships(entity_id),
        request_id=get_request_id(),
    )
