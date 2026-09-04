"""Import package validators."""

from __future__ import annotations

import json
from typing import Any

from backend.app.interoperability.hashing import (
    package_checksum_from_files,
    sha256_bytes,
)
from backend.app.interoperability.manifest import manifest_checksum
from backend.app.interoperability.models import ValidationFinding, ValidationResult
from backend.app.interoperability.policy import (
    PACKAGE_SCHEMA_VERSION,
    REQUIRED_MANIFEST_KEYS,
)


def validate_package(
    *,
    members: dict[str, bytes],
    existing_case_numbers: set[str],
    existing_case_ids: set[str],
) -> ValidationResult:
    """Validate schema, hashes, duplicates, and package integrity."""

    findings: list[ValidationFinding] = []
    conflicts: list[str] = []

    if "manifest.json" not in members:
        findings.append(
            ValidationFinding(
                check="manifest_present",
                status="FAIL",
                message="manifest.json is missing from the package.",
            )
        )
        return ValidationResult(
            valid=False,
            integrity_status="INVALID",
            findings=sorted(findings, key=lambda item: item.check),
            conflicts=conflicts,
            package_version=None,
            schema_version=None,
        )

    try:
        manifest = json.loads(members["manifest.json"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        findings.append(
            ValidationFinding(
                check="manifest_parse",
                status="FAIL",
                message=f"manifest.json is not valid JSON: {type(exc).__name__}",
            )
        )
        return ValidationResult(
            valid=False,
            integrity_status="INVALID",
            findings=sorted(findings, key=lambda item: item.check),
            conflicts=conflicts,
            package_version=None,
            schema_version=None,
        )

    findings.append(
        ValidationFinding(
            check="manifest_present",
            status="PASS",
            message="manifest.json is present and parseable.",
        )
    )

    missing = [key for key in REQUIRED_MANIFEST_KEYS if key not in manifest]
    findings.append(
        ValidationFinding(
            check="schema",
            status="FAIL" if missing else "PASS",
            message=(
                f"Missing required manifest keys: {', '.join(missing)}"
                if missing
                else "Required manifest keys are present."
            ),
        )
    )

    schema_version = manifest.get("schema_version")
    schema_ok = schema_version == PACKAGE_SCHEMA_VERSION
    findings.append(
        ValidationFinding(
            check="package_version",
            status="PASS" if schema_ok else "FAIL",
            message=(
                f"schema_version {PACKAGE_SCHEMA_VERSION} accepted."
                if schema_ok
                else (
                    f"Unsupported schema_version {schema_version!r}; "
                    f"expected {PACKAGE_SCHEMA_VERSION}."
                )
            ),
        )
    )

    declared_files = {
        item["path"]: item["sha256"]
        for item in manifest.get("files", [])
        if isinstance(item, dict) and "path" in item and "sha256" in item
    }
    content_checksums: dict[str, str] = {}
    hash_ok = True
    for path, payload in sorted(members.items()):
        if path == "manifest.json":
            continue
        digest = sha256_bytes(payload)
        content_checksums[path] = digest
        expected = declared_files.get(path)
        if expected is None:
            hash_ok = False
            findings.append(
                ValidationFinding(
                    check="hashes",
                    status="FAIL",
                    message=f"File {path} is not listed in the manifest.",
                )
            )
        elif expected != digest:
            hash_ok = False
            findings.append(
                ValidationFinding(
                    check="hashes",
                    status="FAIL",
                    message=f"Hash mismatch for {path}.",
                )
            )

    for path in sorted(declared_files.keys()):
        if path not in members:
            hash_ok = False
            findings.append(
                ValidationFinding(
                    check="hashes",
                    status="FAIL",
                    message=f"Manifest lists missing file {path}.",
                )
            )

    if hash_ok:
        findings.append(
            ValidationFinding(
                check="hashes",
                status="PASS",
                message="All declared file hashes match package contents.",
            )
        )

    expected_pkg = package_checksum_from_files(content_checksums)
    pkg_ok = manifest.get("package_checksum") == expected_pkg
    findings.append(
        ValidationFinding(
            check="checksum_integrity",
            status="PASS" if pkg_ok else "FAIL",
            message=(
                "Package checksum matches declared file digests."
                if pkg_ok
                else "Overall package_checksum does not match file digests."
            ),
        )
    )

    declared_manifest_checksum = manifest.get("manifest_checksum")
    if declared_manifest_checksum:
        stripped = {
            key: value
            for key, value in manifest.items()
            if key != "manifest_checksum"
        }
        provenance = dict(stripped.get("provenance") or {})
        provenance.pop("manifest_checksum", None)
        stripped["provenance"] = provenance
        computed = manifest_checksum(stripped)
        findings.append(
            ValidationFinding(
                check="manifest",
                status="PASS" if computed == declared_manifest_checksum else "FAIL",
                message=(
                    "Manifest checksum is valid."
                    if computed == declared_manifest_checksum
                    else "manifest_checksum does not match canonical manifest."
                ),
            )
        )
    else:
        findings.append(
            ValidationFinding(
                check="manifest",
                status="WARN",
                message="manifest_checksum not present; skipped.",
            )
        )

    case_number = manifest.get("case_number")
    case_id = manifest.get("case_id")
    meta_ok = bool(case_number) and bool(case_id)
    findings.append(
        ValidationFinding(
            check="required_metadata",
            status="PASS" if meta_ok else "FAIL",
            message=(
                "Case identifiers are present."
                if meta_ok
                else "case_id and case_number are required in the manifest."
            ),
        )
    )

    if case_number and case_number in existing_case_numbers:
        conflicts.append(f"case_number:{case_number}")
    if case_id and case_id in existing_case_ids:
        conflicts.append(f"case_id:{case_id}")

    findings.append(
        ValidationFinding(
            check="duplicate_identifiers",
            status="FAIL" if conflicts else "PASS",
            message=(
                "Import would collide with existing investigations: "
                + ", ".join(sorted(conflicts))
                if conflicts
                else "No duplicate case identifiers detected."
            ),
        )
    )

    findings = sorted(findings, key=lambda item: (item.check, item.message))
    failed = [item for item in findings if item.status == "FAIL"]
    warned = [item for item in findings if item.status == "WARN"]
    hard_checks = {
        "manifest_present",
        "manifest_parse",
        "schema",
        "package_version",
        "hashes",
        "checksum_integrity",
        "required_metadata",
        "manifest",
    }
    hard_fails = [item for item in failed if item.check in hard_checks]

    if hard_fails:
        integrity_status = "INVALID"
        valid = False
    elif conflicts:
        integrity_status = "CONFLICTS"
        valid = False
    elif warned:
        integrity_status = "DEGRADED"
        valid = True
    else:
        integrity_status = "VALID"
        valid = True

    return ValidationResult(
        valid=valid,
        integrity_status=integrity_status,
        findings=findings,
        conflicts=sorted(conflicts),
        package_version=manifest.get("package_version"),
        schema_version=schema_version if isinstance(schema_version, str) else None,
    )


def validate_manifest_dict(manifest: dict[str, Any]) -> list[ValidationFinding]:
    """Lightweight in-memory manifest key validation."""

    missing = [key for key in REQUIRED_MANIFEST_KEYS if key not in manifest]
    if missing:
        return [
            ValidationFinding(
                check="schema",
                status="FAIL",
                message=f"Missing keys: {', '.join(missing)}",
            )
        ]
    return [
        ValidationFinding(
            check="schema",
            status="PASS",
            message="Manifest schema keys present.",
        )
    ]
