"""Investigation graph serialization helpers."""

from __future__ import annotations

from typing import Any

from backend.app.entities.models import (
    CanonicalEntity,
    EntityEdge,
    InvestigationGraph,
)


def build_graph(
    entities: tuple[CanonicalEntity, ...],
    relationships: tuple[EntityEdge, ...],
    *,
    provenance: dict[str, Any],
    metadata: dict[str, Any],
) -> InvestigationGraph:
    """Assemble a deterministic investigation graph."""

    ordered_nodes = tuple(
        sorted(
            entities,
            key=lambda item: (
                item.entity_type.value,
                item.normalized_key,
                item.canonical_id,
            ),
        )
    )
    ordered_edges = tuple(
        sorted(
            relationships,
            key=lambda item: (
                -item.confidence,
                item.relationship_type.value,
                item.source_canonical_id,
                item.target_canonical_id,
                item.relationship_id,
            ),
        )
    )
    return InvestigationGraph(
        nodes=ordered_nodes,
        edges=ordered_edges,
        provenance=provenance,
        metadata=metadata,
    )


def neighborhood_graph(
    entities: tuple[CanonicalEntity, ...],
    relationships: tuple[EntityEdge, ...],
    canonical_id: str,
) -> InvestigationGraph:
    """Return the subgraph centered on one entity."""

    related_ids = {canonical_id}
    edges: list[EntityEdge] = []
    for edge in relationships:
        if (
            edge.source_canonical_id == canonical_id
            or edge.target_canonical_id == canonical_id
        ):
            edges.append(edge)
            related_ids.add(edge.source_canonical_id)
            related_ids.add(edge.target_canonical_id)
    nodes = tuple(item for item in entities if item.canonical_id in related_ids)
    return build_graph(
        nodes,
        tuple(edges),
        provenance={"center_canonical_id": canonical_id, "node_count": len(nodes)},
        metadata={"edge_count": len(edges)},
    )
