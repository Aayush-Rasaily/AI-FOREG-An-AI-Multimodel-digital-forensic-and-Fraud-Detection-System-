"""Version-one signature verification endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from pydantic import BaseModel, ConfigDict

from backend.app.ai.document.signature.schemas import (
    SignatureVerificationListResponse,
    SignatureVerificationResponse,
)
from backend.app.ai.document.signature.service import SignatureVerificationService
from backend.app.api.dependencies import get_signature_verification_service
from backend.app.api.schemas.processing import ProcessingJobResponse
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(tags=["signature-ai"])
SignatureVerificationServiceDependency = Annotated[
    SignatureVerificationService,
    Depends(get_signature_verification_service),
]


class SignatureEvidenceAnalysisRequest(BaseModel):
    """Reference evidence for questioned signature verification."""

    model_config = ConfigDict(extra="forbid")

    reference_evidence_id: UUID


@router.post(
    "/signature/verify",
    response_model=ApiResponse[SignatureVerificationResponse],
    summary="Verify a signature pair",
)
async def verify_signature(
    service: SignatureVerificationServiceDependency,
    reference_evidence_id: Annotated[UUID | None, Form()] = None,
    questioned_evidence_id: Annotated[UUID | None, Form()] = None,
    reference_file: Annotated[UploadFile | None, File()] = None,
    questioned_file: Annotated[UploadFile | None, File()] = None,
) -> ApiResponse[SignatureVerificationResponse]:
    """Verify questioned signature bytes against a trusted reference."""

    reference_bytes = (
        await reference_file.read() if reference_file is not None else None
    )
    questioned_bytes = (
        await questioned_file.read() if questioned_file is not None else None
    )
    result = await service.verify(
        reference_evidence_id=reference_evidence_id,
        questioned_evidence_id=questioned_evidence_id,
        reference_bytes=reference_bytes,
        questioned_bytes=questioned_bytes,
    )
    return ApiResponse(data=result, request_id=get_request_id())


@router.get(
    "/signature/{verification_id}",
    response_model=ApiResponse[SignatureVerificationResponse],
    summary="Retrieve one signature verification run",
)
async def get_signature_verification(
    verification_id: UUID,
    service: SignatureVerificationServiceDependency,
) -> ApiResponse[SignatureVerificationResponse]:
    """Return one persisted signature verification run."""

    return ApiResponse(
        data=await service.get_run(verification_id),
        request_id=get_request_id(),
    )


@router.post(
    "/evidence/{evidence_id}/signature-analysis",
    response_model=ApiResponse[ProcessingJobResponse],
    status_code=202,
    summary="Queue signature verification for evidence",
)
async def analyze_signature_evidence(
    evidence_id: UUID,
    payload: SignatureEvidenceAnalysisRequest,
    background_tasks: BackgroundTasks,
    service: SignatureVerificationServiceDependency,
) -> ApiResponse[ProcessingJobResponse]:
    """Queue signature verification against registered reference evidence."""

    job = await service.create_job(
        questioned_evidence_id=evidence_id,
        reference_evidence_id=payload.reference_evidence_id,
    )
    background_tasks.add_task(service.run, job.id)
    return ApiResponse(data=job, request_id=get_request_id())


@router.get(
    "/evidence/{evidence_id}/signature-analysis",
    response_model=ApiResponse[SignatureVerificationListResponse],
    summary="List signature verification history",
)
async def list_signature_analysis_runs(
    evidence_id: UUID,
    service: SignatureVerificationServiceDependency,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ApiResponse[SignatureVerificationListResponse]:
    """Return signature verification history for one questioned evidence item."""

    return ApiResponse(
        data=await service.list_runs(
            evidence_id,
            limit=limit,
            offset=offset,
        ),
        request_id=get_request_id(),
    )
