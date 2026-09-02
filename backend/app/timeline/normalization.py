"""Timestamp normalization for the investigation timeline engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from backend.app.timeline.confidence import score_confidence
from backend.app.timeline.models import NormalizedTimestamp


def normalize_timestamp(
    value: datetime | str | None,
    *,
    source: str,
    default_timezone: str | None = "UTC",
) -> NormalizedTimestamp:
    """Normalize one timestamp to UTC with confidence metadata."""

    if value is None:
        return NormalizedTimestamp(
            original_timestamp=None,
            normalized_timestamp=None,
            timezone=None,
            confidence=score_confidence(
                source, timezone_known=False, timestamp_present=False
            ),
            uncertainty_ms=86_400_000,
        )
    parsed = _parse_datetime(value)
    if parsed is None:
        return NormalizedTimestamp(
            original_timestamp=None,
            normalized_timestamp=None,
            timezone=None,
            confidence=score_confidence(
                source, timezone_known=False, timestamp_present=False
            ),
            uncertainty_ms=86_400_000,
        )
    naive = parsed.tzinfo is None
    timezone_name = _timezone_name(parsed, default_timezone)
    normalized = _to_utc(parsed, timezone_name)
    confidence = score_confidence(
        source,
        timezone_known=timezone_name is not None,
        timestamp_present=True,
        naive=naive,
    )
    return NormalizedTimestamp(
        original_timestamp=parsed,
        normalized_timestamp=normalized,
        timezone=timezone_name,
        confidence=confidence,
        uncertainty_ms=_uncertainty_from_confidence(confidence),
    )


def normalize_metadata_timestamp(
    metadata: dict[str, Any],
    *,
    keys: tuple[str, ...],
    source: str,
) -> NormalizedTimestamp | None:
    """Extract and normalize the first available timestamp key from metadata."""

    for key in keys:
        raw = metadata.get(key)
        if raw is not None:
            return normalize_timestamp(raw, source=source)
    return None


def _parse_datetime(value: datetime | str) -> datetime | None:
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _timezone_name(parsed: datetime, default_timezone: str | None) -> str | None:
    if parsed.tzinfo is None:
        return default_timezone
    tz_key = getattr(parsed.tzinfo, "key", None)
    if isinstance(tz_key, str):
        return tz_key
    return "UTC"


def _to_utc(parsed: datetime, timezone_name: str | None) -> datetime:
    if parsed.tzinfo is not None:
        return parsed.astimezone(UTC)
    if timezone_name:
        try:
            localized = parsed.replace(tzinfo=ZoneInfo(timezone_name))
            return localized.astimezone(UTC)
        except ZoneInfoNotFoundError:
            return parsed.replace(tzinfo=UTC)
    return parsed.replace(tzinfo=UTC)


def _uncertainty_from_confidence(confidence: float) -> int:
    if confidence >= 0.95:
        return 1_000
    if confidence >= 0.85:
        return 60_000
    if confidence >= 0.60:
        return 300_000
    return 3_600_000
