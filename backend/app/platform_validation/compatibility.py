"""Module compatibility version checks."""

from __future__ import annotations

import importlib
from typing import Any

from backend.app.platform_validation.models import CheckOutcome, CheckStatus
from backend.app.platform_validation.policy import (
    CHECK_CATALOG,
    COMPATIBILITY_MODULES,
)

_IMPORT_TARGETS: tuple[tuple[str, str, str], ...] = (
    ("evidence_integrity", "backend.app.models.evidence", "Evidence"),
    ("chain_of_custody", "backend.app.models.custody", "ChainOfCustodyEvent"),
    ("ai_modules", "backend.app.models.forensics", "AnalysisRun"),
    ("timeline", "backend.app.models.timeline", "TimelineEventRecord"),
    (
        "correlation",
        "backend.app.models.correlation",
        "EvidenceCorrelationRecord",
    ),
    (
        "knowledge_graph",
        "backend.app.models.knowledge_graph",
        "KnowledgeGraphRun",
    ),
    (
        "investigation_intelligence",
        "backend.app.models.investigation_intelligence",
        "InvestigationIntelligenceRun",
    ),
    ("workflow", "backend.app.models.workflow", "InvestigationWorkflow"),
    ("case_review", "backend.app.models.case_review", "CaseReviewRun"),
    (
        "integrity_monitoring",
        "backend.app.models.integrity",
        "IntegrityMonitorRun",
    ),
    ("analytics", "backend.app.models.analytics", "AnalyticsRun"),
    (
        "report_generation",
        "backend.app.models.forensic_report",
        "ForensicReport",
    ),
    ("audit_logging", "backend.app.models.audit", "AuditEvent"),
)


def collect_compatibility() -> dict[str, Any]:
    """Return engine version map for Phase 9 modules."""

    modules: dict[str, str] = {}
    for name, module_path, attr in COMPATIBILITY_MODULES:
        module = importlib.import_module(module_path)
        modules[name] = str(getattr(module, attr))
    return {"modules": modules, "ai_rerun": False, "forecasting": False}


def check_module_imports() -> list[CheckOutcome]:
    """Verify Phase modules import without executing AI workloads."""

    labels = {item["key"]: item["label"] for item in CHECK_CATALOG}
    categories = {item["key"]: item["category"] for item in CHECK_CATALOG}
    outcomes: list[CheckOutcome] = []
    for key, module_path, symbol in _IMPORT_TARGETS:
        try:
            module = importlib.import_module(module_path)
            getattr(module, symbol)
            status = CheckStatus.PASS
            message = f"{symbol} is importable."
            details: dict[str, Any] = {
                "module": module_path,
                "symbol": symbol,
            }
        except Exception as exc:  # noqa: BLE001 — surface import errors only
            status = CheckStatus.FAIL
            message = f"Failed to import {symbol}: {type(exc).__name__}"
            details = {
                "module": module_path,
                "symbol": symbol,
                "error": str(exc),
            }
        outcomes.append(
            CheckOutcome(
                key=key,
                category=categories.get(key, "platform"),
                label=labels.get(key, key),
                status=status,
                message=message,
                details=details,
            )
        )
    return outcomes
