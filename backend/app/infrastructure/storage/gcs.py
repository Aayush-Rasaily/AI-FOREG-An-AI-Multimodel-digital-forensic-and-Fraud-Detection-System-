"""Google Cloud Storage configuration adapter (Phase 10E)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO
from uuid import UUID, uuid4

from backend.app.core.config import Settings
from backend.app.core.exceptions import StorageError


@dataclass(frozen=True, slots=True)
class GCSStorageConfig:
    bucket: str
    project: str | None
    prefix: str = "ai-forge/"

    @classmethod
    def from_settings(cls, settings: Settings) -> GCSStorageConfig:
        return cls(
            bucket=getattr(settings, "gcs_bucket", "ai-forge") or "ai-forge",
            project=getattr(settings, "gcs_project", None),
            prefix=getattr(settings, "object_storage_prefix", "ai-forge/"),
        )

    def as_adapter(self) -> _GCSAdapter:
        return _GCSAdapter(self)


class _GCSAdapter:
    def __init__(self, config: GCSStorageConfig) -> None:
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
        try:
            import google.cloud.storage  # noqa: F401
        except ImportError as exc:
            raise StorageError(
                "google-cloud-storage is required for the GCS storage backend."
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
        raise StorageError("GCS upload is configured but not enabled.")

    def open(self, storage_key: str):  # type: ignore[no-untyped-def]
        self._ensure()
        raise StorageError("GCS download is configured but not enabled.")

    async def commit(self, temporary_key: str, storage_key: str) -> None:
        self._ensure()
        raise StorageError("GCS commit is configured but not enabled.")

    async def exists(self, storage_key: str) -> bool:
        self._ensure()
        return False

    async def delete(self, storage_key: str) -> None:
        self._ensure()
        raise StorageError("GCS delete is configured but not enabled.")
