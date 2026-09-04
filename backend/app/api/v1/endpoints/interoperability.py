"""Phase 9A digital evidence exchange endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse

from backend.app.api.dependencies import get_interoperability_service
from backend.app.auth.models import AuthenticatedPrincipal
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse
from backend.app.interoperability.schemas import (
    ExportJobListResponse,
    ExportJobResponse,
    ExportRequest,
    ImportJobListResponse,
    ImportJobResponse,
    ManifestResponse,
)
from backend.app.interoperability.service import InteroperabilityService

router = APIRouter(tags=["interoperability"])
InteropServiceDependency = Annotated[
    InteroperabilityService, Depends(get_interoperability_service),
]


def _principal(request: Request) -> AuthenticatedPrincipal | None:
    existing = getattr(request.state, "principal", None)
    if isinstance(existing, AuthenticatedPrincipal):
        return existing
    return None


@router.post(
    "/cases/{case_id}/export",
    response_model=ApiResponse[ExportJobResponse],
)
async def export_case(
    case_id: UUID,
    body: ExportRequest,
    request: Request,
    service: InteropServiceDependency,
) -> ApiResponse[ExportJobResponse]:
    data = await service.export_case(
        case_id,
        format_name=body.format,
        evidence_ids=body.evidence_ids,
        include_binaries=body.include_binaries,
        principal=_principal(request),
    )
    return ApiResponse(data=data, request_id=get_request_id())


@router.post(
    "/cases/import",
    response_model=ApiResponse[ImportJobResponse],
)
async def import_case_package(
    request: Request,
    service: InteropServiceDependency,
    file: Annotated[UploadFile, File()],
) -> ApiResponse[ImportJobResponse]:
    payload = await file.read()
    data = await service.import_package(
        filename=file.filename or "package.zip",
        payload=payload,
        principal=_principal(request),
    )
    return ApiResponse(data=data, request_id=get_request_id())


@router.get("/exports", response_model=ApiResponse[ExportJobListResponse])
async def list_exports(
    service: InteropServiceDependency,
    case_id: Annotated[UUID | None, Query()] = None,
) -> ApiResponse[ExportJobListResponse]:
    data = await service.list_exports(case_id=case_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get("/exports/{export_id}", response_model=ApiResponse[ExportJobResponse])
async def get_export(
    export_id: UUID,
    service: InteropServiceDependency,
) -> ApiResponse[ExportJobResponse]:
    data = await service.get_export(export_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get(
    "/exports/{export_id}/manifest",
    response_model=ApiResponse[ManifestResponse],
)
async def get_export_manifest(
    export_id: UUID,
    service: InteropServiceDependency,
) -> ApiResponse[ManifestResponse]:
    data = await service.get_manifest(export_id)
    return ApiResponse(data=data, request_id=get_request_id())


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: UUID,
    service: InteropServiceDependency,
) -> FileResponse:
    path, filename, media_type = await service.download_export(export_id)
    return FileResponse(path=path, filename=filename, media_type=media_type)


@router.get("/imports", response_model=ApiResponse[ImportJobListResponse])
async def list_imports(
    service: InteropServiceDependency,
) -> ApiResponse[ImportJobListResponse]:
    data = await service.list_imports()
    return ApiResponse(data=data, request_id=get_request_id())


@router.get("/imports/{import_id}", response_model=ApiResponse[ImportJobResponse])
async def get_import(
    import_id: UUID,
    service: InteropServiceDependency,
) -> ApiResponse[ImportJobResponse]:
    data = await service.get_import(import_id)
    return ApiResponse(data=data, request_id=get_request_id())
