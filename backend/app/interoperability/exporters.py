"""Deterministic exporters for investigation packages."""

from __future__ import annotations

import csv
import io
from typing import Any

from backend.app.interoperability.hashing import canonical_json_bytes, sha256_bytes
from backend.app.interoperability.manifest import build_manifest, finalize_manifest
from backend.app.interoperability.models import InvestigationSnapshot
from backend.app.interoperability.policy import ExportFormat


def _json_member(path: str, payload: Any, files: dict[str, bytes]) -> None:
    files[path] = canonical_json_bytes(payload)


def _attach_manifest(
    *,
    files: dict[str, bytes],
    snapshot: InvestigationSnapshot,
    format_name: str,
    created_at: str,
) -> dict[str, Any]:
    checksums = {
        path: sha256_bytes(payload)
        for path, payload in files.items()
        if path != "manifest.json"
    }
    case = snapshot.case
    evidence_ids = [str(item.get("id")) for item in snapshot.evidence]
    report_versions = [
        str(item.get("report_version") or item.get("id"))
        for item in snapshot.reports
    ]
    timeline_version = None
    if snapshot.timeline:
        timeline_version = str(
            snapshot.timeline.get("id")
            or snapshot.timeline.get("policy_version")
            or ""
        ) or None
    manifest = build_manifest(
        created_at=created_at,
        case_id=str(case.get("id")),
        case_number=str(case.get("case_number")),
        format_name=format_name,
        file_checksums=checksums,
        evidence_count=len(snapshot.evidence),
        report_count=len(snapshot.reports),
        timeline_count=1 if snapshot.timeline else 0,
        policy_versions=snapshot.policy_versions,
        ai_engine_versions=snapshot.ai_engine_versions,
        evidence_ids=evidence_ids,
        report_versions=report_versions,
        timeline_version=timeline_version,
    )
    manifest = finalize_manifest(manifest)
    files["manifest.json"] = canonical_json_bytes(manifest)
    return manifest


def export_json_package(
    snapshot: InvestigationSnapshot,
    *,
    created_at: str,
    evidence_blobs: dict[str, bytes] | None = None,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Build a full JSON investigation package member map."""

    files: dict[str, bytes] = {}
    _json_member("case.json", snapshot.case, files)
    _json_member("evidence/index.json", snapshot.evidence, files)
    for item in sorted(snapshot.evidence, key=lambda row: str(row.get("id"))):
        eid = str(item.get("id"))
        _json_member(f"evidence/{eid}.json", item, files)
    _json_member("custody/events.json", snapshot.custody, files)
    _json_member("extractions/index.json", snapshot.extractions, files)
    _json_member("ai/summaries.json", snapshot.ai_summaries, files)
    _json_member("fusion/summaries.json", snapshot.fusion_summaries, files)
    _json_member(
        "correlation/summaries.json",
        snapshot.correlation_summaries,
        files,
    )
    if snapshot.timeline is not None:
        _json_member("timeline/timeline.json", snapshot.timeline, files)
    _json_member("reports/index.json", snapshot.reports, files)
    if snapshot.workflow is not None:
        _json_member("workflow/status.json", snapshot.workflow, files)
    if snapshot.security is not None:
        _json_member("security/metadata.json", snapshot.security, files)
    if evidence_blobs:
        for eid, blob in sorted(evidence_blobs.items()):
            files[f"evidence/binaries/{eid}.bin"] = blob
    manifest = _attach_manifest(
        files=files,
        snapshot=snapshot,
        format_name=ExportFormat.JSON_PACKAGE.value,
        created_at=created_at,
    )
    return files, manifest


def export_csv_package(
    snapshot: InvestigationSnapshot,
    *,
    created_at: str,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Export case + evidence metadata as CSV members."""

    files: dict[str, bytes] = {}
    case_buf = io.StringIO()
    case_writer = csv.DictWriter(
        case_buf,
        fieldnames=sorted(snapshot.case.keys()),
        extrasaction="ignore",
    )
    case_writer.writeheader()
    case_writer.writerow(
        {key: snapshot.case.get(key) for key in sorted(snapshot.case.keys())}
    )
    files["case.csv"] = case_buf.getvalue().encode("utf-8")

    evidence_fields = sorted(
        {
            key
            for item in snapshot.evidence
            for key in item.keys()
        }
    ) or ["id"]
    ev_buf = io.StringIO()
    ev_writer = csv.DictWriter(
        ev_buf, fieldnames=evidence_fields, extrasaction="ignore",
    )
    ev_writer.writeheader()
    for item in sorted(snapshot.evidence, key=lambda row: str(row.get("id", ""))):
        ev_writer.writerow({key: item.get(key) for key in evidence_fields})
    files["evidence.csv"] = ev_buf.getvalue().encode("utf-8")

    manifest = _attach_manifest(
        files=files,
        snapshot=snapshot,
        format_name=ExportFormat.CSV.value,
        created_at=created_at,
    )
    return files, manifest


def export_pdf_bundle(
    snapshot: InvestigationSnapshot,
    *,
    created_at: str,
    pdf_blobs: dict[str, bytes],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Bundle existing PDF report bytes without regenerating analyses."""

    files: dict[str, bytes] = {}
    _json_member("reports/index.json", snapshot.reports, files)
    for report_id, blob in sorted(pdf_blobs.items()):
        files[f"reports/pdf/{report_id}.pdf"] = blob
    manifest = _attach_manifest(
        files=files,
        snapshot=snapshot,
        format_name=ExportFormat.PDF_BUNDLE.value,
        created_at=created_at,
    )
    return files, manifest


def export_zip_evidence(
    snapshot: InvestigationSnapshot,
    *,
    created_at: str,
    evidence_blobs: dict[str, bytes],
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """ZIP evidence package with metadata + optional binary payloads."""

    files: dict[str, bytes] = {}
    _json_member("case.json", snapshot.case, files)
    _json_member("evidence/index.json", snapshot.evidence, files)
    for eid, blob in sorted(evidence_blobs.items()):
        files[f"evidence/binaries/{eid}.bin"] = blob
    _json_member("custody/events.json", snapshot.custody, files)
    manifest = _attach_manifest(
        files=files,
        snapshot=snapshot,
        format_name=ExportFormat.ZIP_EVIDENCE.value,
        created_at=created_at,
    )
    return files, manifest


def export_manifest_only(
    snapshot: InvestigationSnapshot,
    *,
    created_at: str,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    """Manifest package with a checksums placeholder member only."""

    files: dict[str, bytes] = {}
    _json_member(
        "checksums.json",
        {
            "evidence": [
                {
                    "id": item.get("id"),
                    "sha256": item.get("sha256_hash"),
                }
                for item in sorted(
                    snapshot.evidence, key=lambda row: str(row.get("id"))
                )
            ]
        },
        files,
    )
    manifest = _attach_manifest(
        files=files,
        snapshot=snapshot,
        format_name=ExportFormat.MANIFEST.value,
        created_at=created_at,
    )
    return files, manifest
