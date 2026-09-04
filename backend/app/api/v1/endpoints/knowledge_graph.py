"""Phase 9B knowledge graph endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from backend.app.api.dependencies import get_knowledge_graph_service
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.knowledge_graph.schemas import (
    GraphEntityListResponse,
    GraphEntityResponse,
    GraphPreviewResponse,
    GraphRelationshipListResponse,
    KnowledgeGraphResponse,
    NeighborResponse,
)
from backend.app.knowledge_graph.service import KnowledgeGraphService

router = APIRouter(tags=["knowledge-graph"])
KgServiceDependency = Annotated[
    KnowledgeGraphService, Depends(get_knowledge_graph_service),
]


@router.post(
    "/cases/{case_id}/knowledge-graph",
    response_model=ApiResponse[KnowledgeGraphResponse],
)
async def build_knowledge_graph(
    case_id: UUID,
    service: KgServiceDependency,
) -> ApiResponse[KnowledgeGraphResponse]:
    data = await service.build_graph(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/knowledge-graph/preview",
    response_model=ApiResponse[GraphPreviewResponse],
)
async def preview_knowledge_graph(
    case_id: UUID,
    service: KgServiceDependency,
) -> ApiResponse[GraphPreviewResponse]:
    data = await service.preview(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/cases/{case_id}/knowledge-graph",
    response_model=ApiResponse[KnowledgeGraphResponse],
)
async def get_case_knowledge_graph(
    case_id: UUID,
    service: KgServiceDependency,
) -> ApiResponse[KnowledgeGraphResponse]:
    data = await service.get_case_graph(case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/knowledge-graph/entities",
    response_model=ApiResponse[GraphEntityListResponse],
)
async def list_graph_entities(
    service: KgServiceDependency,
    graph_id: Annotated[UUID | None, Query()] = None,
    case_id: Annotated[UUID | None, Query()] = None,
    entity_type: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
) -> ApiResponse[GraphEntityListResponse]:
    data = await service.list_entities(
        graph_id=graph_id,
        case_id=case_id,
        entity_type=entity_type,
        query=q,
    )
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/knowledge-graph/relationships",
    response_model=ApiResponse[GraphRelationshipListResponse],
)
async def list_graph_relationships(
    service: KgServiceDependency,
    graph_id: Annotated[UUID | None, Query()] = None,
    case_id: Annotated[UUID | None, Query()] = None,
    relationship_type: Annotated[str | None, Query()] = None,
) -> ApiResponse[GraphRelationshipListResponse]:
    data = await service.list_relationships(
        graph_id=graph_id,
        case_id=case_id,
        relationship_type=relationship_type,
    )
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/knowledge-graph/search",
    response_model=ApiResponse[GraphEntityListResponse],
)
async def search_graph_entities(
    service: KgServiceDependency,
    q: Annotated[str, Query(min_length=1)],
    case_id: Annotated[UUID | None, Query()] = None,
) -> ApiResponse[GraphEntityListResponse]:
    data = await service.search(query=q, case_id=case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/knowledge-graph/entity/{entity_id}/neighbors",
    response_model=ApiResponse[NeighborResponse],
)
async def get_graph_entity_neighbors(
    entity_id: UUID,
    service: KgServiceDependency,
) -> ApiResponse[NeighborResponse]:
    data = await service.get_neighbors(entity_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/knowledge-graph/entity/{entity_id}",
    response_model=ApiResponse[GraphEntityResponse],
)
async def get_graph_entity(
    entity_id: UUID,
    service: KgServiceDependency,
) -> ApiResponse[GraphEntityResponse]:
    data = await service.get_entity(entity_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/knowledge-graph/{graph_id}",
    response_model=ApiResponse[KnowledgeGraphResponse],
)
async def get_knowledge_graph(
    graph_id: UUID,
    service: KgServiceDependency,
) -> ApiResponse[KnowledgeGraphResponse]:
    data = await service.get_graph(graph_id)
    return ApiResponse(data=data, request_id=get_request_id())
