"""Granular permission codes and request-to-permission mapping."""

from __future__ import annotations

from enum import StrEnum


class PermissionCode(StrEnum):
    """Stable permission identifiers enforced server-side."""

    CASE_CREATE = "case.create"
    CASE_VIEW = "case.view"
    CASE_EDIT = "case.edit"
    CASE_DELETE = "case.delete"
    EVIDENCE_UPLOAD = "evidence.upload"
    EVIDENCE_VIEW = "evidence.view"
    EVIDENCE_DELETE = "evidence.delete"
    AI_RUN = "ai.run"
    AI_VIEW = "ai.view"
    FUSION_RUN = "fusion.run"
    FUSION_VIEW = "fusion.view"
    TIMELINE_RUN = "timeline.run"
    TIMELINE_VIEW = "timeline.view"
    CORRELATION_RUN = "correlation.run"
    CORRELATION_VIEW = "correlation.view"
    ENTITY_RUN = "entity.run"
    ENTITY_VIEW = "entity.view"
    REPORT_GENERATE = "report.generate"
    REPORT_VIEW = "report.view"
    REPORT_DOWNLOAD = "report.download"
    REPORT_APPROVE = "report.approve"
    AUDIT_VIEW = "audit.view"
    ADMIN_MANAGE_USERS = "admin.manage_users"
    SYSTEM_MONITOR = "system.monitor"
    COMMENT_CREATE = "comment.create"
    COMMENT_VIEW = "comment.view"
    COLLAB_MANAGE_MEMBERS = "collab.manage_members"
    COLLAB_ASSIGN = "collab.assign"
    TASK_MANAGE = "task.manage"
    REVIEW_DECIDE = "review.decide"
    WORKFLOW_TRANSITION = "workflow.transition"
    SECURITY_VIEW = "security.view"
    SECURITY_MANAGE = "security.manage"
    INTEROP_EXPORT = "interop.export"
    INTEROP_IMPORT = "interop.import"
    KNOWLEDGE_GRAPH_RUN = "knowledge_graph.run"
    KNOWLEDGE_GRAPH_VIEW = "knowledge_graph.view"
    INVESTIGATION_INTELLIGENCE_RUN = "investigation_intelligence.run"
    INVESTIGATION_INTELLIGENCE_VIEW = "investigation_intelligence.view"
    DECISION_SUPPORT_RUN = "decision_support.run"
    DECISION_SUPPORT_VIEW = "decision_support.view"
    CASE_REVIEW_RUN = "case_review.run"
    CASE_REVIEW_VIEW = "case_review.view"
    INTEGRITY_RUN = "integrity.run"
    INTEGRITY_VIEW = "integrity.view"
    ANALYTICS_RUN = "analytics.run"
    ANALYTICS_VIEW = "analytics.view"
    PLATFORM_VALIDATION_RUN = "platform_validation.run"
    PLATFORM_VALIDATION_VIEW = "platform_validation.view"


