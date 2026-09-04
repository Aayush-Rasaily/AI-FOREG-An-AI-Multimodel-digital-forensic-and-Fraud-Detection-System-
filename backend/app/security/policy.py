"""Security governance policy constants and enumerations."""

from __future__ import annotations

from enum import StrEnum

ENGINE_VERSION = "8f.1.0"
SECURITY_POLICY_VERSION = "1.0"
POLICY_VERSION = SECURITY_POLICY_VERSION

# Retention defaults (days) — deterministic governance thresholds.
CASE_RETENTION_DAYS = 2555  # ~7 years
EVIDENCE_RETENTION_DAYS = 2555
REPORT_PUBLICATION_REQUIRES_APPROVAL = True
WORKFLOW_APPROVAL_REQUIRED_FOR_ARCHIVE = True
AI_EXECUTION_REQUIRES_CASE_ACCESS = True
EXPORT_REQUIRES_AUDIT_VIEW = True


class GovernanceRole(StrEnum):
    ADMIN = "ADMIN"
    FORENSIC_ADMIN = "FORENSIC_ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    FORENSIC_ANALYST = "FORENSIC_ANALYST"
    REVIEWER = "REVIEWER"
    AUDITOR = "AUDITOR"
    READ_ONLY = "READ_ONLY"


class AccessLevel(StrEnum):
    OWNER = "Owner"
    ASSIGNED_INVESTIGATOR = "Assigned investigators"
    READ_ONLY_REVIEWER = "Read-only reviewers"
    AUDITOR = "Auditors"
    ADMINISTRATOR = "Administrators"


class PolicyCode(StrEnum):
    CASE_RETENTION = "case_retention"
    EVIDENCE_RETENTION = "evidence_retention"
    REPORT_PUBLICATION = "report_publication"
    WORKFLOW_APPROVAL = "workflow_approval"
    AI_EXECUTION = "ai_execution"
    EXPORT = "export"
    CASE_ACCESS = "case_access"
    EVIDENCE_SECURITY = "evidence_security"
    AUDIT_IMMUTABILITY = "audit_immutability"


class ViolationSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceStatus(StrEnum):
    COMPLIANT = "COMPLIANT"
    PARTIAL = "PARTIAL"
    NON_COMPLIANT = "NON_COMPLIANT"


# Deterministic permission matrix keyed by governance role.
# Codes align with platform PermissionCode values where applicable.
GOVERNANCE_PERMISSION_MATRIX: dict[GovernanceRole, frozenset[str]] = {
    GovernanceRole.ADMIN: frozenset(
        {
            "case.create",
            "case.view",
            "case.edit",
            "case.delete",
            "evidence.upload",
            "evidence.view",
            "evidence.delete",
            "evidence.export",
            "evidence.modify",
            "evidence.review",
            "evidence.approve",
            "ai.run",
            "ai.view",
            "fusion.run",
            "fusion.view",
            "correlation.run",
            "correlation.view",
            "timeline.run",
            "timeline.view",
            "report.generate",
            "report.view",
            "report.download",
            "report.approve",
            "workflow.transition",
            "workflow.approve",
            "monitoring.view",
            "admin.manage_users",
            "security.view",
            "security.manage",
            "audit.view",
        }
    ),
    GovernanceRole.FORENSIC_ADMIN: frozenset(
        {
            "case.create",
            "case.view",
            "case.edit",
            "evidence.upload",
            "evidence.view",
            "evidence.delete",
            "evidence.export",
            "evidence.modify",
            "evidence.review",
            "evidence.approve",
            "ai.run",
            "ai.view",
            "fusion.run",
            "fusion.view",
            "correlation.run",
            "correlation.view",
            "timeline.run",
            "timeline.view",
            "report.generate",
            "report.view",
            "report.download",
            "report.approve",
            "workflow.transition",
            "workflow.approve",
            "monitoring.view",
            "security.view",
            "security.manage",
            "audit.view",
        }
    ),
    GovernanceRole.INVESTIGATOR: frozenset(
        {
            "case.create",
            "case.view",
            "case.edit",
            "evidence.upload",
            "evidence.view",
            "evidence.export",
            "evidence.modify",
            "evidence.review",
            "ai.run",
            "ai.view",
            "fusion.run",
            "fusion.view",
            "correlation.run",
            "correlation.view",
            "timeline.run",
            "timeline.view",
            "report.generate",
            "report.view",
            "report.download",
            "workflow.transition",
            "security.view",
            "audit.view",
        }
    ),
    GovernanceRole.FORENSIC_ANALYST: frozenset(
        {
            "case.view",
            "evidence.view",
            "evidence.review",
            "ai.run",
            "ai.view",
            "fusion.run",
            "fusion.view",
            "correlation.run",
            "correlation.view",
            "timeline.run",
            "timeline.view",
            "report.view",
            "security.view",
        }
    ),
    GovernanceRole.REVIEWER: frozenset(
        {
            "case.view",
            "evidence.view",
            "evidence.review",
            "evidence.approve",
            "ai.view",
            "fusion.view",
            "correlation.view",
            "timeline.view",
            "report.view",
            "report.download",
            "report.approve",
            "workflow.approve",
            "security.view",
            "audit.view",
        }
    ),
    GovernanceRole.AUDITOR: frozenset(
        {
            "case.view",
            "evidence.view",
            "ai.view",
            "fusion.view",
            "correlation.view",
            "timeline.view",
            "report.view",
            "monitoring.view",
            "security.view",
            "audit.view",
        }
    ),
    GovernanceRole.READ_ONLY: frozenset(
        {
            "case.view",
            "evidence.view",
            "ai.view",
            "fusion.view",
            "correlation.view",
            "timeline.view",
            "report.view",
            "security.view",
        }
    ),
}

