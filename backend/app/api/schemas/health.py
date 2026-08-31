"""Health endpoint schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Application and dependency health payload."""

    status: Literal["healthy", "degraded"]
    version: str
    environment: str
    database: Literal["healthy", "unavailable"]
    timestamp: datetime


class LivenessResponse(BaseModel):
    """Minimal process liveness payload safe for load balancer probes."""

    status: Literal["ok"] = "ok"
    service: str
    version: str