PERMISSION_DESCRIPTIONS: dict[str, str] = {
    PermissionCode.CASE_CREATE: "Create investigation cases.",
    PermissionCode.CASE_VIEW: "View cases and related read models.",
    PermissionCode.CASE_EDIT: "Edit case metadata.",
    PermissionCode.CASE_DELETE: "Delete cases.",
    PermissionCode.EVIDENCE_UPLOAD: "Upload and register evidence.",
    PermissionCode.EVIDENCE_VIEW: "View evidence records.",
    PermissionCode.EVIDENCE_DELETE: "Delete evidence.",
    PermissionCode.AI_RUN: "Run AI analyses.",
    PermissionCode.AI_VIEW: "View AI models and analysis results.",
    PermissionCode.FUSION_RUN: "Run fusion and case intelligence.",
    PermissionCode.FUSION_VIEW: "View fusion results.",
    PermissionCode.TIMELINE_RUN: "Generate investigation timelines.",
    PermissionCode.TIMELINE_VIEW: "View timelines.",
    PermissionCode.CORRELATION_RUN: "Run evidence correlation.",
    PermissionCode.CORRELATION_VIEW: "View correlations.",
    PermissionCode.ENTITY_RUN: "Run entity resolution.",
    PermissionCode.ENTITY_VIEW: "View entity graphs.",
    PermissionCode.REPORT_GENERATE: "Generate investigation reports.",
    PermissionCode.REPORT_VIEW: "View reports.",
    PermissionCode.REPORT_DOWNLOAD: "Download reports.",
    PermissionCode.REPORT_APPROVE: "Approve reports.",
    PermissionCode.AUDIT_VIEW: "View audit trails.",
    PermissionCode.ADMIN_MANAGE_USERS: "Manage users, roles, and sessions.",
    PermissionCode.SYSTEM_MONITOR: "Access system health and diagnostics.",
    PermissionCode.COMMENT_CREATE: "Comment on findings.",
    PermissionCode.COMMENT_VIEW: "View investigation comments.",
    PermissionCode.COLLAB_MANAGE_MEMBERS: "Manage case membership.",
    PermissionCode.COLLAB_ASSIGN: "Assign evidence and collaboration work.",
    PermissionCode.TASK_MANAGE: "Create and update investigation tasks.",
    PermissionCode.REVIEW_DECIDE: "Submit and decide collaboration reviews.",
    PermissionCode.WORKFLOW_TRANSITION: "Advance case workflow stages.",
    PermissionCode.SECURITY_VIEW: "View security governance and compliance.",
    PermissionCode.SECURITY_MANAGE: "Manage case access and security policy.",
    PermissionCode.INTEROP_EXPORT: "Export investigation packages.",
    PermissionCode.INTEROP_IMPORT: "Import and validate investigation packages.",
    PermissionCode.KNOWLEDGE_GRAPH_RUN: "Build investigation knowledge graphs.",
    PermissionCode.KNOWLEDGE_GRAPH_VIEW: "View knowledge graph entities and edges.",
    PermissionCode.INVESTIGATION_INTELLIGENCE_RUN: (
        "Run investigation intelligence hypothesis analysis."
    ),
    PermissionCode.INVESTIGATION_INTELLIGENCE_VIEW: (
        "View investigation hypotheses, gaps, and recommendations."
    ),
    PermissionCode.DECISION_SUPPORT_RUN: (
        "Generate investigator decision-support workflows."
    ),
    PermissionCode.DECISION_SUPPORT_VIEW: (
        "View decision-support tasks, review queues, and decisions."
    ),
    PermissionCode.CASE_REVIEW_RUN: (
        "Generate case review validations and record approvals."
    ),
    PermissionCode.CASE_REVIEW_VIEW: (
        "View case review checklists, approvals, and metrics."
    ),
    PermissionCode.INTEGRITY_RUN: (
        "Run digital evidence integrity monitoring checks."
    ),
    PermissionCode.INTEGRITY_VIEW: (
        "View integrity alerts, drift, and verification history."
    ),
    PermissionCode.ANALYTICS_RUN: (
        "Refresh investigation analytics snapshots."
    ),
    PermissionCode.ANALYTICS_VIEW: (
        "View investigation analytics dashboards and exports."
    ),
    PermissionCode.PLATFORM_VALIDATION_RUN: (
        "Run platform readiness validation checks."
    ),
    PermissionCode.PLATFORM_VALIDATION_VIEW: (
        "View platform validation results and health reports."
    ),
}

PUBLIC_PATHS: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/health/live"),
        ("GET", "/system/liveness"),
        ("GET", "/system/readiness"),
        ("POST", "/auth/login"),
        ("POST", "/auth/refresh"),
    }
)


def strip_api_prefix(path: str, api_prefix: str) -> str:
    """Return the versioned API path without the mount prefix."""

    prefix = api_prefix.rstrip("/")
    if path.startswith(prefix):
        path = path[len(prefix) :]
    normalized = path.rstrip("/") or "/"
    if not normalized.startswith("/"):
        return f"/{normalized}"
    return normalized


