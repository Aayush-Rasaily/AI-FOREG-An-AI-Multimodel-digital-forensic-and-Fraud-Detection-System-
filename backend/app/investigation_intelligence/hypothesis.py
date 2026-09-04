"""Deterministic hypothesis generation from investigation snapshots."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.investigation_intelligence.models import (
    HYPOTHESIS_EXPLANATIONS,
    CoverageMetrics,
    HypothesisRecord,
    HypothesisStatus,
    HypothesisType,
    ProvenanceBundle,
)
from backend.app.investigation_intelligence.prioritization import priority_from_score
from backend.app.investigation_intelligence.scoring import score_hypothesis


def _key(hypothesis_type: str, *parts: str) -> str:
    material = "|".join((hypothesis_type, *parts))
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"hyp_{digest[:24]}"


def _title(hypothesis_type: HypothesisType) -> str:
    return hypothesis_type.value.replace("_", " ").title()


def generate_hypotheses(
    snapshot: dict[str, Any],
    coverage: CoverageMetrics,
) -> list[HypothesisRecord]:
    """Build ranked hypotheses from a collected snapshot. Deterministic only."""

    out: list[HypothesisRecord] = []
    evidence = snapshot.get("evidence", [])
    evidence_ids = [str(item["id"]) for item in evidence]
    findings = snapshot.get("ai_findings", [])
    correlations = snapshot.get("correlations", [])
    timeline_conflicts = snapshot.get("timeline_conflicts", [])
    fusion_runs = snapshot.get("fusion_runs", [])
    signatures = snapshot.get("signatures", [])
    graph_rels = snapshot.get("graph_relationships", [])
    graph_entities = snapshot.get("graph_entities", [])
    custody = snapshot.get("custody_by_evidence", {})

    def add(
        htype: HypothesisType,
        *,
        support: list[str],
        contradict: list[str] | None = None,
        provenance: ProvenanceBundle,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        contradict = contradict or []
        conf = score_hypothesis(
            htype.value,
            support_count=max(1, len(support)),
            contradict_count=len(contradict),
            provenance_count=max(
                1,
                len(provenance.evidence_ids)
                + len(provenance.ai_finding_ids)
                + len(provenance.correlation_ids)
                + len(provenance.fusion_ids)
                + len(provenance.timeline_ids),
            ),
        )
        status = HypothesisStatus.OPEN
        if contradict and conf < 0.5:
            status = HypothesisStatus.CONTRADICTED
        elif conf >= 0.8 and not contradict:
            status = HypothesisStatus.SUPPORTED
        out.append(
            HypothesisRecord(
                hypothesis_key=_key(htype.value, *sorted(support)[:8]),
                hypothesis_type=htype,
                title=_title(htype),
                explanation=HYPOTHESIS_EXPLANATIONS[htype],
                confidence=conf,
                priority=priority_from_score(conf),
                status=status,
                supporting_evidence_ids=sorted(set(support)),
                contradicting_evidence_ids=sorted(set(contradict)),
                provenance=provenance,
                attributes=attributes or {},
            )
        )

    if len(evidence) == 0:
        add(
            HypothesisType.INSUFFICIENT_EVIDENCE,
            support=[],
            provenance=ProvenanceBundle(detail="No evidence registered."),
        )
    elif len(evidence) == 1:
        add(
            HypothesisType.INSUFFICIENT_EVIDENCE,
            support=evidence_ids[:1],
            provenance=ProvenanceBundle(
                evidence_ids=tuple(evidence_ids[:1]),
                detail="Single evidence item only.",
            ),
        )

    tamper_findings = [
        item
        for item in findings
        if any(
            token in str(item.get("finding_type", "")).lower()
            for token in ("tamper", "manipulat", "forge", "alter")
        )
        or str(item.get("modality", "")).lower() == "document"
        and float(item.get("confidence") or 0) >= 0.7
    ]
    if tamper_findings:
        eids = sorted({str(item["evidence_id"]) for item in tamper_findings})
        add(
            HypothesisType.LIKELY_DOCUMENT_TAMPERING,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                ai_finding_ids=tuple(
                    sorted(str(item["id"]) for item in tamper_findings)
                ),
            ),
        )

    deepfake_findings = [
        item
        for item in findings
        if any(
            token in str(item.get("finding_type", "")).lower()
            for token in ("deepfake", "synthetic", "gan", "face_swap")
        )
    ]
    if deepfake_findings:
        eids = sorted({str(item["evidence_id"]) for item in deepfake_findings})
        add(
            HypothesisType.POTENTIAL_DEEPFAKE_MEDIA,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                ai_finding_ids=tuple(
                    sorted(str(item["id"]) for item in deepfake_findings)
                ),
            ),
        )

    failed_sigs = [
        item
        for item in signatures
        if str(item.get("status", "")).upper() in {"FAILED", "INVALID", "MISMATCH"}
        or item.get("consistent") is False
    ]
    if failed_sigs:
        eids = sorted(
            {
                str(item["evidence_id"])
                for item in failed_sigs
                if item.get("evidence_id")
            }
        )
        add(
            HypothesisType.SIGNATURE_INCONSISTENCY,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                detail="Signature verification inconsistency.",
            ),
        )

    missing_meta = [
        str(item["id"])
        for item in evidence
        if not item.get("has_metadata")
    ]
    if missing_meta:
        add(
            HypothesisType.METADATA_MANIPULATION,
            support=missing_meta,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(sorted(missing_meta)),
                detail="Missing or empty metadata fields.",
            ),
        )

    if correlations:
        eids = sorted(
            {
                str(item.get("left_evidence_id") or item.get("evidence_a_id") or "")
                for item in correlations
            }
            | {
                str(item.get("right_evidence_id") or item.get("evidence_b_id") or "")
                for item in correlations
            }
            - {""}
        )
        add(
            HypothesisType.CROSS_EVIDENCE_CORROBORATION,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                correlation_ids=tuple(
                    sorted(str(item["id"]) for item in correlations)
                ),
            ),
        )

    if timeline_conflicts:
        tids = tuple(sorted(str(item["id"]) for item in timeline_conflicts))
        eids = sorted(
            {
                str(eid)
                for item in timeline_conflicts
                for eid in (item.get("evidence_ids") or [])
            }
        )
        add(
            HypothesisType.TIMELINE_CONFLICT,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                timeline_ids=tids,
            ),
        )

    device_rels = [
        item
        for item in graph_rels
        if str(item.get("relationship_type", "")).upper()
        in {"USES_DEVICE", "SHARES_IDENTIFIER", "CONNECTED_TO"}
    ]
    if device_rels:
        eids = sorted(
            {
                str(eid)
                for item in device_rels
                for eid in (item.get("evidence_ids") or [])
            }
        )
        add(
            HypothesisType.SHARED_DEVICE_USAGE
            if any(
                str(item.get("relationship_type", "")).upper() == "USES_DEVICE"
                for item in device_rels
            )
            else HypothesisType.SHARED_IDENTITY_INDICATORS,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                graph_node_ids=tuple(
                    sorted(
                        {
                            str(item.get("source_entity_key") or "")
                            for item in device_rels
                        }
                        | {
                            str(item.get("target_entity_key") or "")
                            for item in device_rels
                        }
                        - {""}
                    )
                ),
            ),
        )

    identity_entities = [
        item
        for item in graph_entities
        if str(item.get("entity_type", "")).upper()
        in {"EMAIL", "PHONE", "IMEI", "MAC", "DEVICE"}
    ]
    if len(identity_entities) >= 1 and any(
        len(item.get("evidence_ids") or []) > 1 for item in identity_entities
    ):
        eids = sorted(
            {
                str(eid)
                for item in identity_entities
                for eid in (item.get("evidence_ids") or [])
            }
        )
        add(
            HypothesisType.SHARED_IDENTITY_INDICATORS,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                graph_node_ids=tuple(
                    sorted(
                        str(item.get("entity_key") or "")
                        for item in identity_entities
                    )
                ),
            ),
            attributes={"identity_entity_count": len(identity_entities)},
        )
        if len(eids) >= 2:
            add(
                HypothesisType.POSSIBLE_IDENTITY_FRAUD,
                support=eids,
                provenance=ProvenanceBundle(
                    evidence_ids=tuple(eids),
                    graph_node_ids=tuple(
                        sorted(
                            str(item.get("entity_key") or "")
                            for item in identity_entities
                        )
                    ),
                ),
            )

    event_clusters = snapshot.get("timeline_event_clusters", [])
    multi = [
        cluster
        for cluster in event_clusters
        if len(cluster.get("evidence_ids", [])) >= 2
    ]
    if multi:
        eids = sorted(
            {str(eid) for cluster in multi for eid in cluster.get("evidence_ids", [])}
        )
        add(
            HypothesisType.MULTIPLE_EVIDENCE_SAME_EVENT,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                timeline_ids=tuple(
                    sorted(str(cluster.get("event_id") or "") for cluster in multi)
                ),
            ),
        )

    custody_gaps = [
        eid for eid, count in custody.items() if int(count or 0) == 0
    ]
    if custody_gaps:
        add(
            HypothesisType.CHAIN_OF_CUSTODY_CONCERN,
            support=sorted(custody_gaps),
            provenance=ProvenanceBundle(
                evidence_ids=tuple(sorted(custody_gaps)),
                detail="Evidence lacking custody events.",
            ),
        )

    pending_ai = coverage.evidence_pending
    if pending_ai > 0 or coverage.ai_coverage < 0.5:
        add(
            HypothesisType.MISSING_VERIFICATION,
            support=evidence_ids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(evidence_ids),
                detail="AI/signature/OCR verification incomplete.",
            ),
        )

    high_risk_fusion = [
        item
        for item in fusion_runs
        if str(item.get("verdict", "")).upper()
        in {"HIGH_RISK", "TAMPERED", "SUSPICIOUS", "UNRELIABLE"}
        or float(item.get("risk_score") or 0) >= 0.7
    ]
    if high_risk_fusion and not tamper_findings:
        eids = sorted({str(item["evidence_id"]) for item in high_risk_fusion})
        add(
            HypothesisType.LIKELY_DOCUMENT_TAMPERING,
            support=eids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(eids),
                fusion_ids=tuple(sorted(str(item["id"]) for item in high_risk_fusion)),
            ),
        )

    if (
        coverage.overall_completeness >= 0.85
        and coverage.open_conflicts == 0
        and len(evidence) >= 2
    ):
        add(
            HypothesisType.INVESTIGATION_COMPLETE,
            support=evidence_ids,
            provenance=ProvenanceBundle(
                evidence_ids=tuple(evidence_ids),
                detail="Coverage thresholds met without open conflicts.",
            ),
        )

    # Deterministic ordering
    out.sort(
        key=lambda item: (
            {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[item.priority.value],
            -item.confidence,
            item.hypothesis_type.value,
            item.hypothesis_key,
        )
    )
    # Deduplicate by hypothesis_key
    seen: set[str] = set()
    unique: list[HypothesisRecord] = []
    for item in out:
        if item.hypothesis_key in seen:
            continue
        seen.add(item.hypothesis_key)
        unique.append(item)
    return unique
