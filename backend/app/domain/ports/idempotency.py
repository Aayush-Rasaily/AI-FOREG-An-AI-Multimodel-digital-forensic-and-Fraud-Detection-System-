"""Domain port for deduplicating retried commands and messages."""

from typing import Protocol


class IdempotencyStore(Protocol):
    """Port for an atomic, TTL-backed idempotency key store."""

    async def claim(self, key: str, *, ttl_seconds: int) -> bool:
        """Atomically claim a key, returning false when already claimed."""
        ...
