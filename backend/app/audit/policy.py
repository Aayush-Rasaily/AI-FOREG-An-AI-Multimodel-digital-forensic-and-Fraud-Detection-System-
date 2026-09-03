"""Audit framework version constants."""

ENGINE_VERSION = "1.0"
POLICY_VERSION = "1.0"

SUPPORTED_OPERATIONS: tuple[str, ...] = (
    "case.created",
    "evidence.uploaded",
    "evidence.deleted",
    "metadata.extraction",
    "ocr.execution",
    "pattern.extraction",
    "ai.analysis",
    "fusion.analysis",
    "timeline.generation",
    "correlation.generation",
    "entity.generation",
    "report.generation",
    "user.download",
    "user.export",
    "user.login",
    "user.logout",
    "permission.changed",
    "configuration.updated",
    "migration.executed",
)

COMPLIANCE_STANDARDS: tuple[str, ...] = (
    "ISO 27037",
    "NIST SP 800-86",
)
