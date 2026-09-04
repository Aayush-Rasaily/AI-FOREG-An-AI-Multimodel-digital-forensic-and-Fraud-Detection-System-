"""Import helpers for validated investigation packages."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.app.interoperability.archive import read_zip_members
from backend.app.interoperability.models import ValidationResult
from backend.app.interoperability.validators import validate_package


def load_package_members(path: Path) -> dict[str, bytes]:
    """Load package members from a ZIP path."""

    return read_zip_members(path)


def parse_case_payload(members: dict[str, bytes]) -> dict[str, Any] | None:
    """Extract case.json when present."""

    raw = members.get("case.json")
    if raw is None:
        return None
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def run_import_validation(
    *,
    members: dict[str, bytes],
    existing_case_numbers: set[str],
    existing_case_ids: set[str],
) -> ValidationResult:
    """Validate an import package without mutating investigations."""

    return validate_package(
        members=members,
        existing_case_numbers=existing_case_numbers,
        existing_case_ids=existing_case_ids,
    )
