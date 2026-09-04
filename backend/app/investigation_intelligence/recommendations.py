"""Deterministic recommendation generation (fixed templates only)."""

from __future__ import annotations

import hashlib

from backend.app.investigation_intelligence.models import (
    RECOMMENDATION_TEXT,
    EvidenceGapRecord,
    HypothesisRecord,
    HypothesisType,
    ProvenanceBundle,
    RecommendationCode,
    RecommendationRecord,
)
from backend.app.investigation_intelligence.prioritization import (
    priority_from_score,
    priority_from_severity,
    rank_priority_value,
)


def _key(code: str, *parts: str) -> str:
    material = "|".join((code, *parts))
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"rec_{digest[:24]}"


def generate_recommendations(
    hypotheses: list[HypothesisRecord],
    gaps: list[EvidenceGapRecord],
) -> list[RecommendationRecord]:
    """Map hypotheses and gaps to fixed recommendation templates."""

    bucket: dict[str, RecommendationRecord] = {}

    def upsert(
        code: RecommendationCode,
        *,
        priority_score: float,
        evidence_ids: list[str],
        hypothesis_keys: list[str] | None = None,
        gap_keys: list[str] | None = None,
        detail: str | None = None,
    ) -> None:
        key = _key(code.value, *sorted(evidence_ids)[:8], code.value)
        priority = priority_from_score(priority_score)
        existing = bucket.get(key)
        if existing is None:
            bucket[key] = RecommendationRecord(
                recommendation_key=key,
                code=code,
                action_text=RECOMMENDATION_TEXT[code],
                priority=priority,
                related_hypothesis_keys=sorted(set(hypothesis_keys or [])),
                related_gap_keys=sorted(set(gap_keys or [])),
                affected_evidence_ids=sorted(set(evidence_ids)),
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(sorted(set(evidence_ids))),
                    detail=detail,
                ),
            )
            return
        existing.related_hypothesis_keys = sorted(
            set(existing.related_hypothesis_keys) | set(hypothesis_keys or [])
        )
        existing.related_gap_keys = sorted(
            set(existing.related_gap_keys) | set(gap_keys or [])
        )
        existing.affected_evidence_ids = sorted(
            set(existing.affected_evidence_ids) | set(evidence_ids)
        )
        if rank_priority_value(priority) < rank_priority_value(existing.priority):
            existing.priority = priority

    hypothesis_map: dict[HypothesisType, RecommendationCode] = {
        HypothesisType.LIKELY_DOCUMENT_TAMPERING: (
            RecommendationCode.COMPARE_KNOWN_EVIDENCE
        ),
        HypothesisType.POTENTIAL_DEEPFAKE_MEDIA: (
            RecommendationCode.RUN_IMAGE_COMPARISON
        ),
        HypothesisType.SIGNATURE_INCONSISTENCY: (
            RecommendationCode.VERIFY_DIGITAL_SIGNATURE
        ),
        HypothesisType.METADATA_MANIPULATION: (
            RecommendationCode.OBTAIN_DEVICE_METADATA
        ),
        HypothesisType.TIMELINE_CONFLICT: (
            RecommendationCode.INVESTIGATE_TIMELINE_INCONSISTENCY
        ),
        HypothesisType.CHAIN_OF_CUSTODY_CONCERN: (
            RecommendationCode.VERIFY_CHAIN_OF_CUSTODY
        ),
        HypothesisType.MISSING_VERIFICATION: RecommendationCode.RUN_AI_ANALYSIS,
        HypothesisType.INSUFFICIENT_EVIDENCE: (
            RecommendationCode.COLLECT_CORROBORATING_EVIDENCE
        ),
        HypothesisType.SHARED_IDENTITY_INDICATORS: (
            RecommendationCode.REVIEW_UNRESOLVED_RELATIONSHIPS
        ),
        HypothesisType.POSSIBLE_IDENTITY_FRAUD: (
            RecommendationCode.COMPARE_KNOWN_EVIDENCE
        ),
        HypothesisType.CROSS_EVIDENCE_CORROBORATION: (
            RecommendationCode.COMPARE_KNOWN_EVIDENCE
        ),
        HypothesisType.SHARED_DEVICE_USAGE: (
            RecommendationCode.REVIEW_UNRESOLVED_RELATIONSHIPS
        ),
    }

    for hyp in hypotheses:
        code = hypothesis_map.get(hyp.hypothesis_type)
        if code is None:
            continue
        upsert(
            code,
            priority_score=hyp.confidence,
            evidence_ids=hyp.supporting_evidence_ids,
            hypothesis_keys=[hyp.hypothesis_key],
            detail=hyp.explanation,
        )

    for gap in gaps:
        upsert(
            gap.recommended_action,
            priority_score={
                "HIGH": 0.9,
                "MEDIUM": 0.6,
                "LOW": 0.3,
            }[gap.severity.value],
            evidence_ids=gap.affected_evidence_ids,
            gap_keys=[gap.gap_key],
            detail=gap.reason,
        )
        # Align priority with gap severity when higher
        key = _key(
            gap.recommended_action.value,
            *sorted(gap.affected_evidence_ids)[:8],
            gap.recommended_action.value,
        )
        rec = bucket.get(key)
        if rec is not None:
            sev_priority = priority_from_severity(gap.severity)
            if rank_priority_value(sev_priority) < rank_priority_value(rec.priority):
                rec.priority = sev_priority

    items = list(bucket.values())
    items.sort(
        key=lambda item: (
            rank_priority_value(item.priority),
            item.code.value,
            item.recommendation_key,
        )
    )
    return items
