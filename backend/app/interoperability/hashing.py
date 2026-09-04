"""Deterministic hashing helpers for interoperability packages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(payload: bytes) -> str:
    """Return lowercase hex SHA-256 for raw bytes."""

    return hashlib.sha256(payload).hexdigest()


def sha256_text(text: str) -> str:
    """Return SHA-256 for UTF-8 text."""

    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    """Stream a file and return its SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    """Serialize JSON with stable key ordering and separators."""

    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")


def package_checksum_from_files(file_checksums: dict[str, str]) -> str:
    """Compute overall package checksum from sorted path→sha256 map."""

    lines = [
        f"{path}:{file_checksums[path]}"
        for path in sorted(file_checksums.keys())
    ]
    return sha256_text("\n".join(lines) + ("\n" if lines else ""))
