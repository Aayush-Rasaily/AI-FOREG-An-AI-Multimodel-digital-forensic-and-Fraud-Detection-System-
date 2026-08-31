"""Processing job and artifact domain enumerations."""

from enum import StrEnum


class ProcessingJobType(StrEnum):
    """Supported processing stages in the Phase 4 foundation."""

    INGESTION_INSPECTION = "INGESTION_INSPECTION"
    METADATA_EXTRACTION = "METADATA_EXTRACTION"
    PREVIEW_GENERATION = "PREVIEW_GENERATION"
    FILE_CLASSIFICATION = "FILE_CLASSIFICATION"
    PREPROCESSING = "PREPROCESSING"


class ProcessingJobStatus(StrEnum):
    """Controlled processing job lifecycle states."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ArtifactType(StrEnum):
    """Non-forensic derived artifact categories."""

    PREVIEW = "PREVIEW"
    THUMBNAIL = "THUMBNAIL"
    METADATA = "METADATA"
    CLASSIFICATION = "CLASSIFICATION"
    DERIVATIVE = "DERIVATIVE"


class EvidenceClassification(StrEnum):
    """Safe broad file categories used to select future processors."""

    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    VIDEO = "VIDEO"
    AUDIO = "AUDIO"
    UNKNOWN = "UNKNOWN"
