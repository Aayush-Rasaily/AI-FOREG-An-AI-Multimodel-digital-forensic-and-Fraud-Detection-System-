"""Domain port for durable evidence and result artifact storage."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """Opaque reference to content stored outside the relational database."""

    uri: str
    content_type: str
    size_bytes: int
    checksum: str


class ArtifactStore(Protocol):
    """Port implemented by an encrypted, durable object-storage adapter."""

    async def put(
        self,
        content: AsyncIterator[bytes],
        *,
        content_type: str,
        checksum: str,
    ) -> ArtifactReference:
        """Persist a streamed artifact and return its immutable reference."""
        ...

    async def get(self, reference: ArtifactReference) -> AsyncIterator[bytes]:
        """Stream an artifact without loading it fully into process memory."""
        ...
