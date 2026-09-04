"""Interoperability policy constants and format catalogs."""

from __future__ import annotations

from enum import StrEnum

INTEROP_POLICY_VERSION = "1.0"
INTEROP_ENGINE_VERSION = "9a.1.0"
PACKAGE_SCHEMA_VERSION = "1.0"
PACKAGE_VERSION = "1.0"

# Fixed ZipInfo date for byte-identical archives given identical file payloads.
DETERMINISTIC_ZIP_DATE = (2020, 1, 1, 0, 0, 0)


class ExportFormat(StrEnum):
    """Supported export package formats."""

    JSON_PACKAGE = "json_package"
    CSV = "csv"
    PDF_BUNDLE = "pdf_bundle"
    ZIP_EVIDENCE = "zip_evidence"
    MANIFEST = "manifest"


class JobStatus(StrEnum):
    """Export / import job lifecycle."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CONFLICTS = "CONFLICTS"
    INVALID = "INVALID"


SUPPORTED_EXPORT_FORMATS: tuple[str, ...] = tuple(
    item.value for item in ExportFormat
)

REQUIRED_MANIFEST_KEYS: tuple[str, ...] = (
    "package_version",
    "schema_version",
    "created_at",
    "evidence_count",
    "report_count",
    "timeline_count",
    "files",
    "package_checksum",
    "policy_versions",
)
