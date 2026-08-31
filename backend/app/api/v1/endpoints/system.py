"""Non-sensitive system diagnostics endpoint."""

import platform
import sys

from fastapi import APIRouter, Request

from backend.app.api.schemas.system import SystemInfoResponse
from backend.app.core.config import Settings
from backend.app.core.request_context import get_request_id
from backend.app.core.responses import ApiResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/info",
    response_model=ApiResponse[SystemInfoResponse],
    summary="Get safe system information",
)
async def read_system_info(request: Request) -> ApiResponse[SystemInfoResponse]:
    """Return diagnostics that do not disclose secrets or filesystem paths."""

    settings: Settings = request.app.state.settings
    return ApiResponse(
        data=SystemInfoResponse(
            service=settings.app_name,
            version=settings.app_version,
            environment=settings.app_env,
            python_version=sys.version.split()[0],
            platform=platform.system(),
        ),
        request_id=get_request_id(),
    )
