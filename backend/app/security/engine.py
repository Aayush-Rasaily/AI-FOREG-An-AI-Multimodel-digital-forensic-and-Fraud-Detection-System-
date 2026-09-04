"""Deterministic security policy and chain-validation engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from backend.app.security.models import (
    ComplianceSnapshot,
    ValidationFinding,
    ValidationResult,
)
from backend.app.security.policy import (
    AI_EXECUTION_REQUIRES_CASE_ACCESS,
    CASE_RETENTION_DAYS,
    ENGINE_VERSION,
    EVIDENCE_RETENTION_DAYS,
    EXPORT_REQUIRES_AUDIT_VIEW,
    REPORT_PUBLICATION_REQUIRES_APPROVAL,
    SECURITY_POLICY_VERSION,
    WORKFLOW_APPROVAL_REQUIRED_FOR_ARCHIVE,
    ComplianceStatus,
    PolicyCode,
)


def policy_document() -> dict[str, Any]:
    """Return the immutable governance policy document."""

    return {
        "policy_version": SECURITY_POLICY_VERSION,
        "engine_version": ENGINE_VERSION,
        "case_retention_days": CASE_RETENTION_DAYS,
        "evidence_retention_days": EVIDENCE_RETENTION_DAYS,
        "report_publication_requires_approval": (
            REPORT_PUBLICATION_REQUIRES_APPROVAL
        ),
        "workflow_approval_required_for_archive": (
            WORKFLOW_APPROVAL_REQUIRED_FOR_ARCHIVE
        ),
        "ai_execution_requires_case_access": AI_EXECUTION_REQUIRES_CASE_ACCESS,
        "export_requires_audit_view": EXPORT_REQUIRES_AUDIT_VIEW,
        "policies": [
            {
                "code": PolicyCode.CASE_RETENTION.value,
                "description": (
                    f"Cases retained for {CASE_RETENTION_DAYS} days."
                ),
            },
            {
                "code": PolicyCode.EVIDENCE_RETENTION.value,
                "description": (
                    f"Evidence retained for {EVIDENCE_RETENTION_DAYS} days."
                ),
            },
            {
                "code": PolicyCode.REPORT_PUBLICATION.value,
                "description": "Reports cannot publish without approval.",
            },
            {
                "code": PolicyCode.WORKFLOW_APPROVAL.value,
                "description": (
                    "Archival requires approved/reported workflow status."
                ),
            },
            {
                "code": PolicyCode.AI_EXECUTION.value,
                "description": "AI execution requires case access grant.",
            },
            {
                "code": PolicyCode.EXPORT.value,
                "description": "Exports require audit.view capability.",
            },
        ],
    }


def evaluate_compliance(
    *,
    case_id: UUID | None,
    evidence_count: int,
    custody_event_count: int,
    evidence_with_hash: int,
    audit_event_count: int,
    workflow_status: str | None,
    approved_report_reviews: int,
    published_without_approval: int,
    reports_with_provenance: int,
    report_count: int,
    fusion_with_provenance: int,
    fusion_count: int,
    correlation_with_provenance: int,
    correlation_count: int,
    open_violations: list[str],
) -> ComplianceSnapshot:
    """Build a deterministic compliance snapshot from persisted facts."""

    missing_approvals: list[str] = []
    missing_provenance: list[str] = []

    chain_ok = evidence_count == 0 or custody_event_count >= evidence_count
    integrity_ok = evidence_count == 0 or evidence_with_hash == evidence_count
    audit_ok = audit_event_count > 0 or evidence_count == 0
    workflow_ok = workflow_status is None or workflow_status in {
        "NEW",
        "ACTIVE",
        "UNDER_REVIEW",
        "REQUIRES_CHANGES",
        "APPROVED",
        "REPORTED",
        "ARCHIVED",
        "open",
        "evidence_collection",
        "analysis",
        "review",
        "reporting",
        "closed",
        "archived",
    }
    if (
        WORKFLOW_APPROVAL_REQUIRED_FOR_ARCHIVE
        and workflow_status in {"ARCHIVED", "archived"}
        and approved_report_reviews == 0
        and report_count > 0
    ):
        workflow_ok = False
        missing_approvals.append("workflow_archive_without_report_approval")

    report_ok = published_without_approval == 0
    if report_count > approved_report_reviews and report_count > 0:
        # Draft reports without approval are acceptable; flag only when
        # publication policy is violated (tracked separately).
        pass
    if published_without_approval > 0:
        missing_approvals.append("report_published_without_approval")

    if report_count > reports_with_provenance:
        missing_provenance.append("report_provenance")
    if fusion_count > fusion_with_provenance:
        missing_provenance.append("fusion_provenance")
    if correlation_count > correlation_with_provenance:
        missing_provenance.append("correlation_provenance")

    flags = [
        chain_ok,
        integrity_ok,
        audit_ok,
        workflow_ok,
        report_ok,
        not missing_provenance,
        not open_violations,
    ]
    if all(flags):
        status = ComplianceStatus.COMPLIANT.value
    elif any(flags):
        status = ComplianceStatus.PARTIAL.value
    else:
        status = ComplianceStatus.NON_COMPLIANT.value

    return ComplianceSnapshot(
        status=status,
        chain_of_custody_complete=chain_ok,
        evidence_integrity_ok=integrity_ok,
        audit_complete=audit_ok,
        workflow_compliant=workflow_ok,
        report_approval_compliant=report_ok,
        missing_approvals=sorted(missing_approvals),
        missing_provenance=sorted(set(missing_provenance)),
        policy_violations=sorted(open_violations),
        details={
            "evidence_count": evidence_count,
            "custody_event_count": custody_event_count,
            "audit_event_count": audit_event_count,
            "workflow_status": workflow_status,
            "report_count": report_count,
            "approved_report_reviews": approved_report_reviews,
        },
        generated_at=datetime.now(UTC),
        policy_version=SECURITY_POLICY_VERSION,
        engine_version=ENGINE_VERSION,
        case_id=case_id,
    )


def evaluate_chain_validation(
    *,
    evidence_hash_ok: bool,
    audit_continuity_ok: bool,
    timeline_continuity_ok: bool,
    workflow_continuity_ok: bool,
    report_provenance_ok: bool,
    fusion_provenance_ok: bool,
    correlation_provenance_ok: bool,
    details: dict[str, Any] | None = None,
) -> ValidationResult:
    """Aggregate forensic chain validation checks."""

    meta = details or {}
    findings = [
        ValidationFinding(
            check="evidence_hashes",
            status="PASS" if evidence_hash_ok else "FAIL",
            message=(
                "Evidence hashes present and consistent."
                if evidence_hash_ok
                else "One or more evidence hashes are missing."
            ),
            details=meta.get("evidence", {}),
        ),
        ValidationFinding(
            check="audit_continuity",
            status="PASS" if audit_continuity_ok else "FAIL",
            message=(
                "Audit trail is continuous."
                if audit_continuity_ok
                else "Audit continuity gaps detected."
            ),
            details=meta.get("audit", {}),
        ),
        ValidationFinding(
            check="timeline_continuity",
            status="PASS" if timeline_continuity_ok else "FAIL",
            message=(
                "Timeline continuity validated."
                if timeline_continuity_ok
                else "Timeline continuity could not be confirmed."
            ),
            details=meta.get("timeline", {}),
        ),
        ValidationFinding(
            check="workflow_continuity",
            status="PASS" if workflow_continuity_ok else "FAIL",
            message=(
                "Workflow continuity validated."
                if workflow_continuity_ok
                else "Workflow continuity gaps detected."
            ),
            details=meta.get("workflow", {}),
        ),
        ValidationFinding(
            check="report_provenance",
            status="PASS" if report_provenance_ok else "FAIL",
            message=(
                "Report provenance present."
                if report_provenance_ok
                else "Report provenance missing."
            ),
            details=meta.get("report", {}),
        ),
        ValidationFinding(
            check="fusion_provenance",
            status="PASS" if fusion_provenance_ok else "FAIL",
            message=(
                "Fusion provenance present."
                if fusion_provenance_ok
                else "Fusion provenance missing."
            ),
            details=meta.get("fusion", {}),
        ),
        ValidationFinding(
            check="correlation_provenance",
            status="PASS" if correlation_provenance_ok else "FAIL",
            message=(
                "Correlation provenance present."
                if correlation_provenance_ok
                else "Correlation provenance missing."
            ),
            details=meta.get("correlation", {}),
        ),
    ]
    failed = [item for item in findings if item.status == "FAIL"]
    status = (
        ComplianceStatus.COMPLIANT.value
        if not failed
        else (
            ComplianceStatus.PARTIAL.value
            if len(failed) < len(findings)
            else ComplianceStatus.NON_COMPLIANT.value
        )
    )
    return ValidationResult(
        status=status,
        findings=findings,
        generated_at=datetime.now(UTC),
        policy_version=SECURITY_POLICY_VERSION,
        engine_version=ENGINE_VERSION,
    )