PERMISSION_CATALOG: tuple[tuple[str, str, str, str], ...] = (
    ("case.create", "Cases", "create", "Create investigation cases"),
    ("case.view", "Cases", "view", "View cases"),
    ("case.edit", "Cases", "edit", "Edit case metadata"),
    ("case.delete", "Cases", "delete", "Delete cases"),
    ("evidence.upload", "Evidence", "upload", "Upload evidence"),
    ("evidence.view", "Evidence", "view", "View evidence"),
    ("evidence.delete", "Evidence", "delete", "Delete evidence"),
    ("evidence.export", "Evidence", "export", "Export evidence"),
    ("evidence.modify", "Evidence", "modify", "Modify evidence metadata"),
    ("evidence.review", "Evidence", "review", "Review evidence"),
    ("evidence.approve", "Evidence", "approve", "Approve evidence"),
    ("ai.run", "AI Analysis", "run", "Execute AI analysis"),
    ("ai.view", "AI Analysis", "view", "View AI results"),
    ("fusion.run", "Fusion", "run", "Run fusion"),
    ("fusion.view", "Fusion", "view", "View fusion"),
    ("correlation.run", "Correlation", "run", "Run correlation"),
    ("correlation.view", "Correlation", "view", "View correlation"),
    ("timeline.run", "Timeline", "run", "Generate timeline"),
    ("timeline.view", "Timeline", "view", "View timeline"),
    ("report.generate", "Reports", "generate", "Generate reports"),
    ("report.view", "Reports", "view", "View reports"),
    ("report.download", "Reports", "download", "Download reports"),
    ("report.approve", "Reports", "approve", "Approve reports"),
    ("workflow.transition", "Workflow", "transition", "Advance workflow"),
    ("workflow.approve", "Workflow", "approve", "Approve workflow steps"),
    ("monitoring.view", "Monitoring", "view", "View monitoring"),
    ("admin.manage_users", "Administration", "manage", "Manage users"),
    ("security.view", "Administration", "view", "View security governance"),
    ("security.manage", "Administration", "manage", "Manage security access"),
    ("audit.view", "Administration", "audit", "View audit trails"),
)

ROLE_DESCRIPTIONS: dict[GovernanceRole, str] = {
    GovernanceRole.ADMIN: "Full enterprise administration.",
    GovernanceRole.FORENSIC_ADMIN: "Forensic platform administration.",
    GovernanceRole.INVESTIGATOR: "Lead case investigation work.",
    GovernanceRole.FORENSIC_ANALYST: "Run forensic and AI analyses.",
    GovernanceRole.REVIEWER: "Review and approve evidence/reports.",
    GovernanceRole.AUDITOR: "Read-only compliance and audit access.",
    GovernanceRole.READ_ONLY: "Limited read-only visibility.",
}
