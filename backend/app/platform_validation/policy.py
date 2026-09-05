"""Deterministic policy for Phase 9H platform validation."""

from __future__ import annotations

PV_ENGINE_VERSION = "9h.1.0"
PV_POLICY_VERSION = "1.0"

# Severity weights for readiness scoring (deterministic).
SEVERITY_WEIGHTS: dict[str, float] = {
    "PASS": 1.0,
    "WARN": 0.5,
    "FAIL": 0.0,
}

# Ordered catalog of validation checks (no AI re-runs; read-only).
CHECK_CATALOG: tuple[dict[str, str], ...] = (
    {
        "key": "migrations",
        "category": "migrations",
        "label": "Database migrations",
    },
    {
        "key": "orm_consistency",
        "category": "orm",
        "label": "ORM consistency",
    },
    {
        "key": "api_compatibility",
        "category": "api",
        "label": "API compatibility",
    },
    {
        "key": "openapi_generation",
        "category": "api",
        "label": "OpenAPI generation",
    },
    {
        "key": "evidence_integrity",
        "category": "evidence",
        "label": "Evidence integrity tables",
    },
    {
        "key": "chain_of_custody",
        "category": "evidence",
        "label": "Chain of custody",
    },
    {
        "key": "ai_modules",
        "category": "ai",
        "label": "AI modules",
    },
    {
        "key": "timeline",
        "category": "investigation",
        "label": "Timeline",
    },
    {
        "key": "correlation",
        "category": "investigation",
        "label": "Correlation",
    },
    {
        "key": "knowledge_graph",
        "category": "investigation",
        "label": "Knowledge Graph",
    },
    {
        "key": "investigation_intelligence",
        "category": "investigation",
        "label": "Investigation Intelligence",
    },
    {
        "key": "workflow",
        "category": "workflow",
        "label": "Workflow",
    },
    {
        "key": "case_review",
        "category": "workflow",
        "label": "Case Review",
    },
    {
        "key": "integrity_monitoring",
        "category": "integrity",
        "label": "Integrity Monitoring",
    },
    {
        "key": "analytics",
        "category": "analytics",
        "label": "Analytics",
    },
    {
        "key": "report_generation",
        "category": "reports",
        "label": "Report generation",
    },
    {
        "key": "audit_logging",
        "category": "audit",
        "label": "Audit logging",
    },
    {
        "key": "configuration",
        "category": "platform",
        "label": "Configuration",
    },
    {
        "key": "storage_accessibility",
        "category": "platform",
        "label": "Storage accessibility",
    },
)

# Required ORM / DB table presence for module consistency.
REQUIRED_TABLES: dict[str, tuple[str, ...]] = {
    "evidence_integrity": ("evidence", "artifacts"),
    "chain_of_custody": ("chain_of_custody_events",),
    "ai_modules": (
        "ai_model_records",
        "analysis_runs",
        "image_analysis_runs",
        "document_analysis_runs",
        "video_analysis_runs",
        "audio_analysis_runs",
    ),
    "timeline": ("timeline_events", "investigation_timelines"),
    "correlation": ("evidence_correlations", "correlation_analysis_runs"),
    "knowledge_graph": ("graph_entities", "knowledge_graph_runs"),
    "investigation_intelligence": ("investigation_intelligence_runs",),
    "workflow": (
        "case_workflow_states",
        "investigation_workflows",
        "decision_support_runs",
    ),
    "case_review": ("case_review_runs",),
    "integrity_monitoring": (
        "integrity_monitor_runs",
        "integrity_checks",
        "integrity_alerts",
    ),
    "analytics": (
        "analytics_runs",
        "analytics_snapshots",
        "analytics_metrics",
    ),
    "report_generation": ("forensic_reports",),
    "audit_logging": ("audit_events",),
    "orm_consistency": (
        "cases",
        "evidence",
        "users",
        "platform_validation_runs",
        "platform_validation_results",
        "platform_validation_issues",
    ),
}

# Required API path suffixes under /api/v1 (compatibility contract).
REQUIRED_API_PATHS: tuple[str, ...] = (
    "/health",
    "/cases",
    "/analytics",
    "/analytics/refresh",
    "/platform/validate",
    "/platform/validation",
    "/platform/validation/latest",
    "/platform/readiness",
    "/platform/health/report",
)

COMPATIBILITY_MODULES: tuple[tuple[str, str, str], ...] = (
    ("integrity", "backend.app.integrity.policy", "IM_ENGINE_VERSION"),
    ("analytics", "backend.app.analytics.policy", "AN_ENGINE_VERSION"),
    (
        "platform_validation",
        "backend.app.platform_validation.policy",
        "PV_ENGINE_VERSION",
    ),
)
