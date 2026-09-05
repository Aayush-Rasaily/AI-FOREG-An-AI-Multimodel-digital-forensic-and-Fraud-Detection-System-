"""Deterministic validation scoring for case review."""

from __future__ import annotations

from backend.app.case_review.models import ChecklistItemDraft, ValidationMetrics


def compute_metrics(
    checklist: list[ChecklistItemDraft],
    *,
    evidence_total: int,
    evidence_with_hash: int,
    approvals_done: int,
    approvals_required: int,
) -> ValidationMetrics:
    total = len(checklist) or 1
    passed = sum(
        1
        for item in checklist
        if item.status.value in {"PASS", "NA"}
        or item.suggested_status.value in {"PASS", "NA"}
    )
    reviewed = sum(
        1
        for item in checklist
        if item.status.value != "PENDING" or item.suggested_status.value != "PENDING"
    )
    outstanding = sum(1 for item in checklist if item.outstanding)
    blocking = sum(1 for item in checklist if item.blocking)
    evidence_cov = (
        round(evidence_with_hash / evidence_total, 4) if evidence_total else 0.0
    )
    approval_pct = (
        round(approvals_done / approvals_required, 4) if approvals_required else 0.0
    )
    return ValidationMetrics(
        validation_pct=round(passed / total, 4),
        evidence_coverage_pct=evidence_cov,
        review_completion_pct=round(reviewed / total, 4),
        approval_completion_pct=min(1.0, approval_pct),
        outstanding_issues=outstanding,
        blocking_issues=blocking,
    )
