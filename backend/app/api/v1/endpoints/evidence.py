"""Version-one evidence registry endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile

from backend.app.api.dependencies import get_evidence_service
from backend.app.api.schemas.evidence import EvidenceListResponse, EvidenceResponse
from backend.app.application.services.evidence_service import EvidenceService
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["evidence"])
EvidenceServiceDependency = Annotated[
    EvidenceService,
    Depends(get_evidence_service),
]


@router.post(
    "/cases/{case_id}/evidence",
    response_model=ApiResponse[EvidenceResponse],
    status_code=201,
    summary="Register an evidence object",
)
async def upload_evidence(
    case_id: UUID,
    file: Annotated[UploadFile, File(description="Untrusted evidence object")],
    service: EvidenceServiceDependency,
) -> ApiResponse[EvidenceResponse]:
    """Ingest, hash, store, and register one original evidence object."""

    return ApiResponse(
        data=await service.ingest(case_id, file),
        request_id=get_request_id(),
    )


@router.get(
    "/cases/{case_id}/evidence",
    response_model=ApiResponse[EvidenceListResponse],
    summary="List evidence for a case",
)
async def list_evidence(
    case_id: UUID,
    service: EvidenceServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[EvidenceListResponse]:
    """Return a bounded evidence page for a case."""

    return ApiResponse(
        data=await service.list_for_case(case_id, limit=limit, offset=offset),
        request_id=get_request_id(),
    )


@router.get(
    "/evidence/{evidence_id}",
    response_model=ApiResponse[EvidenceResponse],
    summary="Retrieve evidence metadata",
)
async def get_evidence(
    evidence_id: UUID,
    service: EvidenceServiceDependency,
) -> ApiResponse[EvidenceResponse]:
    """Retrieve evidence metadata and custody history without file bytes."""

    return ApiResponse(
        data=await service.get(evidence_id),
        request_id=get_request_id(),
    )
