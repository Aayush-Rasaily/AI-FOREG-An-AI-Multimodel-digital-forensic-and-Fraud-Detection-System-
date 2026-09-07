"""Azure Blob storage configuration adapter (Phase 10E)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO
from uuid import UUID, uuid4

from backend.app.core.config import Settings
from backend.app.core.exceptions import StorageError


@dataclass(frozen=True, slots=True)
class AzureBlobStorageConfig:
    """Configuration holder that surfaces a StorageService-compatible adapter."""

    connection_string: str | None
    container: str
    prefix: str = "ai-forge/"

    @classmethod
    def from_settings(cls, settings: Settings) -> AzureBlobStorageConfig:
        return cls(
            connection_string=getattr(settings, "azure_blob_connection_string", None),
            container=(
                getattr(settings, "azure_blob_container", "ai-forge") or "ai-forge"
            ),
            prefix=getattr(settings, "object_storage_prefix", "ai-forge/"),
        )

    def as_adapter(self) -> _AzureBlobAdapter:
        return _AzureBlobAdapter(self)


class _AzureBlobAdapter:
    """Configured Azure adapter — operations require azure-storage-blob."""

    def __init__(self, config: AzureBlobStorageConfig) -> None:
        self.config = config

    def temporary_key(self) -> str:
        return f".tmp/{uuid4().hex}.upload"

    def artifact_key(
        self,
        case_id: UUID,
        evidence_id: UUID,
        artifact_id: UUID,
    ) -> str:
        return f"evidence/{case_id}/{evidence_id}/artifacts/{artifact_id}.artifact"

    def _ensure(self) -> None:
        if not self.config.connection_string:
            raise StorageError("Azure Blob connection string is not configured.")
        try:
            import azure.storage.blob  # noqa: F401
        except ImportError as exc:
            raise StorageError(
                "azure-storage-blob is required for the Azure storage backend."
            ) from exc

    async def save_stream(
        self,
        source: BinaryIO,
        storage_key: str,
        *,
        max_bytes: int,
        chunk_size: int,
    ) -> int:
        self._ensure()
        raise StorageError("Azure Blob upload is configured but not enabled.")

    def open(self, storage_key: str):  # type: ignore[no-untyped-def]
        self._ensure()
        raise StorageError("Azure Blob download is configured but not enabled.")

    async def commit(self, temporary_key: str, storage_key: str) -> None:
        self._ensure()
        raise StorageError("Azure Blob commit is configured but not enabled.")

    async def exists(self, storage_key: str) -> bool:
        self._ensure()
        return False

    async def delete(self, storage_key: str) -> None:
        self._ensure()
        raise StorageError("Azure Blob delete is configured but not enabled.")
