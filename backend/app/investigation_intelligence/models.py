"""In-memory domain models for Phase 9C investigation intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class RunStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class HypothesisStatus(StrEnum):
    OPEN = "OPEN"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    RESOLVED = "RESOLVED"


class PriorityLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class GapSeverity(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class HypothesisType(StrEnum):
    LIKELY_DOCUMENT_TAMPERING = "LIKELY_DOCUMENT_TAMPERING"
    POSSIBLE_IDENTITY_FRAUD = "POSSIBLE_IDENTITY_FRAUD"
    POTENTIAL_DEEPFAKE_MEDIA = "POTENTIAL_DEEPFAKE_MEDIA"
    SIGNATURE_INCONSISTENCY = "SIGNATURE_INCONSISTENCY"
    METADATA_MANIPULATION = "METADATA_MANIPULATION"
    CROSS_EVIDENCE_CORROBORATION = "CROSS_EVIDENCE_CORROBORATION"
    TIMELINE_CONFLICT = "TIMELINE_CONFLICT"
    SHARED_DEVICE_USAGE = "SHARED_DEVICE_USAGE"
    SHARED_IDENTITY_INDICATORS = "SHARED_IDENTITY_INDICATORS"
    MULTIPLE_EVIDENCE_SAME_EVENT = "MULTIPLE_EVIDENCE_SAME_EVENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CHAIN_OF_CUSTODY_CONCERN = "CHAIN_OF_CUSTODY_CONCERN"
    MISSING_VERIFICATION = "MISSING_VERIFICATION"
    INVESTIGATION_COMPLETE = "INVESTIGATION_COMPLETE"


class GapType(StrEnum):
    MISSING_ORIGINAL_FILE = "MISSING_ORIGINAL_FILE"
    MISSING_METADATA = "MISSING_METADATA"
    MISSING_TIMESTAMP = "MISSING_TIMESTAMP"
    MISSING_COMPARISON_TARGET = "MISSING_COMPARISON_TARGET"
    MISSING_SIGNATURE_VERIFICATION = "MISSING_SIGNATURE_VERIFICATION"
    MISSING_OCR = "MISSING_OCR"
    MISSING_AI_ANALYSIS = "MISSING_AI_ANALYSIS"
    MISSING_CORROBORATING_EVIDENCE = "MISSING_CORROBORATING_EVIDENCE"
    MISSING_TIMELINE_EVENT = "MISSING_TIMELINE_EVENT"
    MISSING_GRAPH_RELATIONSHIP = "MISSING_GRAPH_RELATIONSHIP"
    MISSING_CHAIN_OF_CUSTODY = "MISSING_CHAIN_OF_CUSTODY"


class RecommendationCode(StrEnum):
    RUN_IMAGE_COMPARISON = "RUN_IMAGE_COMPARISON"
    ACQUIRE_ORIGINAL_MEDIA = "ACQUIRE_ORIGINAL_MEDIA"
    VERIFY_DIGITAL_SIGNATURE = "VERIFY_DIGITAL_SIGNATURE"
    OBTAIN_DEVICE_METADATA = "OBTAIN_DEVICE_METADATA"
    COMPARE_KNOWN_EVIDENCE = "COMPARE_KNOWN_EVIDENCE"
    REVIEW_CONFLICTING_AI = "REVIEW_CONFLICTING_AI"
    INVESTIGATE_TIMELINE_INCONSISTENCY = "INVESTIGATE_TIMELINE_INCONSISTENCY"
    VERIFY_CHAIN_OF_CUSTODY = "VERIFY_CHAIN_OF_CUSTODY"
    COLLECT_CORROBORATING_EVIDENCE = "COLLECT_CORROBORATING_EVIDENCE"
    REVIEW_UNRESOLVED_RELATIONSHIPS = "REVIEW_UNRESOLVED_RELATIONSHIPS"
    RUN_OCR = "RUN_OCR"
    RUN_AI_ANALYSIS = "RUN_AI_ANALYSIS"
    BUILD_KNOWLEDGE_GRAPH = "BUILD_KNOWLEDGE_GRAPH"
    GENERATE_TIMELINE = "GENERATE_TIMELINE"


# Fixed human-readable templates (never LLM-generated).
RECOMMENDATION_TEXT: dict[str, str] = {
    RecommendationCode.RUN_IMAGE_COMPARISON: (
        "Run image comparison against known reference media."
    ),
    RecommendationCode.ACQUIRE_ORIGINAL_MEDIA: (
        "Acquire original media for the affected evidence items."
    ),
    RecommendationCode.VERIFY_DIGITAL_SIGNATURE: (
        "Verify digital signature on the affected documents."
    ),
    RecommendationCode.OBTAIN_DEVICE_METADATA: (
        "Obtain device and capture metadata for the evidence."
    ),
    RecommendationCode.COMPARE_KNOWN_EVIDENCE: (
        "Compare against other known evidence in the case."
    ),
    RecommendationCode.REVIEW_CONFLICTING_AI: (
        "Review conflicting AI findings across modalities."
    ),
    RecommendationCode.INVESTIGATE_TIMELINE_INCONSISTENCY: (
        "Investigate timeline inconsistency between events."
    ),
    RecommendationCode.VERIFY_CHAIN_OF_CUSTODY: (
        "Verify chain of custody continuity for affected evidence."
    ),
    RecommendationCode.COLLECT_CORROBORATING_EVIDENCE: (
        "Collect additional corroborating evidence."
    ),
    RecommendationCode.REVIEW_UNRESOLVED_RELATIONSHIPS: (
        "Review unresolved knowledge-graph relationships."
    ),
    RecommendationCode.RUN_OCR: "Run OCR extraction on document evidence.",
    RecommendationCode.RUN_AI_ANALYSIS: (
        "Run pending AI analysis for the affected evidence."
    ),
    RecommendationCode.BUILD_KNOWLEDGE_GRAPH: (
        "Build the investigation knowledge graph for relationship coverage."
    ),
    RecommendationCode.GENERATE_TIMELINE: (
        "Generate an investigation timeline for temporal coverage."
    ),
}

HYPOTHESIS_EXPLANATIONS: dict[str, str] = {
    HypothesisType.LIKELY_DOCUMENT_TAMPERING: (
        "Document AI / fusion outputs indicate possible document tampering."
    ),
    HypothesisType.POSSIBLE_IDENTITY_FRAUD: (
        "Shared identity indicators across evidence suggest possible identity fraud."
    ),
    HypothesisType.POTENTIAL_DEEPFAKE_MEDIA: (
        "Media AI findings indicate potential synthetic or deepfake content."
    ),
    HypothesisType.SIGNATURE_INCONSISTENCY: (
        "Signature verification results are inconsistent or failed."
    ),
    HypothesisType.METADATA_MANIPULATION: (
        "Evidence metadata appears incomplete or inconsistent with capture norms."
    ),
    HypothesisType.CROSS_EVIDENCE_CORROBORATION: (
        "Multiple evidence items corroborate the same investigative signal."
    ),
    HypothesisType.TIMELINE_CONFLICT: (
        "Timeline reconstruction reports conflicting temporal events."
    ),
    HypothesisType.SHARED_DEVICE_USAGE: (
        "Knowledge graph links indicate shared device usage across evidence."
    ),
    HypothesisType.SHARED_IDENTITY_INDICATORS: (
        "Exact identity keys (email/phone/hash) are shared across evidence."
    ),
    HypothesisType.MULTIPLE_EVIDENCE_SAME_EVENT: (
        "Multiple evidence items map to the same timeline event cluster."
    ),
    HypothesisType.INSUFFICIENT_EVIDENCE: (
        "Case has insufficient evidence to support strong investigative conclusions."
    ),
    HypothesisType.CHAIN_OF_CUSTODY_CONCERN: (
        "Chain-of-custody coverage is incomplete for one or more evidence items."
    ),
    HypothesisType.MISSING_VERIFICATION: (
        "Required verification steps (signature/AI/OCR) are missing."
    ),
    HypothesisType.INVESTIGATION_COMPLETE: (
        "Coverage thresholds indicate the investigation is sufficiently complete."
    ),
}


@dataclass(frozen=True)
class ProvenanceBundle:
    evidence_ids: tuple[str, ...] = ()
    timeline_ids: tuple[str, ...] = ()
    graph_node_ids: tuple[str, ...] = ()
    correlation_ids: tuple[str, ...] = ()
    fusion_ids: tuple[str, ...] = ()
    ai_finding_ids: tuple[str, ...] = ()
    report_ids: tuple[str, ...] = ()
    detail: str | None = None


@dataclass
class HypothesisRecord:
    hypothesis_key: str
    hypothesis_type: HypothesisType
    title: str
    explanation: str
    confidence: float
    priority: PriorityLevel
    status: HypothesisStatus
    supporting_evidence_ids: list[str] = field(default_factory=list)
    contradicting_evidence_ids: list[str] = field(default_factory=list)
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceGapRecord:
    gap_key: str
    gap_type: GapType
    severity: GapSeverity
    reason: str
    recommended_action: RecommendationCode
    affected_evidence_ids: list[str] = field(default_factory=list)
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class RecommendationRecord:
    recommendation_key: str
    code: RecommendationCode
    action_text: str
    priority: PriorityLevel
    related_hypothesis_keys: list[str] = field(default_factory=list)
    related_gap_keys: list[str] = field(default_factory=list)
    affected_evidence_ids: list[str] = field(default_factory=list)
    provenance: ProvenanceBundle = field(default_factory=ProvenanceBundle)


@dataclass
class CoverageMetrics:
    evidence_total: int = 0
    evidence_analyzed: int = 0
    evidence_pending: int = 0
    timeline_coverage: float = 0.0
    knowledge_graph_coverage: float = 0.0
    correlation_coverage: float = 0.0
    fusion_coverage: float = 0.0
    ai_coverage: float = 0.0
    metadata_completeness: float = 0.0
    chain_of_custody_completeness: float = 0.0
    overall_completeness: float = 0.0
    open_conflicts: int = 0


@dataclass
class IntelligenceResult:
    hypotheses: list[HypothesisRecord]
    gaps: list[EvidenceGapRecord]
    recommendations: list[RecommendationRecord]
    coverage: CoverageMetrics
    investigation_score: float
    provenance: dict[str, Any]
    open_conflicts: list[dict[str, Any]] = field(default_factory=list)