def is_public_path(method: str, path: str) -> bool:
    """Return whether the route may be called without authentication."""

    return (method.upper(), path) in PUBLIC_PATHS


def required_permission(method: str, path: str) -> str | None:
    """Return the permission required for a request, or None if auth-only."""

    method = method.upper()
    parts = [segment for segment in path.split("/") if segment]
    if not parts:
        return None
    root = parts[0]
    joined = "/".join(parts)

    if root == "auth":
        return None
    if root in {"users"}:
        return PermissionCode.ADMIN_MANAGE_USERS
    if root in {"roles", "permissions"}:
        return None
    if root == "sessions":
        return None
    if root == "audit":
        return PermissionCode.AUDIT_VIEW
    if root == "monitoring":
        return PermissionCode.SYSTEM_MONITOR
    if root == "security":
        if method == "GET":
            return PermissionCode.SECURITY_VIEW
        return PermissionCode.SECURITY_MANAGE
    if "compliance" in parts:
        return PermissionCode.SECURITY_VIEW
    if (parts and parts[-1] == "access") or ("access" in parts):
        if method == "GET":
            return PermissionCode.SECURITY_VIEW
        return PermissionCode.SECURITY_MANAGE
    if root == "system":
        if len(parts) >= 2 and parts[1] == "info":
            return None
        if len(parts) >= 2 and parts[1] in {"liveness", "readiness"}:
            return None
        return PermissionCode.SYSTEM_MONITOR
    if root == "models":
        if method == "POST":
            return PermissionCode.AI_RUN
        return PermissionCode.AI_VIEW
    if root == "notifications":
        return None
    if root == "comments" or "comments" in parts:
        if method == "POST":
            return PermissionCode.COMMENT_CREATE
        if method in {"PATCH", "DELETE"}:
            return PermissionCode.COMMENT_CREATE
        return PermissionCode.COMMENT_VIEW
    if (
        root.startswith("workflow-")
        or "investigation-workflow" in parts
        or any(part.startswith("workflow-") for part in parts)
    ):
        if root.startswith("workflow-tasks") or any(
            part.startswith("workflow-tasks") for part in parts
        ):
            if method == "GET":
                return PermissionCode.CASE_VIEW
            return PermissionCode.TASK_MANAGE
        if root.startswith("workflow-reviews") or any(
            part.startswith("workflow-reviews") for part in parts
        ):
            return PermissionCode.REVIEW_DECIDE
        if method == "GET":
            return PermissionCode.CASE_VIEW
        return PermissionCode.WORKFLOW_TRANSITION
    if root == "reviews" or "reviews" in parts:
        return PermissionCode.REVIEW_DECIDE
    if root == "tasks" or "tasks" in parts:
        if method == "GET":
            return PermissionCode.CASE_VIEW
        return PermissionCode.TASK_MANAGE
    if "members" in parts:
        if method == "GET":
            return PermissionCode.CASE_VIEW
        return PermissionCode.COLLAB_MANAGE_MEMBERS
    if "assign" in parts or "assignments" in parts:
        if method == "GET":
            return PermissionCode.CASE_VIEW
        return PermissionCode.COLLAB_ASSIGN
    if "activity" in parts:
        return PermissionCode.CASE_VIEW
    if root == "exports" or (root == "cases" and "export" in parts):
        return PermissionCode.INTEROP_EXPORT
    if root == "imports" or (
        root == "cases" and len(parts) >= 2 and parts[1] == "import"
    ):
        return PermissionCode.INTEROP_IMPORT
    if "knowledge-graph" in joined or root == "knowledge-graph":
        if method == "POST":
            return PermissionCode.KNOWLEDGE_GRAPH_RUN
        return PermissionCode.KNOWLEDGE_GRAPH_VIEW
    if (
        "investigation-intelligence" in joined
        or root == "investigation-intelligence"
        or "investigation-preview" in joined
        or "investigation-summary" in parts
        or "hypotheses" in parts
        or "evidence-gaps" in parts
        or (
            "recommendations" in parts
            and root == "cases"
            and "investigation-summaries" not in joined
        )
    ):
        if method == "POST":
            return PermissionCode.INVESTIGATION_INTELLIGENCE_RUN
        return PermissionCode.INVESTIGATION_INTELLIGENCE_VIEW
    if "decision-support" in joined or root == "decision-support":
        if method == "POST" or method == "PATCH":
            return PermissionCode.DECISION_SUPPORT_RUN
        return PermissionCode.DECISION_SUPPORT_VIEW
    if "case-review" in joined or root == "case-review":
        if method == "POST" or method == "PATCH":
            return PermissionCode.CASE_REVIEW_RUN
        return PermissionCode.CASE_REVIEW_VIEW
    if root == "analytics" or "analytics" in parts:
        if method == "POST":
            return PermissionCode.ANALYTICS_RUN
        return PermissionCode.ANALYTICS_VIEW
    if root == "platform" or "platform" in parts:
        if method == "POST":
            return PermissionCode.PLATFORM_VALIDATION_RUN
        return PermissionCode.PLATFORM_VALIDATION_VIEW
    if (
        "integrity-check" in joined
        or root == "integrity"
        or (root == "cases" and "integrity" in parts)
    ):
        if method == "POST":
            return PermissionCode.INTEGRITY_RUN
        return PermissionCode.INTEGRITY_VIEW
    if "workflow" in parts:
        if method == "GET":
            return PermissionCode.CASE_VIEW
        return PermissionCode.WORKFLOW_TRANSITION
    if "download" in parts:
        return PermissionCode.REPORT_DOWNLOAD
    if "reports" in parts:
        if method == "POST":
            return PermissionCode.REPORT_GENERATE
        return PermissionCode.REPORT_VIEW
    if "investigation-summaries" in parts or root == "investigation-summaries":
        if method == "POST":
            return PermissionCode.REPORT_GENERATE
        return PermissionCode.REPORT_VIEW
    if any(
        token in joined for token in ("fusion", "case-intelligence", "intelligence")
    ):
        if method == "POST":
            return PermissionCode.FUSION_RUN
        return PermissionCode.FUSION_VIEW
    if "timeline" in joined:
        if method == "POST":
            return PermissionCode.TIMELINE_RUN
        return PermissionCode.TIMELINE_VIEW
    if "correlation" in joined:
        if method == "POST":
            return PermissionCode.CORRELATION_RUN
        return PermissionCode.CORRELATION_VIEW
    if "entit" in joined:
        if method == "POST":
            return PermissionCode.ENTITY_RUN
        return PermissionCode.ENTITY_VIEW
    if any(
        token in joined
        for token in (
            "image-ai",
            "document-ai",
            "signature",
            "video-ai",
            "audio-ai",
            "comparison",
            "forensic",
            "inference",
        )
    ):
        if method == "POST":
            return PermissionCode.AI_RUN
        return PermissionCode.AI_VIEW
    if "extraction" in joined or "processing" in joined:
        if method == "POST":
            return PermissionCode.EVIDENCE_UPLOAD
        return PermissionCode.EVIDENCE_VIEW
    if "evidence" in parts:
        if method == "POST":
            return PermissionCode.EVIDENCE_UPLOAD
        if method == "DELETE":
            return PermissionCode.EVIDENCE_DELETE
        return PermissionCode.EVIDENCE_VIEW
    if root == "cases":
        if method == "POST" and len(parts) == 1:
            return PermissionCode.CASE_CREATE
        if method == "PATCH":
            return PermissionCode.CASE_EDIT
        if method == "DELETE":
            return PermissionCode.CASE_DELETE
        return PermissionCode.CASE_VIEW
    if method == "POST":
        return PermissionCode.AI_RUN
    return PermissionCode.CASE_VIEW
