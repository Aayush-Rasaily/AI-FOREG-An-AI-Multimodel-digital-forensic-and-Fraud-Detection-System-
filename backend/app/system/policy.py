"""System monitoring version constants and policy."""

ENGINE_VERSION = "1.0"
POLICY_VERSION = "1.0"

DIAGNOSTIC_CHECKS: tuple[str, ...] = (
    "configuration",
    "database_connectivity",
    "storage_verification",
    "migration_verification",
    "ai_model_availability",
    "queue_health",
    "cache_verification",
    "dependency_checks",
)

JOB_CATEGORIES: tuple[str, ...] = (
    "extraction",
    "ai",
    "fusion",
    "timeline",
    "correlation",
    "entity_resolution",
    "reports",
    "processing",
)
