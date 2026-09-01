"""API schemas for AI infrastructure."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ModelReloadRequest(BaseModel):
    """Request body to reload one registered model."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(min_length=1, max_length=128)


class AIModelResponse(BaseModel):
    """One registered AI model."""

    id: UUID
    name: str
    version: str
    framework: str
    author: str
    license: str
    input_type: str
    output_type: str
    model_hash: str
    required_device: str
    status: str
    current_device: str | None
    last_loaded_at: datetime | None
    last_latency_ms: float | None
    supported_tasks: list[str]
    cache_state: dict[str, Any] | None
    health: dict[str, Any]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class AIModelListResponse(BaseModel):
    """Registered AI models."""

    items: list[AIModelResponse]
    total: int
    limit: int
    offset: int
    cache_statistics: dict[str, int]
    devices: list[dict[str, Any]]


class InferenceLogResponse(BaseModel):
    """One inference log entry."""

    id: UUID
    level: str
    message: str
    metadata: dict[str, Any]
    created_at: datetime


class InferenceJobResponse(BaseModel):
    """One tracked inference job."""

    id: UUID
    model_record_id: UUID
    model_name: str
    model_version: str
    task: str
    device: str
    status: str
    latency_ms: float | None
    batch_size: int
    error_code: str | None
    error_message: str | None
    metadata: dict[str, Any]
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime
    logs: list[InferenceLogResponse]


class InferenceJobListResponse(BaseModel):
    """Inference job history."""

    items: list[InferenceJobResponse]
    total: int
    limit: int
    offset: int
