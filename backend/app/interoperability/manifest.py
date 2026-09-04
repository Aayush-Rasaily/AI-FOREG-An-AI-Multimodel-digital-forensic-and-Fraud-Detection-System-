"""Investigation package manifest generation."""

from __future__ import annotations

from typing import Any

from backend.app.interoperability.hashing import (
    canonical_json_bytes,
    package_checksum_from_files,
    sha256_bytes,
)
from backend.app.interoperability.policy import (
    INTEROP_ENGINE_VERSION,
    INTEROP_POLICY_VERSION,
    PACKAGE_SCHEMA_VERSION,
    PACKAGE_VERSION,
)


def build_manifest(
    *,
    created_at: str,
    case_id: str,
    case_number: str,
    format_name: str,
    file_checksums: dict[str, str],
    evidence_count: int,
    report_count: int,
    timeline_count: int,
    policy_versions: dict[str, str],
    ai_engine_versions: dict[str, str],
    evidence_ids: list[str],
    report_versions: list[str],
    timeline_version: str | None,
    export_version: str = PACKAGE_VERSION,
) -> dict[str, Any]:
    """Build a deterministic package manifest (excludes package_checksum)."""

    files = [
        {"path": path, "sha256": file_checksums[path]}
        for path in sorted(file_checksums.keys())
    ]
    package_checksum = package_checksum_from_files(file_checksums)
    manifest: dict[str, Any] = {
        "package_version": export_version,
        "schema_version": PACKAGE_SCHEMA_VERSION,
        "created_at": created_at,
        "case_id": case_id,
        "case_number": case_number,
        "format": format_name,
        "evidence_count": evidence_count,
        "report_count": report_count,
        "timeline_count": timeline_count,
        "files": files,
        "package_checksum": package_checksum,
        "policy_versions": dict(sorted(policy_versions.items())),
        "ai_engine_versions": dict(sorted(ai_engine_versions.items())),
        "provenance": {
            "export_version": export_version,
            "evidence_included": sorted(evidence_ids),
            "report_versions": sorted(report_versions),
            "timeline_version": timeline_version,
            "policy_versions": dict(sorted(policy_versions.items())),
            "package_checksum": package_checksum,
            "engine_version": INTEROP_ENGINE_VERSION,
            "policy_version": INTEROP_POLICY_VERSION,
        },
        "engine_version": INTEROP_ENGINE_VERSION,
        "policy_version": INTEROP_POLICY_VERSION,
    }
    return manifest


def manifest_checksum(manifest: dict[str, Any]) -> str:
    """SHA-256 of the canonical manifest JSON (including package_checksum)."""

    return sha256_bytes(canonical_json_bytes(manifest))


def finalize_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Attach manifest_checksum to provenance and top-level fields."""

    checksum = manifest_checksum(manifest)
    result = dict(manifest)
    provenance = dict(result.get("provenance") or {})
    provenance["manifest_checksum"] = checksum
    result["provenance"] = provenance
    result["manifest_checksum"] = checksum
    return result
