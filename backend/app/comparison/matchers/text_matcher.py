"""Text, number, and date comparison matcher."""

import asyncio
import difflib
import re

from backend.app.comparison.models import (
    ComparisonContext,
    DifferenceItem,
    DifferenceSeverity,
    DifferenceType,
    MatcherResult,
)
from backend.app.comparison.utils import extract_text_content

NUMBER_PATTERN = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b")
DATE_PATTERN = re.compile(r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b")
CURRENCY_PATTERN = re.compile(r"[$€£₹]\s?[\d,]+(?:\.\d+)?|\bUSD\s?[\d,]+(?:\.\d+)?")


class TextMatcher:
    """Compare extracted text, numbers, and dates between reference and questioned."""

    name = "text"
    version = "1.0"

    def can_compare(self, context: ComparisonContext) -> bool:
        return bool(context.questioned_extractions or context.reference_extractions)

    async def compare(self, context: ComparisonContext) -> MatcherResult:
        differences = await asyncio.to_thread(_compare_text, context)
        return MatcherResult(
            matcher=self.name,
            version=self.version,
            differences=tuple(differences),
            metadata={"difference_count": len(differences)},
        )


def _compare_text(context: ComparisonContext) -> list[DifferenceItem]:
    reference_text = extract_text_content(context.reference_extractions)
    questioned_text = extract_text_content(context.questioned_extractions)
    differences: list[DifferenceItem] = []
    if not reference_text and questioned_text:
        differences.append(
            DifferenceItem(
                matcher="text",
                difference_type=DifferenceType.TEXT_INSERTED,
                severity=DifferenceSeverity.MEDIUM,
                confidence=0.85,
                description="Submitted document contains text absent from reference.",
                explanation=(
                    "Questioned extraction produced text where reference was empty."
                ),
                submitted_value=questioned_text[:240],
            )
        )
    if reference_text and not questioned_text:
        differences.append(
            DifferenceItem(
                matcher="text",
                difference_type=DifferenceType.TEXT_REMOVED,
                severity=DifferenceSeverity.MEDIUM,
                confidence=0.85,
                description="Reference text is missing from submitted document.",
                explanation=(
                    "Reference extraction produced text "
                    "not present in questioned output."
                ),
                original_value=reference_text[:240],
            )
        )
    if reference_text and questioned_text and reference_text != questioned_text:
        ratio = difflib.SequenceMatcher(
            None,
            reference_text,
            questioned_text,
        ).ratio()
        if ratio < 0.98:
            differences.append(
                DifferenceItem(
                    matcher="text",
                    difference_type=DifferenceType.TEXT_CHANGED,
                    severity=(
                        DifferenceSeverity.HIGH
                        if ratio < 0.85
                        else DifferenceSeverity.MEDIUM
                    ),
                    confidence=min(0.95, 1.0 - ratio + 0.2),
                    description="Extracted text differs from reference content.",
                    explanation=(
                        f"Sequence similarity ratio {ratio:.3f} "
                        "indicates textual changes."
                    ),
                    original_value=reference_text[:240],
                    submitted_value=questioned_text[:240],
                    metadata={"similarity_ratio": round(ratio, 4)},
                )
            )
        differences.extend(
            _compare_numbers(reference_text, questioned_text),
        )
        differences.extend(
            _compare_dates(reference_text, questioned_text),
        )
    return differences


def _compare_numbers(reference: str, questioned: str) -> list[DifferenceItem]:
    ref_numbers = NUMBER_PATTERN.findall(reference)
    q_numbers = NUMBER_PATTERN.findall(questioned)
    differences: list[DifferenceItem] = []
    for index, ref_value in enumerate(ref_numbers[:20]):
        if index >= len(q_numbers):
            break
        q_value = q_numbers[index]
        if ref_value == q_value:
            continue
        ref_amount = _parse_amount(ref_value)
        q_amount = _parse_amount(q_value)
        delta = q_amount - ref_amount
        differences.append(
            DifferenceItem(
                matcher="text",
                difference_type=DifferenceType.NUMBER_CHANGED,
                severity=(
                    DifferenceSeverity.HIGH
                    if abs(delta) > 1000
                    else DifferenceSeverity.MEDIUM
                ),
                confidence=0.9,
                description=(
                    "Numeric value changed between reference and submitted text."
                ),
                explanation=(
                    f"Position {index + 1}: {ref_value} -> {q_value} "
                    f"(delta {delta:+.2f})."
                ),
                original_value=ref_value,
                submitted_value=q_value,
                metadata={"delta": delta},
            )
        )
    ref_currencies = CURRENCY_PATTERN.findall(reference)
    q_currencies = CURRENCY_PATTERN.findall(questioned)
    for index, ref_value in enumerate(ref_currencies[:10]):
        if index >= len(q_currencies):
            break
        q_value = q_currencies[index]
        if ref_value == q_value:
            continue
        ref_amount = _parse_amount(ref_value)
        q_amount = _parse_amount(q_value)
        differences.append(
            DifferenceItem(
                matcher="text",
                difference_type=DifferenceType.NUMBER_CHANGED,
                severity=DifferenceSeverity.HIGH,
                confidence=0.92,
                description=(
                    "Monetary amount changed between reference and submitted text."
                ),
                explanation=(
                    f"Currency value changed from {ref_value} to {q_value} "
                    f"(delta {q_amount - ref_amount:+.2f})."
                ),
                original_value=ref_value,
                submitted_value=q_value,
                metadata={"delta": q_amount - ref_amount},
            )
        )
    return differences


def _compare_dates(reference: str, questioned: str) -> list[DifferenceItem]:
    ref_dates = DATE_PATTERN.findall(reference)
    q_dates = DATE_PATTERN.findall(questioned)
    differences: list[DifferenceItem] = []
    for index, ref_parts in enumerate(ref_dates[:10]):
        if index >= len(q_dates):
            break
        q_parts = q_dates[index]
        ref_raw = "/".join(ref_parts)
        q_raw = "/".join(q_parts)
        if ref_raw == q_raw:
            continue
        differences.append(
            DifferenceItem(
                matcher="text",
                difference_type=DifferenceType.DATE_CHANGED,
                severity=DifferenceSeverity.MEDIUM,
                confidence=0.88,
                description="Date value changed between reference and submitted text.",
                explanation=f"Date at position {index + 1}: {ref_raw} -> {q_raw}.",
                original_value=ref_raw,
                submitted_value=q_raw,
            )
        )
    return differences


def _parse_amount(value: str) -> float:
    cleaned = (
        value.replace(",", "")
        .replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("₹", "")
        .replace("USD", "")
        .strip()
    )
    return float(cleaned)
