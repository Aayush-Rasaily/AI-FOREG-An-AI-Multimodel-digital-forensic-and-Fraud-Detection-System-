"""Storage service contract for evidence object persistence."""

from contextlib import AbstractAsyncContextManager
from pathlib import Path
from typing import BinaryIO, Protocol


class StorageService(Protocol):
    """Opaque object-storage contract used by the evidence service."""

    def temporary_key(self) -> str:
        """Return a collision-resistant key for a temporary upload object."""
        ...

    async def save_stream(
        self,
        source: BinaryIO,
        storage_key: str,
        *,
        max_bytes: int,
        chunk_size: int,
    ) -> int:
        """Persist a stream without loading the entire object in memory."""
        ...

    def open(self, storage_key: str) -> AbstractAsyncContextManager[BinaryIO]:
        """Open an object for streaming reads."""
        ...

    async def commit(self, temporary_key: str, storage_key: str) -> None:
        """Atomically commit a temporary object without overwriting."""
        ...

    async def exists(self, storage_key: str) -> bool:
        """Return whether an opaque storage object exists."""
        ...

    async def delete(self, storage_key: str) -> None:
        """Delete an object during controlled failure cleanup."""
        ...


def storage_root(root: Path) -> Path:
    """Normalize a configured local root without exposing it externally."""

    return root.expanduser().resolve()
