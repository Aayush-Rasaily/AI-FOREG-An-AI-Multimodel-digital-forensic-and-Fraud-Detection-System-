"""Metadata and field drift detection."""

from __future__ import annotations

import hashlib
from typing import Any

from backend.app.integrity.hash_monitor import metadata_fingerprint
from backend.app.integrity.models import DriftDraft, ProvenanceBundle


def _key(*parts: str) -> str:
    material = "|".join(parts)
    digest = hashlib.sha256(material.encode()).hexdigest()
    return f"imdrift_{digest[:24]}"


def detect_drifts(
    evidence_items: list[dict[str, Any]],
    previous_fingerprints: dict[str, str],
) -> list[DriftDraft]:
    """Compare current metadata fingerprints to prior integrity snapshots."""

    drifts: list[DriftDraft] = []
    for item in sorted(evidence_items, key=lambda row: str(row["id"])):
        eid = str(item["id"])
        current = metadata_fingerprint(item.get("metadata") or {})
        previous = previous_fingerprints.get(eid)
        if previous is None:
            continue
        if previous != current:
            drifts.append(
                DriftDraft(
                    drift_key=_key(eid, "metadata", previous[:16], current[:16]),
                    evidence_id=eid,
                    field_name="metadata",
                    previous_value=previous,
                    current_value=current,
                    message=(
                        "Evidence metadata fingerprint changed since last monitor run."
                    ),
                    provenance=ProvenanceBundle(
                        evidence_ids=(eid,),
                        detail="metadata_drift",
                    ),
                )
            )
        recorded_mime = str(item.get("mime_type") or "")
        prior_mime = previous_fingerprints.get(f"{eid}:mime")
        if prior_mime and prior_mime != recorded_mime:
            drifts.append(
                DriftDraft(
                    drift_key=_key(eid, "mime", prior_mime, recorded_mime),
                    evidence_id=eid,
                    field_name="mime_type",
                    previous_value=prior_mime,
                    current_value=recorded_mime,
                    message="MIME type changed since last monitor run.",
                    provenance=ProvenanceBundle(
                        evidence_ids=(eid,),
                        detail="mime_drift",
                    ),
                )
            )
        recorded_size = str(item.get("file_size") or "")
        prior_size = previous_fingerprints.get(f"{eid}:size")
        if prior_size and prior_size != recorded_size:
            drifts.append(
                DriftDraft(
                    drift_key=_key(eid, "size", prior_size, recorded_size),
                    evidence_id=eid,
                    field_name="file_size",
                    previous_value=prior_size,
                    current_value=recorded_size,
                    message="File size changed since last monitor run.",
                    provenance=ProvenanceBundle(
                        evidence_ids=(eid,),
                        detail="size_drift",
                    ),
                )
            )
    drifts.sort(key=lambda item: (item.evidence_id, item.field_name, item.drift_key))
    return drifts


def current_fingerprints(evidence_items: list[dict[str, Any]]) -> dict[str, str]:
    """Snapshot fingerprints for persistence on this run."""

    out: dict[str, str] = {}
    for item in evidence_items:
        eid = str(item["id"])
        out[eid] = metadata_fingerprint(item.get("metadata") or {})
        out[f"{eid}:mime"] = str(item.get("mime_type") or "")
        out[f"{eid}:size"] = str(item.get("file_size") or "")
    return dict(sorted(out.items()))
