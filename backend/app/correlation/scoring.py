"""Deterministic correlation scoring helpers."""

from __future__ import annotations

from backend.app.correlation import policy
from backend.app.correlation.models import CorrelationType

SCORE_BY_TYPE: dict[CorrelationType, float] = {
    CorrelationType.SAME_HASH: policy.SCORE_SAME_HASH,
    CorrelationType.SAME_EMAIL: policy.SCORE_SAME_EMAIL,
    CorrelationType.SAME_PHONE: policy.SCORE_SAME_PHONE,
    CorrelationType.SAME_QR: policy.SCORE_SAME_QR,
    CorrelationType.SAME_SIGNATURE: policy.SCORE_SAME_SIGNATURE,
    CorrelationType.SAME_LOCATION: policy.SCORE_SAME_LOCATION,
    CorrelationType.SAME_CAMERA: policy.SCORE_SAME_CAMERA,
    CorrelationType.SAME_DEVICE: policy.SCORE_SAME_DEVICE,
    CorrelationType.SAME_AUDIO_SPEAKER: policy.SCORE_SAME_AUDIO_SPEAKER,
    CorrelationType.SAME_LOGO: policy.SCORE_SAME_LOGO,
    CorrelationType.SAME_DOCUMENT: policy.SCORE_SAME_DOCUMENT,
    CorrelationType.SHARED_IDENTIFIER: policy.SCORE_SHARED_IDENTIFIER,
    CorrelationType.SHARED_METADATA: policy.SCORE_SHARED_METADATA,
    CorrelationType.TEMPORAL_OVERLAP: policy.SCORE_TEMPORAL_OVERLAP,
    CorrelationType.SIMILAR_FILENAME: policy.SCORE_SIMILAR_FILENAME,
}

CONFIDENCE_BY_TYPE: dict[CorrelationType, float] = {
    CorrelationType.SAME_HASH: policy.CONFIDENCE_EXACT,
    CorrelationType.SAME_EMAIL: policy.CONFIDENCE_STRONG,
    CorrelationType.SAME_PHONE: policy.CONFIDENCE_STRONG,
    CorrelationType.SAME_QR: policy.CONFIDENCE_STRONG,
    CorrelationType.SAME_SIGNATURE: policy.CONFIDENCE_STRONG,
    CorrelationType.SAME_LOCATION: policy.CONFIDENCE_STRONG,
    CorrelationType.SAME_CAMERA: policy.CONFIDENCE_MODERATE,
    CorrelationType.SAME_DEVICE: policy.CONFIDENCE_MODERATE,
    CorrelationType.SAME_AUDIO_SPEAKER: policy.CONFIDENCE_MODERATE,
    CorrelationType.SAME_LOGO: policy.CONFIDENCE_MODERATE,
    CorrelationType.SAME_DOCUMENT: policy.CONFIDENCE_MODERATE,
    CorrelationType.SHARED_IDENTIFIER: policy.CONFIDENCE_MODERATE,
    CorrelationType.SHARED_METADATA: policy.CONFIDENCE_MODERATE,
    CorrelationType.TEMPORAL_OVERLAP: policy.CONFIDENCE_WEAK,
    CorrelationType.SIMILAR_FILENAME: policy.CONFIDENCE_WEAK,
}


def score_for(correlation_type: CorrelationType) -> float:
    """Return the deterministic base score for a correlation type."""

    return SCORE_BY_TYPE[correlation_type]


def confidence_for(correlation_type: CorrelationType) -> float:
    """Return the deterministic confidence for a correlation type."""

    return CONFIDENCE_BY_TYPE[correlation_type]


def filename_similarity(left: str, right: str) -> float:
    """Deterministic Jaccard token similarity for filenames (0..1)."""

    left_tokens = _filename_tokens(left)
    right_tokens = _filename_tokens(right)
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return round(len(intersection) / len(union), 4)


def _filename_tokens(name: str) -> set[str]:
    cleaned = name.lower().replace("_", " ").replace("-", " ").replace(".", " ")
    return {token for token in cleaned.split() if len(token) > 1}
