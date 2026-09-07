"""Object storage factory for local and cloud backends (Phase 10E)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from backend.app.application.services.storage import StorageService
from backend.app.core.config import Settings
from backend.app.core.exceptions import StorageError
from backend.app.infrastructure.storage.local import LocalStorage

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def create_storage_service(settings: Settings) -> StorageService:
    """Build a storage adapter without changing evidence API contracts."""

    backend = settings.storage_backend
    if backend == "local":
        return LocalStorage(settings.storage_root)
    if backend in {"s3", "minio"}:
        from backend.app.infrastructure.storage.s3 import S3CompatibleStorage

        return S3CompatibleStorage.from_settings(settings)
    if backend == "azure":
        from backend.app.infrastructure.storage.azure_blob import (
            AzureBlobStorageConfig,
        )

        return AzureBlobStorageConfig.from_settings(settings).as_adapter()
    if backend == "gcs":
        from backend.app.infrastructure.storage.gcs import GCSStorageConfig

        return GCSStorageConfig.from_settings(settings).as_adapter()
    raise StorageError(
        f"The configured storage backend '{backend}' is not available."
    )
