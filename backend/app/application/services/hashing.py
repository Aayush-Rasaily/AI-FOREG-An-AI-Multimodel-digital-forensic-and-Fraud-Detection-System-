"""Streaming SHA-256 hashing service."""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True, slots=True)
class HashResult:
    """Digest and byte count for one exact input stream."""

    sha256_hash: str
    file_size: int


class HashService:
    """Calculate hashes without loading an evidence object into memory."""

    async def hash_stream(self, stream: BinaryIO, *, chunk_size: int) -> HashResult:
        """Hash a binary stream in a worker thread using bounded chunks."""

        return await asyncio.to_thread(self._hash_stream_sync, stream, chunk_size)

    @staticmethod
    def _hash_stream_sync(stream: BinaryIO, chunk_size: int) -> HashResult:
        digest = hashlib.sha256()
        file_size = 0
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
            file_size += len(chunk)
        return HashResult(digest.hexdigest(), file_size)
