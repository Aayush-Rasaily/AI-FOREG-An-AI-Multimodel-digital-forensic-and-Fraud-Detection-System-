"""Compliance summary helpers."""

from __future__ import annotations

from typing import Any

from backend.app.security.models import ComplianceSnapshot


def snapshot_to_dict(snapshot: ComplianceSnapshot) -> dict[str, Any]:
    """Serialize a compliance snapshot for persistence and API responses."""

    return {
        "status": snapshot.status,
        "case_id": str(snapshot.case_id) if snapshot.case_id else None,
        "chain_of_custody_complete": snapshot.chain_of_custody_complete,
        "evidence_integrity_ok": snapshot.evidence_integrity_ok,
        "audit_complete": snapshot.audit_complete,
        "workflow_compliant": snapshot.workflow_compliant,
        "report_approval_compliant": snapshot.report_approval_compliant,
        "missing_approvals": list(snapshot.missing_approvals),
        "missing_provenance": list(snapshot.missing_provenance),
        "policy_violations": list(snapshot.policy_violations),
        "details": dict(snapshot.details),
        "generated_at": snapshot.generated_at.isoformat(),
        "policy_version": snapshot.policy_version,
        "engine_version": snapshot.engine_version,
    }
