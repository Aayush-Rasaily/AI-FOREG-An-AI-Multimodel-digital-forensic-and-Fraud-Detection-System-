"""Signal collection and matching helpers for correlation."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from backend.app.correlation.models import CorrelationSupport
from backend.app.correlation.scoring import filename_similarity

EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
)
PHONE_RE = re.compile(
    r"\b(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{4}\b",
)
IDENTIFIER_RE = re.compile(
    r"\b(?:INV|INVOICE|ID|REF|DOC|CASE)[-_]?\d{4,}\b",
    re.IGNORECASE,
)
GPS_KEYS = ("gps", "GPS", "gps_latitude", "gps_longitude", "latitude", "longitude")


@dataclass
class EvidenceSignals:
    """Normalized correlation signals for one evidence item."""

    evidence_id: UUID
    evidence_number: str
    sha256_hash: str
    original_filename: str
    mime_type: str
    emails: set[str] = field(default_factory=set)
    phones: set[str] = field(default_factory=set)
    identifiers: set[str] = field(default_factory=set)
    qr_payloads: set[str] = field(default_factory=set)
    camera_models: set[str] = field(default_factory=set)
    device_models: set[str] = field(default_factory=set)
    locations: set[str] = field(default_factory=set)
    document_ids: set[str] = field(default_factory=set)
    logo_labels: set[str] = field(default_factory=set)
    logo_finding_ids: list[str] = field(default_factory=list)
    extraction_ids: list[str] = field(default_factory=list)
    signature_pairs: list[tuple[UUID, UUID, str, float]] = field(default_factory=list)
    speaker_pairs: list[tuple[UUID, str]] = field(default_factory=list)
    metadata_fields: dict[str, str] = field(default_factory=dict)
    timeline_timestamps: list[tuple[str, Any, int]] = field(default_factory=list)


def normalize_email(value: str) -> str:
    return value.strip().lower()


def normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if len(digits) > 10 and digits.startswith("0"):
        digits = digits.lstrip("0")
    return digits


def extract_emails(text: str) -> set[str]:
    return {normalize_email(match) for match in EMAIL_RE.findall(text)}


def extract_phones(text: str) -> set[str]:
    phones: set[str] = set()
    for match in PHONE_RE.findall(text):
        normalized = normalize_phone(match)
        if 7 <= len(normalized) <= 15:
            phones.add(normalized)
    return phones


def extract_identifiers(text: str) -> set[str]:
    return {match.upper() for match in IDENTIFIER_RE.findall(text)}


def metadata_scalar(metadata: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return None


def nested_dict(metadata: dict[str, Any], key: str) -> dict[str, Any]:
    value = metadata.get(key)
    return value if isinstance(value, dict) else {}


def location_key(metadata: dict[str, Any]) -> str | None:
    exif = nested_dict(metadata, "exif")
    gps = (
        nested_dict(metadata, "gps")
        or nested_dict(exif, "gps")
        or nested_dict(exif, "GPS")
    )
    lat = metadata_scalar(gps, "latitude", "lat", "GPSLatitude")
    lon = metadata_scalar(gps, "longitude", "lon", "GPSLongitude")
    if lat and lon:
        return f"{lat},{lon}"
    for key in GPS_KEYS:
        value = metadata_scalar(metadata, key) or metadata_scalar(exif, key)
        if value and "," in value:
            return value
    return None


def group_by_value(
    signals: list[EvidenceSignals],
    getter: Any,
) -> dict[str, list[EvidenceSignals]]:
    groups: dict[str, list[EvidenceSignals]] = defaultdict(list)
    for item in signals:
        values = getter(item)
        for value in values:
            if value:
                groups[str(value)].append(item)
    return groups


def similar_filename_pairs(
    signals: list[EvidenceSignals],
    *,
    threshold: float = 0.5,
) -> list[tuple[EvidenceSignals, EvidenceSignals, float]]:
    pairs: list[tuple[EvidenceSignals, EvidenceSignals, float]] = []
    ordered = sorted(signals, key=lambda item: str(item.evidence_id))
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            score = filename_similarity(left.original_filename, right.original_filename)
            if score >= threshold and left.original_filename != right.original_filename:
                pairs.append((left, right, score))
    return pairs


def support_entity(
    kind: str,
    support_id: str,
    label: str,
    value: str | None = None,
    **metadata: Any,
) -> CorrelationSupport:
    return CorrelationSupport(
        support_kind=kind,
        support_id=support_id,
        label=label,
        value=value,
        metadata=dict(metadata),
    )
