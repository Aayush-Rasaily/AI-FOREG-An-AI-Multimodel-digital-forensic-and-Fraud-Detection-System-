"""Evidence domain enumerations."""

from enum import StrEnum


class EvidenceStatus(StrEnum):
    """Controlled lifecycle states for an evidence item."""

    REGISTERED = "REGISTERED"
    READY_FOR_ANALYSIS = "READY_FOR_ANALYSIS"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"
    QUARANTINED = "QUARANTINED"
