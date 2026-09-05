"""Chain-of-custody continuity validation."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def custody_gaps(events: list[dict[str, Any]]) -> list[str]:
    """Return human-readable custody continuity issues (deterministic order)."""

    issues: list[str] = []
    if not events:
        issues.append("No custody events recorded.")
        return issues
    ordered = sorted(
        events,
        key=lambda item: (
            str(item.get("timestamp") or ""),
            str(item.get("id") or ""),
        ),
    )
    types = [str(item.get("event_type") or "") for item in ordered]
    if types and types[0] not in {
        "ACQUIRED",
        "REGISTERED",
        "INGESTED",
        "CREATED",
        "EVIDENCE_INGESTED",
        "REFERENCE_REGISTERED",
    }:
        # Soft warning — first event type unexpected
        issues.append(f"First custody event type is {types[0]}.")
    prev_ts: datetime | None = None
    for item in ordered:
        raw = item.get("timestamp")
        if isinstance(raw, datetime):
            ts = raw
        elif isinstance(raw, str) and raw:
            try:
                ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except ValueError:
                issues.append(f"Unparseable custody timestamp on {item.get('id')}.")
                continue
        else:
            issues.append(f"Missing custody timestamp on {item.get('id')}.")
            continue
        if prev_ts is not None and ts < prev_ts:
            issues.append("Custody timestamps are not monotonic.")
            break
        prev_ts = ts
    return issues
