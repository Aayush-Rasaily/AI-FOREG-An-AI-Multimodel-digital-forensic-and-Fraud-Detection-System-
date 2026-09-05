"""Hash consistency monitoring (read-only; never modifies evidence)."""

from __future__ import annotations

import hashlib
from typing import Any


def custody_hash_mismatch(
    evidence_hash: str,
    custody_hashes: list[str],
) -> list[str]:
    """Return custody hashes that differ from the registered evidence hash."""

    expected = evidence_hash.strip().lower()
    return sorted(
        {
            value
            for value in custody_hashes
            if value and value.strip().lower() != expected
        }
    )


def metadata_fingerprint(metadata: dict[str, Any] | None) -> str:
    """Deterministic fingerprint of evidence metadata."""

    import json

    payload = json.dumps(metadata or {}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def size_mismatch(recorded_size: int, observed_size: int | None) -> bool:
    if observed_size is None:
        return False
    return int(recorded_size) != int(observed_size)
