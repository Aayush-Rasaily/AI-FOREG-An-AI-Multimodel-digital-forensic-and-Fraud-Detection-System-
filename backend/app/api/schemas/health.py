"""Health endpoint schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


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


class ReadinessResponse(BaseModel):
    """Aggregated readiness payload for orchestration probes."""

    status: Literal["ready", "not_ready"]
    ready: bool
    checks: list[dict[str, Any]] = Field(default_factory=list)
    fail_count: int
    environment: str
    version: str
    timestamp: datetime
