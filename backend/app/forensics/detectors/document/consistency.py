"""Document field consistency detector."""

import asyncio
import io
import re
from datetime import datetime

from pypdf import PdfReader

from backend.app.domain.processing import EvidenceClassification
from backend.app.forensics.models import (
    AnalysisContext,
    DetectorResult,
    FindingCategory,
    FindingItem,
    Severity,
)

TOTAL_PATTERN = re.compile(r"total[\s:]*([\d,]+\.\d{2})", re.I)
LINE_ITEM_PATTERN = re.compile(r"\b(\d+\.\d{2})\b")
CURRENCY_MARKERS = ("$", "€", "£", "USD")


class ConsistencyDetector:
    """Validate dates, currency, totals, and duplicate fields in documents."""

    name = "consistency"
    version = "1.0"

    def can_analyze(self, context: AnalysisContext) -> bool:
        extension = context.original_filename.rsplit(".", 1)[-1].lower()
        return (
            context.classification == EvidenceClassification.DOCUMENT
            and extension in {"pdf", "txt", "csv"}
        )

    async def analyze(self, context: AnalysisContext) -> DetectorResult:
        max_bytes = context.settings.max_upload_size_mb * 1024 * 1024
        async with context.storage.open(context.storage_key) as stream:
            data = await asyncio.to_thread(stream.read, max_bytes + 1)
        text = await asyncio.to_thread(_extract_text, data, context.original_filename)
        findings = await asyncio.to_thread(_analyze_text, text)
        return DetectorResult(
            detector=self.name,
            version=self.version,
            findings=tuple(findings),
            metadata={"text_length": len(text)},
        )


def _extract_text(data: bytes, filename: str) -> str:
    extension = filename.rsplit(".", 1)[-1].lower()
    if extension == "pdf":
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return data.decode("utf-8", errors="replace")


def _normalize_amount(value: str) -> float:
    cleaned = value.replace(",", "")
    for marker in CURRENCY_MARKERS:
        cleaned = cleaned.replace(marker, "")
    return float(cleaned)


def _analyze_text(text: str) -> list[FindingItem]:
    findings: list[FindingItem] = []
    date_pattern = re.compile(
        r"\b(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})\b",
    )
    currency_pattern = re.compile(r"[$€£]\s?[\d,]+\.\d{2}|\bUSD\s?[\d,]+\.\d{2}")
    number_pattern = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b")
    dates: list[tuple[int, int, int]] = []
    for match in date_pattern.finditer(text):
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
        if month < 1 or month > 12 or day < 1 or day > 31:
            findings.append(
                FindingItem(
                    detector="consistency",
                    category=FindingCategory.DATE,
                    severity=Severity.HIGH,
                    confidence=0.95,
                    description="Impossible calendar date detected.",
                    explanation=(
                        f"Parsed date components: day={day}, month={month}, year={year}"
                    ),
                    metadata={"raw": match.group(0)},
                )
            )
            continue
        try:
            datetime(year, month, day)
            dates.append((year, month, day))
        except ValueError:
            findings.append(
                FindingItem(
                    detector="consistency",
                    category=FindingCategory.DATE,
                    severity=Severity.HIGH,
                    confidence=0.95,
                    description="Invalid calendar date detected.",
                    explanation=(
                        f"Date '{match.group(0)}' does not exist on the calendar."
                    ),
                    metadata={"raw": match.group(0)},
                )
            )
    if len(dates) >= 2 and dates[0] > dates[-1]:
        findings.append(
            FindingItem(
                detector="consistency",
                category=FindingCategory.DATE,
                severity=Severity.MEDIUM,
                confidence=0.8,
                description="Issue date appears after a later referenced date.",
                explanation=(
                    "First parsed date occurs chronologically after a later date."
                ),
                metadata={"first_date": dates[0], "later_date": dates[-1]},
            )
        )
    currencies = currency_pattern.findall(text)
    plain_numbers = number_pattern.findall(text)
    formats = {
        "currency" if value.startswith(CURRENCY_MARKERS) else "plain"
        for value in plain_numbers
    }
    if currencies and len(formats) > 1:
        findings.append(
            FindingItem(
                detector="consistency",
                category=FindingCategory.NUMBER,
                severity=Severity.LOW,
                confidence=0.75,
                description="Mixed currency and plain number formatting detected.",
                explanation=(
                    "Document uses inconsistent monetary and numeric formatting."
                ),
                metadata={"currency_hits": len(currencies)},
            )
        )
    totals = [_normalize_amount(value) for value in TOTAL_PATTERN.findall(text)]
    line_items = [
        float(value.replace(",", "")) for value in LINE_ITEM_PATTERN.findall(text)
    ]
    if totals and line_items:
        computed = round(sum(line_items[: min(len(line_items), 20)]), 2)
        declared = totals[0]
        if abs(computed - declared) > max(1.0, declared * 0.05):
            findings.append(
                FindingItem(
                    detector="consistency",
                    category=FindingCategory.NUMBER,
                    severity=Severity.HIGH,
                    confidence=0.85,
                    description="Declared total differs from summed line amounts.",
                    explanation=(
                        f"Declared total {declared:.2f} vs computed sum {computed:.2f}."
                    ),
                    metadata={"declared_total": declared, "computed_total": computed},
                )
            )
    duplicate_fields = _duplicate_lines(text)
    for line in duplicate_fields[:3]:
        findings.append(
            FindingItem(
                detector="consistency",
                category=FindingCategory.OTHER,
                severity=Severity.LOW,
                confidence=0.7,
                description="Duplicate field line detected.",
                explanation=f"Repeated line: {line[:120]}",
                metadata={"line": line},
            )
        )
    return findings


def _duplicate_lines(text: str) -> list[str]:
    counts: dict[str, int] = {}
    for line in text.splitlines():
        normalized = line.strip()
        if len(normalized) < 8:
            continue
        counts[normalized] = counts.get(normalized, 0) + 1
    return [line for line, count in counts.items() if count >= 2]
