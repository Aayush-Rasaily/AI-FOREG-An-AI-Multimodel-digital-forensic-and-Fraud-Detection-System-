"""Relationship construction between resolved knowledge-graph entities."""

from __future__ import annotations

import hashlib

from backend.app.knowledge_graph.models import (
    GraphEdge,
    GraphProvenanceRef,
    GraphRelationshipType,
    ResolvedEntity,
)
from backend.app.knowledge_graph.scoring import score_relationship


def _edge_id(
    source: str,
    target: str,
    rel_type: str,
) -> str:
    digest = hashlib.sha256(
        f"{source}|{target}|{rel_type}".encode()
    ).hexdigest()
    return f"kgedge_{digest[:24]}"


CorrelationPair = tuple[str, str, str, float, GraphProvenanceRef]
EntityPair = tuple[str, str, GraphProvenanceRef]


def build_relationships(
    entities: list[ResolvedEntity],
    *,
    correlation_pairs: list[CorrelationPair] | None = None,
    mention_pairs: list[EntityPair] | None = None,
    part_of_pairs: list[EntityPair] | None = None,
    derived_pairs: list[EntityPair] | None = None,
) -> list[GraphEdge]:
    """Build deduplicated directed edges from explicit pair inputs."""

    by_id = {entity.entity_id: entity for entity in entities}
    bucket: dict[str, GraphEdge] = {}

    def add_edge(
        source_id: str,
        target_id: str,
        rel_type: GraphRelationshipType,
        *,
        creation_source: str,
        provenance: tuple[GraphProvenanceRef, ...],
        evidence_ids: tuple[str, ...] = (),
        base_confidence: float | None = None,
    ) -> None:
        if source_id not in by_id or target_id not in by_id:
            return
        if source_id == target_id:
            return
        key = _edge_id(source_id, target_id, rel_type.value)
        existing = bucket.get(key)
        prov = provenance
        evidence = set(evidence_ids)
        support = 1
        if existing is not None:
            support = existing.support_count + 1
            evidence.update(existing.evidence_ids)
            prov = tuple(
                sorted(
                    {*(existing.provenance), *provenance},
                    key=lambda item: (
                        item.source_kind,
                        item.source_id,
                        item.evidence_id or "",
                    ),
                )
            )
            # unique by (kind, id, evidence)
            seen: set[tuple[str, str, str | None]] = set()
            unique: list[GraphProvenanceRef] = []
            for ref in prov:
                marker = (ref.source_kind, ref.source_id, ref.evidence_id)
                if marker in seen:
                    continue
                seen.add(marker)
                unique.append(ref)
            prov = tuple(unique)

        confidence, weight = score_relationship(
            relationship_type=rel_type.value,
            support_count=support,
            provenance_count=len(prov),
            base_confidence=base_confidence,
        )
        bucket[key] = GraphEdge(
            relationship_id=key,
            source_entity_id=source_id,
            target_entity_id=target_id,
            relationship_type=rel_type,
            confidence=confidence,
            support_count=support,
            provenance_count=len(prov),
            relationship_weight=weight,
            creation_source=creation_source,
            evidence_ids=tuple(sorted(evidence)),
            provenance=prov,
        )

    for left, right, _ctype, score, prov in correlation_pairs or []:
        add_edge(
            left,
            right,
            GraphRelationshipType.CORRELATED_WITH,
            creation_source="correlation",
            provenance=(prov,),
            evidence_ids=tuple(
                item for item in (prov.evidence_id,) if item
            ),
            base_confidence=min(1.0, max(0.0, score)),
        )

    for source, target, prov in mention_pairs or []:
        add_edge(
            source,
            target,
            GraphRelationshipType.MENTIONS,
            creation_source="extraction",
            provenance=(prov,),
            evidence_ids=tuple(item for item in (prov.evidence_id,) if item),
        )

    for source, target, prov in part_of_pairs or []:
        add_edge(
            source,
            target,
            GraphRelationshipType.PART_OF,
            creation_source="structure",
            provenance=(prov,),
            evidence_ids=tuple(item for item in (prov.evidence_id,) if item),
        )

    for source, target, prov in derived_pairs or []:
        add_edge(
            source,
            target,
            GraphRelationshipType.DERIVED_FROM,
            creation_source="derivation",
            provenance=(prov,),
            evidence_ids=tuple(item for item in (prov.evidence_id,) if item),
        )

    # Exact shared identity across different entity types → SHARES_IDENTIFIER
    identity_map: dict[str, list[ResolvedEntity]] = {}
    for entity in entities:
        for alias in entity.aliases:
            # aliases are normalized display values; also check attributes
            _ = alias
        for key, value in entity.attributes.items():
            if key.startswith("identity:"):
                identity_map.setdefault(str(value), []).append(entity)

    for _value, group in identity_map.items():
        unique = {item.entity_id: item for item in group}
        ids = sorted(unique.keys())
        for i, left in enumerate(ids):
            for right in ids[i + 1 :]:
                add_edge(
                    left,
                    right,
                    GraphRelationshipType.SHARES_IDENTIFIER,
                    creation_source="entity_resolution",
                    provenance=(
                        GraphProvenanceRef(
                            source_kind="entity_resolution",
                            source_id="shared_identity",
                            detail="Exact identity key shared across entities.",
                        ),
                    ),
                )

    return sorted(
        bucket.values(),
        key=lambda edge: (
            edge.relationship_type.value,
            edge.source_entity_id,
            edge.target_entity_id,
        ),
    )
