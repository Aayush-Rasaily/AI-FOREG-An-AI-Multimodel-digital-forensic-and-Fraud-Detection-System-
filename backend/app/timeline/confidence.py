"""Deterministic timestamp confidence scoring."""

from __future__ import annotations

from backend.app.timeline.models import NormalizedTimestamp

SOURCE_BASE_CONFIDENCE: dict[str, float] = {
    "signed_document": 0.98,
    "filesystem": 0.95,
    "exif": 0.90,
    "processing": 0.85,
    "custody": 0.85,
    "fusion": 0.80,
    "case_intelligence": 0.80,
    "report": 0.80,
    "forensic": 0.80,
    "image_ai": 0.75,
    "document_ai": 0.75,
    "signature_ai": 0.75,
    "video_ai": 0.75,
    "audio_ai": 0.75,
    "manual_note": 0.60,
    "unknown_metadata": 0.30,
    "missing": 0.0,
}

MISSING_TIMEZONE_DEDUCTION = 0.10
NAIVE_TIMEZONE_DEDUCTION = 0.05
MISSING_TIMESTAMP_CONFIDENCE = 0.0


def score_confidence(
    source: str,
    *,
    timezone_known: bool,
    timestamp_present: bool,
    naive: bool = False,
) -> float:
    """Return a deterministic confidence score for one timestamp source."""

    if not timestamp_present:
        return MISSING_TIMESTAMP_CONFIDENCE
    base = SOURCE_BASE_CONFIDENCE.get(
        source, SOURCE_BASE_CONFIDENCE["unknown_metadata"]
    )
    score = base
    if not timezone_known:
        score -= MISSING_TIMEZONE_DEDUCTION
    if naive:
        score -= NAIVE_TIMEZONE_DEDUCTION
    return round(max(0.0, min(1.0, score)), 4)


def uncertainty_ms(normalized: NormalizedTimestamp) -> int:
    """Map confidence to a deterministic uncertainty window in milliseconds."""

    if normalized.normalized_timestamp is None:
        return 86_400_000
    if normalized.confidence >= 0.95:
        return 1_000
    if normalized.confidence >= 0.85:
        return 60_000
    if normalized.confidence >= 0.60:
        return 300_000
    return 3_600_000
