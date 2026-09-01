"""In-memory model instance cache."""

from __future__ import annotations

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass

from backend.app.ai.models.base import AIModel

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CacheEntry:
    """One cached model instance."""

    model: AIModel
    device: str
    loaded_at: float
    last_used_at: float
    hits: int = 0


@dataclass(slots=True)
class CacheStatistics:
    """Aggregate cache performance metrics."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    entries: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "entries": self.entries,
        }


class CacheManager:
    """Cache loaded models to avoid reloading on every request."""

    def __init__(self, *, max_models: int = 8, ttl_seconds: int = 3600) -> None:
        self.max_models = max_models
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStatistics()

    def get(self, name: str) -> AIModel | None:
        """Return a cached model if present and not expired."""

        entry = self._entries.get(name)
        if entry is None:
            self._stats.misses += 1
            return None
        if self._is_expired(entry):
            self.evict(name)
            self._stats.misses += 1
            return None
        entry.hits += 1
        entry.last_used_at = time.monotonic()
        self._entries.move_to_end(name)
        self._stats.hits += 1
        return entry.model

    def put(self, name: str, model: AIModel, *, device: str) -> None:
        """Store a loaded model instance."""

        if name in self._entries:
            self.evict(name)
        while len(self._entries) >= self.max_models:
            oldest = next(iter(self._entries))
            self.evict(oldest)
        now = time.monotonic()
        self._entries[name] = CacheEntry(
            model=model,
            device=device,
            loaded_at=now,
            last_used_at=now,
        )
        self._stats.entries = len(self._entries)

    def evict(self, name: str) -> None:
        """Remove one model from the cache."""

        entry = self._entries.pop(name, None)
        if entry is None:
            return
        if entry.model.is_loaded:
            entry.model.unload()
        self._stats.evictions += 1
        self._stats.entries = len(self._entries)
        logger.info("Evicted model from cache", extra={"model": name})

    def clear(self) -> None:
        """Evict all cached models."""

        for name in list(self._entries):
            self.evict(name)

    def statistics(self) -> CacheStatistics:
        """Return cache hit/miss statistics."""

        self._stats.entries = len(self._entries)
        return self._stats

    def state(self, name: str) -> dict[str, object] | None:
        """Return cache state for one model."""

        entry = self._entries.get(name)
        if entry is None:
            return None
        return {
            "device": entry.device,
            "loaded_at": entry.loaded_at,
            "last_used_at": entry.last_used_at,
            "hits": entry.hits,
            "loaded": entry.model.is_loaded,
        }

    def _is_expired(self, entry: CacheEntry) -> bool:
        return (time.monotonic() - entry.last_used_at) > self.ttl_seconds
