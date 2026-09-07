"""Input validation helpers for HTTP security hardening (Phase 10D)."""

from __future__ import annotations

import re
from typing import Any

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:@/\-]{1,256}$")


def sanitize_string(
    value: str | None,
    *,
    max_length: int = 1024,
    allow_empty: bool = False,
) -> str:
    """Normalize and bound a user-supplied string."""

    if value is None:
        if allow_empty:
            return ""
        raise ValueError("Value is required.")
    cleaned = _CONTROL_CHARS.sub("", value).strip()
    if not cleaned and not allow_empty:
        raise ValueError("Value is empty.")
    if len(cleaned) > max_length:
        raise ValueError("Value exceeds maximum length.")
    return cleaned


def reject_path_traversal(value: str) -> str:
    """Reject path segments that attempt directory traversal."""

    if "\x00" in value:
        raise ValueError("Null bytes are not allowed.")
    normalized = value.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError("Path traversal is not allowed.")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:/", normalized):
        raise ValueError("Absolute paths are not allowed.")
    return value


def is_safe_identifier(value: str) -> bool:
    return bool(_SAFE_TOKEN.fullmatch(value))


def clamp_pagination(
    *,
    limit: int,
    offset: int,
    max_limit: int = 100,
) -> tuple[int, int]:
    """Bound pagination inputs for list/search APIs."""

    safe_limit = max(1, min(int(limit), max_limit))
    safe_offset = max(0, int(offset))
    return safe_limit, safe_offset


def validate_json_object_depth(
    payload: Any,
    *,
    max_depth: int = 12,
    max_keys: int = 500,
) -> None:
    """Reject deeply nested or extremely wide JSON objects."""

    def _walk(node: Any, depth: int) -> int:
        if depth > max_depth:
            raise ValueError("JSON nesting exceeds maximum depth.")
        count = 0
        if isinstance(node, dict):
            if len(node) > max_keys:
                raise ValueError("JSON object exceeds maximum key count.")
            for value in node.values():
                count += 1 + _walk(value, depth + 1)
        elif isinstance(node, list):
            if len(node) > max_keys:
                raise ValueError("JSON array exceeds maximum length.")
            for value in node:
                count += 1 + _walk(value, depth + 1)
        return count

    _walk(payload, 0)
