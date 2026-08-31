"""System information response schema."""

from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    """Safe, non-sensitive runtime information for diagnostics."""

    service: str
    version: str
    environment: str
    python_version: str
    platform: str
