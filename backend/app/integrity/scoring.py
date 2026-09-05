"""Integrity scoring helpers."""

from __future__ import annotations

from backend.app.integrity.models import (
    AlertDraft,
    CheckDraft,
    CheckStatus,
    DriftDraft,
    IntegrityMetrics,
)


def compute_metrics(
    checks: list[CheckDraft],
    alerts: list[AlertDraft],
    drifts: list[DriftDraft],
    *,
    evidence_total: int,
    evidence_checked: int,
) -> IntegrityMetrics:
    total = len(checks) or 1
    passed = sum(1 for item in checks if item.status == CheckStatus.PASS)
    failed = sum(1 for item in checks if item.status == CheckStatus.FAIL)
    warned = sum(1 for item in checks if item.status == CheckStatus.WARN)
    coverage = round(evidence_checked / evidence_total, 4) if evidence_total else 0.0
    # Score: passed share penalized by critical/high alerts
    base = passed / total
    critical = sum(1 for item in alerts if item.severity.value == "CRITICAL")
    high = sum(1 for item in alerts if item.severity.value == "HIGH")
    penalty = min(0.5, critical * 0.15 + high * 0.08)
    score = round(max(0.0, base - penalty), 4)
    return IntegrityMetrics(
        checks_total=len(checks),
        checks_passed=passed,
        checks_failed=failed,
        checks_warned=warned,
        alert_count=len(alerts),
        drift_count=len(drifts),
        evidence_coverage_pct=coverage,
        integrity_score=score,
        critical_alerts=critical,
        high_alerts=high,
    )
