"""Compose integrity checks, alerts, and timeline from snapshots."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.integrity.custody_validator import custody_gaps
from backend.app.integrity.drift import detect_drifts
from backend.app.integrity.hash_monitor import custody_hash_mismatch, size_mismatch
from backend.app.integrity.models import (
    AlertDraft,
    AlertSeverity,
    CheckDraft,
    CheckStatus,
    DriftDraft,
    ProvenanceBundle,
)
from backend.app.integrity.policy import CHECK_CODES
from backend.app.integrity.provenance_validator import (
    has_audit_coverage,
    missing_provenance_signals,
)


def _ckey(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"imchk_{digest[:24]}"


def _akey(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode()).hexdigest()
    return f"imalert_{digest[:24]}"


def _alert_from_check(check: CheckDraft) -> AlertDraft | None:
    if check.status not in {CheckStatus.FAIL, CheckStatus.WARN}:
        return None
    severity = check.severity
    if check.status == CheckStatus.FAIL and severity == AlertSeverity.INFO:
        severity = AlertSeverity.HIGH
    return AlertDraft(
        alert_key=_akey(
            check.check_code, check.evidence_id or "case", check.status.value
        ),
        alert_code=check.check_code,
        severity=severity,
        title=check.title,
        message=check.message,
        evidence_id=check.evidence_id,
        check_code=check.check_code,
        provenance=check.provenance,
    )


def verify_case_snapshot(
    snapshot: dict[str, Any],
    *,
    previous_fingerprints: dict[str, str] | None = None,
) -> tuple[list[CheckDraft], list[AlertDraft], list[DriftDraft], list[dict[str, Any]]]:
    """Run all deterministic integrity checks for a collected snapshot."""

    evidence = list(snapshot.get("evidence") or [])
    custody_by = dict(snapshot.get("custody_by_evidence") or {})
    audit_ids = set(snapshot.get("audit_evidence_ids") or [])
    ai_ids = set(snapshot.get("ai_evidence_ids") or [])
    report_ids = [str(item["id"]) for item in snapshot.get("reports") or []]
    storage_presence = dict(snapshot.get("storage_presence") or {})
    observed_sizes = dict(snapshot.get("observed_sizes") or {})
    previous = previous_fingerprints or {}

    checks: list[CheckDraft] = []
    timeline: list[dict[str, Any]] = []

    # Case-level missing reports
    if evidence and not report_ids:
        checks.append(
            CheckDraft(
                check_key=_ckey("MISSING_REPORTS", "case"),
                check_code="MISSING_REPORTS",
                title="Missing Reports",
                status=CheckStatus.WARN,
                severity=AlertSeverity.MEDIUM,
                evidence_id=None,
                message="No forensic reports registered for this case.",
                provenance=ProvenanceBundle(detail="missing_reports"),
            )
        )
    else:
        checks.append(
            CheckDraft(
                check_key=_ckey("MISSING_REPORTS", "case", "ok"),
                check_code="MISSING_REPORTS",
                title="Missing Reports",
                status=CheckStatus.PASS
                if report_ids or not evidence
                else CheckStatus.INFO,
                severity=AlertSeverity.INFO,
                evidence_id=None,
                message=(
                    f"{len(report_ids)} report(s) present."
                    if report_ids
                    else "No evidence; report check skipped."
                ),
                provenance=ProvenanceBundle(
                    report_ids=tuple(sorted(report_ids)),
                    detail="reports",
                ),
            )
        )

    # Duplicates by hash within snapshot (should be rare due to DB constraint)
    by_hash: dict[str, list[str]] = {}
    for item in evidence:
        by_hash.setdefault(str(item.get("sha256_hash") or ""), []).append(
            str(item["id"])
        )
    dup_ids = sorted(
        eid
        for hash_val, ids in by_hash.items()
        if hash_val and len(ids) > 1
        for eid in ids
    )
    if dup_ids:
        checks.append(
            CheckDraft(
                check_key=_ckey("DUPLICATE_DETECTION", *dup_ids),
                check_code="DUPLICATE_DETECTION",
                title="Duplicate Detection",
                status=CheckStatus.FAIL,
                severity=AlertSeverity.CRITICAL,
                evidence_id=None,
                message=(
                    f"Duplicate SHA-256 groups involve {len(dup_ids)} evidence items."
                ),
                observed=",".join(dup_ids),
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(dup_ids),
                    detail="duplicates",
                ),
            )
        )
    else:
        checks.append(
            CheckDraft(
                check_key=_ckey("DUPLICATE_DETECTION", "none"),
                check_code="DUPLICATE_DETECTION",
                title="Duplicate Detection",
                status=CheckStatus.PASS if evidence else CheckStatus.INFO,
                severity=AlertSeverity.INFO,
                evidence_id=None,
                message="No duplicate SHA-256 values among case evidence.",
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(str(i["id"]) for i in evidence),
                    detail="duplicates",
                ),
            )
        )

    for item in sorted(evidence, key=lambda row: str(row["id"])):
        eid = str(item["id"])
        ev_hash = str(item.get("sha256_hash") or "")
        custody_events = list(custody_by.get(eid) or [])
        custody_hashes = [
            str(event.get("sha256_hash") or "") for event in custody_events
        ]
        custody_ids = tuple(
            sorted(
                str(event.get("id") or "")
                for event in custody_events
                if event.get("id")
            )
        )
        prov = ProvenanceBundle(
            evidence_ids=(eid,),
            custody_event_ids=custody_ids,
            storage_keys=tuple(
                [str(item["storage_key"])] if item.get("storage_key") else []
            ),
        )

        # SHA-256 consistency vs custody
        mismatches = custody_hash_mismatch(ev_hash, custody_hashes)
        if not custody_events:
            sha_status = CheckStatus.WARN
            sha_msg = "No custody hashes to cross-check."
            sha_sev = AlertSeverity.MEDIUM
        elif mismatches:
            sha_status = CheckStatus.FAIL
            sha_msg = f"Custody hash mismatch(es): {len(mismatches)}."
            sha_sev = AlertSeverity.CRITICAL
        else:
            sha_status = CheckStatus.PASS
            sha_msg = "Custody hashes match registered SHA-256."
            sha_sev = AlertSeverity.INFO
        checks.append(
            CheckDraft(
                check_key=_ckey("SHA256_CONSISTENCY", eid, sha_status.value),
                check_code="SHA256_CONSISTENCY",
                title="SHA-256 Consistency",
                status=sha_status,
                severity=sha_sev,
                evidence_id=eid,
                message=sha_msg,
                expected=ev_hash or None,
                observed=",".join(mismatches) if mismatches else ev_hash or None,
                provenance=prov,
            )
        )

        # File size
        observed = observed_sizes.get(eid)
        if observed is None:
            size_status = CheckStatus.SKIP
            size_msg = "Storage size not observed (storage unavailable or missing)."
            size_sev = AlertSeverity.INFO
        elif size_mismatch(int(item.get("file_size") or 0), int(observed)):
            size_status = CheckStatus.FAIL
            size_msg = "Observed storage size differs from registered file_size."
            size_sev = AlertSeverity.HIGH
        else:
            size_status = CheckStatus.PASS
            size_msg = "File size matches storage object."
            size_sev = AlertSeverity.INFO
        checks.append(
            CheckDraft(
                check_key=_ckey("FILE_SIZE_CONSISTENCY", eid, size_status.value),
                check_code="FILE_SIZE_CONSISTENCY",
                title="File Size Consistency",
                status=size_status,
                severity=size_sev,
                evidence_id=eid,
                message=size_msg,
                expected=str(item.get("file_size")),
                observed=str(observed) if observed is not None else None,
                provenance=prov,
            )
        )

        # MIME consistency (recorded presence)
        mime = str(item.get("mime_type") or "")
        if not mime:
            mime_status = CheckStatus.FAIL
            mime_msg = "MIME type missing on evidence record."
            mime_sev = AlertSeverity.HIGH
        else:
            mime_status = CheckStatus.PASS
            mime_msg = "MIME type present on evidence record."
            mime_sev = AlertSeverity.INFO
        checks.append(
            CheckDraft(
                check_key=_ckey("MIME_CONSISTENCY", eid, mime_status.value),
                check_code="MIME_CONSISTENCY",
                title="MIME Consistency",
                status=mime_status,
                severity=mime_sev,
                evidence_id=eid,
                message=mime_msg,
                expected=mime or None,
                observed=mime or None,
                provenance=prov,
            )
        )

        # Timestamp consistency
        created = str(item.get("created_at") or "")
        updated = str(item.get("updated_at") or "")
        if created and updated and updated < created:
            ts_status = CheckStatus.FAIL
            ts_msg = "updated_at precedes created_at."
            ts_sev = AlertSeverity.HIGH
        else:
            ts_status = CheckStatus.PASS
            ts_msg = "Evidence timestamps are consistent."
            ts_sev = AlertSeverity.INFO
        checks.append(
            CheckDraft(
                check_key=_ckey("TIMESTAMP_CONSISTENCY", eid, ts_status.value),
                check_code="TIMESTAMP_CONSISTENCY",
                title="Timestamp Consistency",
                status=ts_status,
                severity=ts_sev,
                evidence_id=eid,
                message=ts_msg,
                provenance=prov,
            )
        )

        # Custody continuity
        gaps = custody_gaps(custody_events)
        if gaps and custody_events:
            # monotonic issues are FAIL; soft first-type is WARN
            hard = any(
                "monotonic" in g.lower() or "Unparseable" in g or "Missing" in g
                for g in gaps
            )
            soft_only = not hard and any("First custody" in g for g in gaps)
            if hard:
                cust_status = CheckStatus.FAIL
                cust_sev = AlertSeverity.HIGH
            elif soft_only and len(gaps) == 1:
                cust_status = CheckStatus.WARN
                cust_sev = AlertSeverity.LOW
            else:
                cust_status = CheckStatus.WARN
                cust_sev = AlertSeverity.MEDIUM
            cust_msg = "; ".join(gaps)
        elif not custody_events:
            cust_status = CheckStatus.FAIL
            cust_sev = AlertSeverity.CRITICAL
            cust_msg = "No custody events recorded."
        else:
            cust_status = CheckStatus.PASS
            cust_sev = AlertSeverity.INFO
            cust_msg = "Custody chain is continuous."
        checks.append(
            CheckDraft(
                check_key=_ckey("CUSTODY_CONTINUITY", eid, cust_status.value),
                check_code="CUSTODY_CONTINUITY",
                title="Chain-of-Custody Continuity",
                status=cust_status,
                severity=cust_sev,
                evidence_id=eid,
                message=cust_msg,
                provenance=prov,
            )
        )

        # Storage location
        key = str(item.get("storage_key") or "")
        present = storage_presence.get(eid)
        if not key:
            st_status = CheckStatus.FAIL
            st_sev = AlertSeverity.CRITICAL
            st_msg = "Storage key missing."
        elif present is True:
            st_status = CheckStatus.PASS
            st_sev = AlertSeverity.INFO
            st_msg = "Storage object present."
        elif present is False:
            st_status = CheckStatus.FAIL
            st_sev = AlertSeverity.CRITICAL
            st_msg = "Storage object missing for registered key."
        else:
            st_status = CheckStatus.SKIP
            st_sev = AlertSeverity.INFO
            st_msg = "Storage presence not checked."
        checks.append(
            CheckDraft(
                check_key=_ckey("STORAGE_LOCATION", eid, st_status.value),
                check_code="STORAGE_LOCATION",
                title="Storage Location Verification",
                status=st_status,
                severity=st_sev,
                evidence_id=eid,
                message=st_msg,
                expected=key or None,
                provenance=prov,
            )
        )

        # Provenance
        missing = missing_provenance_signals(item)
        if missing:
            checks.append(
                CheckDraft(
                    check_key=_ckey("MISSING_PROVENANCE", eid, *missing),
                    check_code="MISSING_PROVENANCE",
                    title="Missing Provenance",
                    status=CheckStatus.FAIL,
                    severity=AlertSeverity.HIGH,
                    evidence_id=eid,
                    message=f"Missing fields: {', '.join(missing)}.",
                    provenance=prov,
                )
            )
        else:
            checks.append(
                CheckDraft(
                    check_key=_ckey("MISSING_PROVENANCE", eid, "ok"),
                    check_code="MISSING_PROVENANCE",
                    title="Missing Provenance",
                    status=CheckStatus.PASS,
                    severity=AlertSeverity.INFO,
                    evidence_id=eid,
                    message="Core provenance fields present.",
                    provenance=prov,
                )
            )

        # Audit
        if has_audit_coverage(eid, audit_ids):
            checks.append(
                CheckDraft(
                    check_key=_ckey("MISSING_AUDIT", eid, "ok"),
                    check_code="MISSING_AUDIT",
                    title="Missing Audit Entries",
                    status=CheckStatus.PASS,
                    severity=AlertSeverity.INFO,
                    evidence_id=eid,
                    message="Audit events reference this evidence.",
                    provenance=ProvenanceBundle(
                        evidence_ids=(eid,),
                        detail="audit",
                    ),
                )
            )
        else:
            checks.append(
                CheckDraft(
                    check_key=_ckey("MISSING_AUDIT", eid, "missing"),
                    check_code="MISSING_AUDIT",
                    title="Missing Audit Entries",
                    status=CheckStatus.WARN,
                    severity=AlertSeverity.MEDIUM,
                    evidence_id=eid,
                    message="No audit events reference this evidence.",
                    provenance=ProvenanceBundle(
                        evidence_ids=(eid,),
                        detail="audit",
                    ),
                )
            )

        # AI artifacts (advisory)
        if eid in ai_ids:
            checks.append(
                CheckDraft(
                    check_key=_ckey("MISSING_AI_ARTIFACTS", eid, "ok"),
                    check_code="MISSING_AI_ARTIFACTS",
                    title="Missing AI Artifacts",
                    status=CheckStatus.PASS,
                    severity=AlertSeverity.INFO,
                    evidence_id=eid,
                    message="Stored AI findings present (not re-run).",
                    provenance=prov,
                )
            )
        else:
            checks.append(
                CheckDraft(
                    check_key=_ckey("MISSING_AI_ARTIFACTS", eid, "missing"),
                    check_code="MISSING_AI_ARTIFACTS",
                    title="Missing AI Artifacts",
                    status=CheckStatus.INFO,
                    severity=AlertSeverity.LOW,
                    evidence_id=eid,
                    message="No stored AI findings for this evidence.",
                    provenance=prov,
                )
            )

        timeline.append(
            {
                "evidence_id": eid,
                "event": "integrity_evaluated",
                "sha256": ev_hash,
                "custody_events": len(custody_events),
                "storage_present": present,
            }
        )

    # Metadata drift (case-level aggregation of per-evidence drifts)
    drifts = detect_drifts(evidence, previous)
    if drifts:
        for drift in drifts:
            checks.append(
                CheckDraft(
                    check_key=_ckey("METADATA_DRIFT", drift.drift_key),
                    check_code="METADATA_DRIFT",
                    title="Metadata Drift",
                    status=CheckStatus.WARN,
                    severity=AlertSeverity.MEDIUM,
                    evidence_id=drift.evidence_id,
                    message=drift.message,
                    expected=drift.previous_value,
                    observed=drift.current_value,
                    provenance=drift.provenance,
                )
            )
    else:
        checks.append(
            CheckDraft(
                check_key=_ckey("METADATA_DRIFT", "none"),
                check_code="METADATA_DRIFT",
                title="Metadata Drift",
                status=CheckStatus.PASS if evidence else CheckStatus.INFO,
                severity=AlertSeverity.INFO,
                evidence_id=None,
                message=(
                    "No metadata drift vs prior monitor snapshot."
                    if previous
                    else "No prior snapshot; drift baseline will be recorded."
                ),
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(str(i["id"]) for i in evidence),
                    detail="metadata_drift",
                ),
            )
        )

    # Ensure deterministic order by policy codes then evidence id
    code_order = {code: idx for idx, (code, _) in enumerate(CHECK_CODES)}
    checks.sort(
        key=lambda item: (
            code_order.get(item.check_code, 999),
            item.evidence_id or "",
            item.check_key,
        )
    )
    alerts = [
        alert for check in checks if (alert := _alert_from_check(check)) is not None
    ]
    alerts.sort(
        key=lambda item: (
            item.severity.value,
            item.alert_code,
            item.evidence_id or "",
            item.alert_key,
        )
    )
    timeline.sort(key=lambda item: str(item.get("evidence_id") or ""))
    return checks, alerts, drifts, timeline
