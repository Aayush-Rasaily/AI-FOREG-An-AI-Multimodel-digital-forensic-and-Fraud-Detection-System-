"""Deterministic built-in roles for Phase 8A."""

from __future__ import annotations

from backend.app.auth.permissions import PermissionCode

ROLE_ADMINISTRATOR = "Administrator"
ROLE_INVESTIGATOR = "Investigator"
ROLE_ANALYST = "Analyst"
ROLE_REVIEWER = "Reviewer"
ROLE_VIEWER = "Viewer"

BUILTIN_ROLES: tuple[str, ...] = (
    ROLE_ADMINISTRATOR,
    ROLE_INVESTIGATOR,
    ROLE_ANALYST,
    ROLE_REVIEWER,
    ROLE_VIEWER,
)

ROLE_DESCRIPTIONS: dict[str, str] = {
    ROLE_ADMINISTRATOR: "Full platform access including user administration.",
    ROLE_INVESTIGATOR: (
        "Manage cases, upload evidence, run analyses, and generate reports."
    ),
    ROLE_ANALYST: "Review findings, perform AI analyses, and comment.",
    ROLE_REVIEWER: "Read-only access with report approval.",
    ROLE_VIEWER: "Read-only evidence and case visibility.",
}

_READ = frozenset(
    {
        PermissionCode.CASE_VIEW.value,
        PermissionCode.EVIDENCE_VIEW.value,
        PermissionCode.AI_VIEW.value,
        PermissionCode.FUSION_VIEW.value,
        PermissionCode.TIMELINE_VIEW.value,
        PermissionCode.CORRELATION_VIEW.value,
        PermissionCode.ENTITY_VIEW.value,
        PermissionCode.REPORT_VIEW.value,
    }
)

ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    ROLE_ADMINISTRATOR: frozenset(item.value for item in PermissionCode),
    ROLE_INVESTIGATOR: frozenset(
        {
            PermissionCode.CASE_CREATE.value,
            PermissionCode.CASE_VIEW.value,
            PermissionCode.CASE_EDIT.value,
            PermissionCode.CASE_DELETE.value,
            PermissionCode.EVIDENCE_UPLOAD.value,
            PermissionCode.EVIDENCE_VIEW.value,
            PermissionCode.EVIDENCE_DELETE.value,
            PermissionCode.AI_RUN.value,
            PermissionCode.AI_VIEW.value,
            PermissionCode.FUSION_RUN.value,
            PermissionCode.FUSION_VIEW.value,
            PermissionCode.TIMELINE_RUN.value,
            PermissionCode.TIMELINE_VIEW.value,
            PermissionCode.CORRELATION_RUN.value,
            PermissionCode.CORRELATION_VIEW.value,
            PermissionCode.ENTITY_RUN.value,
            PermissionCode.ENTITY_VIEW.value,
            PermissionCode.REPORT_GENERATE.value,
            PermissionCode.REPORT_VIEW.value,
            PermissionCode.REPORT_DOWNLOAD.value,
            PermissionCode.AUDIT_VIEW.value,
            PermissionCode.COMMENT_CREATE.value,
            PermissionCode.COMMENT_VIEW.value,
            PermissionCode.COLLAB_MANAGE_MEMBERS.value,
            PermissionCode.COLLAB_ASSIGN.value,
            PermissionCode.TASK_MANAGE.value,
            PermissionCode.REVIEW_DECIDE.value,
            PermissionCode.WORKFLOW_TRANSITION.value,
            PermissionCode.SECURITY_VIEW.value,
            PermissionCode.INTEROP_EXPORT.value,
            PermissionCode.INTEROP_IMPORT.value,
            PermissionCode.KNOWLEDGE_GRAPH_RUN.value,
            PermissionCode.KNOWLEDGE_GRAPH_VIEW.value,
            PermissionCode.INVESTIGATION_INTELLIGENCE_RUN.value,
            PermissionCode.INVESTIGATION_INTELLIGENCE_VIEW.value,
        }
    ),
    ROLE_ANALYST: _READ
    | frozenset(
        {
            PermissionCode.AI_RUN.value,
            PermissionCode.FUSION_RUN.value,
            PermissionCode.COMMENT_CREATE.value,
            PermissionCode.COMMENT_VIEW.value,
            PermissionCode.TASK_MANAGE.value,
            PermissionCode.COLLAB_ASSIGN.value,
            PermissionCode.SECURITY_VIEW.value,
            PermissionCode.INTEROP_EXPORT.value,
            PermissionCode.KNOWLEDGE_GRAPH_RUN.value,
            PermissionCode.KNOWLEDGE_GRAPH_VIEW.value,
            PermissionCode.INVESTIGATION_INTELLIGENCE_RUN.value,
            PermissionCode.INVESTIGATION_INTELLIGENCE_VIEW.value,
        }
    ),
    ROLE_REVIEWER: _READ
    | frozenset(
        {
            PermissionCode.REPORT_DOWNLOAD.value,
            PermissionCode.REPORT_APPROVE.value,
            PermissionCode.AUDIT_VIEW.value,
            PermissionCode.COMMENT_VIEW.value,
            PermissionCode.REVIEW_DECIDE.value,
            PermissionCode.SECURITY_VIEW.value,
            PermissionCode.INTEROP_EXPORT.value,
            PermissionCode.KNOWLEDGE_GRAPH_VIEW.value,
            PermissionCode.INVESTIGATION_INTELLIGENCE_VIEW.value,
        }
    ),
    ROLE_VIEWER: frozenset(
        {
            PermissionCode.CASE_VIEW.value,
            PermissionCode.EVIDENCE_VIEW.value,
            PermissionCode.REPORT_VIEW.value,
            PermissionCode.COMMENT_VIEW.value,
        }
    ),
}
