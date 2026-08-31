"""Local development object storage for evidence originals."""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path, PurePosixPath
from typing import BinaryIO
from uuid import UUID

from backend.app.application.services.storage import storage_root
from backend.app.core.exceptions import FileTooLargeError, StorageError


class LocalStorage:
    """Filesystem-backed storage with opaque, traversal-safe object keys."""

    def __init__(self, root: Path) -> None:
        self.root = storage_root(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def temporary_key(self) -> str:
        """Return a temporary object key under the private staging prefix."""

        from uuid import uuid4

        return f".tmp/{uuid4().hex}.upload"

    def artifact_key(
        self,
        case_id: UUID,
        evidence_id: UUID,
        artifact_id: UUID,
    ) -> str:
        """Return a stable derived-artifact key below the evidence prefix."""

        return f"evidence/{case_id}/{evidence_id}/artifacts/{artifact_id}.artifact"

    async def save_stream(
        self,
        source: BinaryIO,
        storage_key: str,
        *,
        max_bytes: int,
        chunk_size: int,
    ) -> int:
        """Copy a stream to an exclusive object without buffering it in memory."""

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
        destination_path = self._safe_path(storage_key)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        try:
            with destination_path.open("xb") as destination:
                while chunk := source.read(chunk_size):
                    written += len(chunk)
                    if written > max_bytes:
                        raise FileTooLargeError(
                            "The uploaded file exceeds the size limit."
                        )
                    destination.write(chunk)
        except FileTooLargeError:
            self._unlink_if_present(destination_path)
            raise
        except FileExistsError as exc:
            raise StorageError("The storage object already exists.") from exc
        except OSError as exc:
            self._unlink_if_present(destination_path)
            raise StorageError("The storage operation failed.") from exc
        return written

    @asynccontextmanager
    async def open(self, storage_key: str) -> AsyncIterator[BinaryIO]:
        """Open a stored object for streaming reads."""

        path = self._safe_path(storage_key)
        try:
            handle = await asyncio.to_thread(path.open, "rb")
        except OSError as exc:
            raise StorageError("The storage object could not be opened.") from exc
        try:
            yield handle
        finally:
            await asyncio.to_thread(handle.close)

    async def commit(self, temporary_key: str, storage_key: str) -> None:
        """Move a staged object atomically without replacing an existing object."""

        temporary_path = self._safe_path(temporary_key)
        destination_path = self._safe_path(storage_key)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            await asyncio.to_thread(os.link, temporary_path, destination_path)
            await asyncio.to_thread(temporary_path.unlink)
        except FileExistsError as exc:
            raise StorageError("The storage object already exists.") from exc
        except OSError:
            try:
                await asyncio.to_thread(
                    self._exclusive_copy,
                    temporary_path,
                    destination_path,
                )
                await asyncio.to_thread(temporary_path.unlink)
            except FileExistsError as exc:
                raise StorageError("The storage object already exists.") from exc
            except OSError as exc:
                self._unlink_if_present(destination_path)
                raise StorageError("The storage commit failed.") from exc

    @staticmethod
    def _exclusive_copy(source: Path, destination: Path) -> None:
        with (
            source.open("rb") as source_handle,
            destination.open("xb") as destination_handle,
        ):
            while chunk := source_handle.read(1024 * 1024):
                destination_handle.write(chunk)

    async def exists(self, storage_key: str) -> bool:
        """Return whether an object exists under a validated key."""

        return await asyncio.to_thread(self._safe_path(storage_key).is_file)

    async def delete(self, storage_key: str) -> None:
        """Delete one object for controlled failure cleanup."""

        path = self._safe_path(storage_key)
        try:
            await asyncio.to_thread(self._unlink_if_present, path)
        except OSError as exc:
            raise StorageError("The storage cleanup failed.") from exc

    def _safe_path(self, storage_key: str) -> Path:
        """Resolve an internal key while rejecting traversal and absolute paths."""

        if (
            not storage_key
            or "\x00" in storage_key
            or "\\" in storage_key
            or ":" in storage_key
        ):
            raise StorageError("The storage key is invalid.")
        key_path = PurePosixPath(storage_key)
        if key_path.is_absolute() or ".." in key_path.parts:
            raise StorageError("The storage key is invalid.")
        resolved = (self.root / Path(*key_path.parts)).resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise StorageError("The storage key is invalid.")
        return resolved

    @staticmethod
    def _unlink_if_present(path: Path) -> None:
        try:
            path.unlink()
        except FileNotFoundError:
            return
