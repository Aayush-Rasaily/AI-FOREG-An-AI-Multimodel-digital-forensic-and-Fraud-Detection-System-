"""S3-compatible object storage adapter (Phase 10E)."""

from __future__ import annotations

import asyncio
import io
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import BinaryIO
from uuid import UUID, uuid4

from backend.app.core.config import Settings
from backend.app.core.exceptions import FileTooLargeError, StorageError


class S3CompatibleStorage:
    """Opaque key storage over S3 / MinIO using optional boto3."""

    def __init__(
        self,
        *,
        bucket: str,
        endpoint_url: str | None,
        access_key: str | None,
        secret_key: str | None,
        region: str = "us-east-1",
        prefix: str = "ai-forge/",
    ) -> None:
        self.bucket = bucket
        self.endpoint_url = endpoint_url
        self.access_key = access_key
        self.secret_key = secret_key
        self.region = region
        self.prefix = prefix.rstrip("/") + "/"
        self._client = None

    @classmethod
    def from_settings(cls, settings: Settings) -> S3CompatibleStorage:
        bucket = getattr(settings, "object_storage_bucket", None) or "ai-forge"
        secret = getattr(settings, "object_storage_secret_key", None)
        secret_value = secret.get_secret_value() if secret is not None else None
        return cls(
            bucket=bucket,
            endpoint_url=getattr(settings, "object_storage_endpoint", None),
            access_key=getattr(settings, "object_storage_access_key", None),
            secret_key=secret_value,
            region=getattr(settings, "object_storage_region", "us-east-1"),
            prefix=getattr(settings, "object_storage_prefix", "ai-forge/"),
        )

    def _client_or_raise(self):  # type: ignore[no-untyped-def]
        if self._client is not None:
            return self._client
        try:
            import boto3
        except ImportError as exc:
            raise StorageError(
                "boto3 is required for S3/MinIO storage backends."
            ) from exc
        self._client = boto3.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name=self.region,
        )
        return self._client

    def _full_key(self, storage_key: str) -> str:
        return f"{self.prefix}{storage_key.lstrip('/')}"

    def temporary_key(self) -> str:
        return f".tmp/{uuid4().hex}.upload"

    def artifact_key(
        self,
        case_id: UUID,
        evidence_id: UUID,
        artifact_id: UUID,
    ) -> str:
        return f"evidence/{case_id}/{evidence_id}/artifacts/{artifact_id}.artifact"

    async def save_stream(
        self,
        source: BinaryIO,
        storage_key: str,
        *,
        max_bytes: int,
        chunk_size: int,
    ) -> int:
        return await asyncio.to_thread(
            self._save_stream_sync,
            source,
            storage_key,
            max_bytes,
            chunk_size,
        )

    def _save_stream_sync(
        self,
        source: BinaryIO,
        storage_key: str,
        max_bytes: int,
        chunk_size: int,
    ) -> int:
        client = self._client_or_raise()
        buffer = io.BytesIO()
        written = 0
        while chunk := source.read(chunk_size):
            written += len(chunk)
            if written > max_bytes:
                raise FileTooLargeError("The uploaded file exceeds the size limit.")
            buffer.write(chunk)
        buffer.seek(0)
        try:
            client.upload_fileobj(buffer, self.bucket, self._full_key(storage_key))
        except Exception as exc:  # noqa: BLE001
            raise StorageError("Object storage upload failed.") from exc
        return written

    @asynccontextmanager
    async def open(self, storage_key: str) -> AsyncIterator[BinaryIO]:
        handle = await asyncio.to_thread(self._open_sync, storage_key)
        try:
            yield handle
        finally:
            handle.close()

    def _open_sync(self, storage_key: str) -> BinaryIO:
        client = self._client_or_raise()
        buffer = io.BytesIO()
        try:
            client.download_fileobj(self.bucket, self._full_key(storage_key), buffer)
        except Exception as exc:  # noqa: BLE001
            raise StorageError("Object storage download failed.") from exc
        buffer.seek(0)
        return buffer

    async def commit(self, temporary_key: str, storage_key: str) -> None:
        await asyncio.to_thread(self._commit_sync, temporary_key, storage_key)

    def _commit_sync(self, temporary_key: str, storage_key: str) -> None:
        client = self._client_or_raise()
        src = {"Bucket": self.bucket, "Key": self._full_key(temporary_key)}
        try:
            client.copy_object(
                Bucket=self.bucket,
                CopySource=src,
                Key=self._full_key(storage_key),
            )
            client.delete_object(Bucket=self.bucket, Key=self._full_key(temporary_key))
        except Exception as exc:  # noqa: BLE001
            raise StorageError("Object storage commit failed.") from exc

    async def exists(self, storage_key: str) -> bool:
        return await asyncio.to_thread(self._exists_sync, storage_key)

    def _exists_sync(self, storage_key: str) -> bool:
        client = self._client_or_raise()
        try:
            client.head_object(Bucket=self.bucket, Key=self._full_key(storage_key))
            return True
        except Exception:  # noqa: BLE001
            return False

    async def delete(self, storage_key: str) -> None:
        await asyncio.to_thread(self._delete_sync, storage_key)

    def _delete_sync(self, storage_key: str) -> None:
        client = self._client_or_raise()
        try:
            client.delete_object(Bucket=self.bucket, Key=self._full_key(storage_key))
        except Exception as exc:  # noqa: BLE001
            raise StorageError("Object storage delete failed.") from exc
