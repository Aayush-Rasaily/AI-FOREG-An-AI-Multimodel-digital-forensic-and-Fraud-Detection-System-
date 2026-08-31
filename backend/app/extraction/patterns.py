"""Conservative, meaning-neutral number and date extraction."""

import re
from collections.abc import Iterable
from datetime import datetime

from backend.app.extraction.models import (
    ExtractionContext,
    ExtractionItem,
    ExtractionSourceType,
    ExtractionType,
)

DATE_PATTERN = re.compile(
    r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
    r"[a-z]*\s+\d{1,2},\s+\d{4})\b",
    re.IGNORECASE,
)
NUMBER_PATTERN = re.compile(r"(?<![\w])\d[\d,.-]*\d(?![\w])")


def structured_value_items(
    text: str,
    context: ExtractionContext,
    *,
    page_number: int | None = None,
    frame_number: int | None = None,
    timestamp_ms: int | None = None,
) -> Iterable[ExtractionItem]:
    """Yield raw date/number matches without assigning semantic labels."""

    date_spans: list[tuple[int, int]] = []
    for match in DATE_PATTERN.finditer(text):
        raw_value = match.group(0)
        date_spans.append(match.span())
        yield ExtractionItem(
            evidence_id=context.evidence_id,
            source_type=ExtractionSourceType.ORIGINAL,
            source_identifier=context.original_filename,
            extraction_type=ExtractionType.DATE,
            page_number=page_number,
            frame_number=frame_number,
            timestamp_ms=timestamp_ms,
            content=raw_value,
            method="date_pattern",
            version="1.0",
            confidence=0.8,
            metadata={
                "source_text": text,
                "normalized_value": _normalize_date(raw_value),
            },
        )
    for match in NUMBER_PATTERN.finditer(text):
        if any(
            start <= match.start() < end
            for start, end in date_spans
        ):
            continue
        raw_value = match.group(0)
        if len(re.sub(r"\D", "", raw_value)) < 3:
            continue
        yield ExtractionItem(
            evidence_id=context.evidence_id,
            source_type=ExtractionSourceType.ORIGINAL,
            source_identifier=context.original_filename,
            extraction_type=ExtractionType.NUMBER,
            page_number=page_number,
            frame_number=frame_number,
            timestamp_ms=timestamp_ms,
            content=raw_value,
            method="number_pattern",
            version="1.0",
            confidence=0.8,
            metadata={"source_text": text},
        )


def _normalize_date(raw_value: str) -> str | None:
    """Normalize only formats that can be parsed without guessing."""

    formats = ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%b %d, %Y")
    for date_format in formats:
        try:
            return datetime.strptime(raw_value, date_format).date().isoformat()
        except ValueError:
            continue
    return None
