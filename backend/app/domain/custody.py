"""Chain-of-custody domain enumerations."""

from enum import StrEnum


class CustodyEventType(StrEnum):
    """Controlled event types for evidence custody history."""

    EVIDENCE_INGESTED = "EVIDENCE_INGESTED"
    VIEWED = "VIEWED"
    DOWNLOADED = "DOWNLOADED"
    ANALYSIS_STARTED = "ANALYSIS_STARTED"
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"
    EXPORTED = "EXPORTED"
    DERIVED_ARTIFACT_CREATED = "DERIVED_ARTIFACT_CREATED"


class CustodyActorType(StrEnum):
    """Actor categories that may create custody events."""

    SYSTEM = "SYSTEM"
    USER = "USER"
    SERVICE = "SERVICE"
