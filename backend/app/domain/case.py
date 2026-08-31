"""Case domain enumerations."""

from enum import StrEnum


class CaseStatus(StrEnum):
    """Controlled lifecycle states for an investigation case."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CasePriority(StrEnum):
    """Controlled priority levels for an investigation case."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
