"""Contracts and context objects for deterministic evidence processors."""

from dataclasses import dataclass, field
from typing import Protocol

from backend.app.domain.processing import (
    ArtifactType,
    EvidenceClassification,
)
from backend.app.models.evidence import Evidence


@dataclass(frozen=True, slots=True)
class InspectionResult:
    """Verified facts about the immutable original."""

    file_exists: bool
    file_size: int
    extension: str
    mime_type: str
    sha256_hash: str
    sha256_verified: bool


@dataclass(frozen=True, slots=True)
class DerivedArtifactPayload:
    """Unpersisted artifact bytes returned by a processor."""

    artifact_type: ArtifactType
    mime_type: str
    content: bytes
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ProcessorContext:
    """Shared facts passed through the ordered processing pipeline."""

    evidence: Evidence
    extension: str
    inspection: InspectionResult | None = None
    classification: EvidenceClassification = EvidenceClassification.UNKNOWN
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProcessorResult:
    """Typed output from one processor stage."""

    inspection: InspectionResult | None = None
    classification: EvidenceClassification | None = None
    metadata: dict[str, object] | None = None
    artifacts: tuple[DerivedArtifactPayload, ...] = ()


class EvidenceProcessor(Protocol):
    """Processor plug-in contract with no forensic algorithms."""

    def can_process(self, context: ProcessorContext) -> bool:
        """Return whether this processor supports the current context."""
        ...

    async def process(self, context: ProcessorContext) -> ProcessorResult:
        """Inspect or derive safe, non-forensic processing output."""
        ...
