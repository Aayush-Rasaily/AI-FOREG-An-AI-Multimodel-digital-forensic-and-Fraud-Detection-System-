"""Deterministic entity resolution (exact identity keys only)."""

from __future__ import annotations

import hashlib
from collections import defaultdict

from backend.app.knowledge_graph.models import (
    CandidateEntity,
    GraphProvenanceRef,
    ResolvedEntity,
)
from backend.app.knowledge_graph.policy import MERGE_CONFIDENCE
from backend.app.knowledge_graph.provenance import merge_provenance


def normalize_identity_value(value: str) -> str:
    """Normalize identity strings for exact matching."""

    return " ".join(value.strip().lower().split())


def make_identity_key(kind: str, value: str) -> str:
    """Build a typed identity key used for exact merges."""

    return f"{kind.upper()}:{normalize_identity_value(value)}"


def _stable_entity_id(entity_type: str, normalized_key: str) -> str:
    digest = hashlib.sha256(f"{entity_type}|{normalized_key}".encode()).hexdigest()
    return f"kgent_{digest[:24]}"


def resolve_entities(candidates: list[CandidateEntity]) -> list[ResolvedEntity]:
    """Merge candidates that share exact identity keys.

    Never uses fuzzy or LLM matching. Merge provenance is preserved.
    """

    # Union-find over candidate indices via shared identity keys
    parent = list(range(len(candidates)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri == rj:
            return
        if ri < rj:
            parent[rj] = ri
        else:
            parent[ri] = rj

    key_to_indices: dict[str, list[int]] = defaultdict(list)
    for index, candidate in enumerate(candidates):
        keys = candidate.identity_keys or (candidate.normalized_key,)
        for key in keys:
            key_to_indices[key].append(index)

    for indices in key_to_indices.values():
        if len(indices) < 2:
            continue
        first = indices[0]
        for other in indices[1:]:
            # Only merge same entity type
            if candidates[first].entity_type == candidates[other].entity_type:
                union(first, other)

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(candidates)):
        groups[find(index)].append(index)

    resolved: list[ResolvedEntity] = []
    for root in sorted(groups.keys()):
        members = sorted(groups[root])
        primary = candidates[members[0]]
        aliases: list[str] = []
        evidence: set[str] = set()
        provenance: tuple[GraphProvenanceRef, ...] = ()
        attributes: dict = {}
        identity_kinds: list[str] = []
        display_names: list[str] = []

        for index in members:
            item = candidates[index]
            display_names.append(item.display_name)
            aliases.append(item.display_name)
            aliases.append(item.normalized_key)
            evidence.update(item.evidence_ids)
            provenance = merge_provenance(provenance, item.provenance)
            attributes.update(item.attributes)
            for key in item.identity_keys:
                kind = key.split(":", 1)[0]
                identity_kinds.append(kind)

        # Deterministic display name: shortest then lexical
        display_name = sorted(display_names, key=lambda name: (len(name), name))[0]
        confidences = [
            MERGE_CONFIDENCE.get(kind, MERGE_CONFIDENCE["DEFAULT"])
            for kind in identity_kinds
        ] or [MERGE_CONFIDENCE["DEFAULT"]]
        confidence = max(confidences)
        if len(members) > 1:
            # Documented merge boost for multi-support exact identity
            confidence = min(1.0, round(confidence + 0.01 * (len(members) - 1), 4))

        unique_aliases = tuple(
            sorted({normalize_identity_value(alias) for alias in aliases if alias})
        )
        entity = ResolvedEntity(
            entity_id=_stable_entity_id(
                primary.entity_type.value, primary.normalized_key,
            ),
            entity_type=primary.entity_type,
            display_name=display_name,
            normalized_key=primary.normalized_key,
            aliases=unique_aliases,
            confidence=confidence,
            attributes=dict(sorted(attributes.items())),
            evidence_ids=tuple(sorted(evidence)),
            provenance=provenance,
        )
        resolved.append(entity)

    return sorted(
        resolved,
        key=lambda item: (item.entity_type.value, item.normalized_key, item.entity_id),
    )
