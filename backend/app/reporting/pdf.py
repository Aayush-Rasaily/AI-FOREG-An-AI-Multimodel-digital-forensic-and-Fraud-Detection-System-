"""Deterministic PDF generation for forensic reports."""

from __future__ import annotations

import io
from typing import Any

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _content_stream(lines: list[str]) -> bytes:
    commands: list[str] = ["BT", "/F1 10 Tf", "50 750 Td"]
    for index, line in enumerate(lines):
        if index > 0:
            commands.append("0 -14 Td")
        commands.append(f"({_pdf_escape(line)}) Tj")
    commands.append("ET")
    return "\n".join(commands).encode("ascii", errors="replace")


def _add_page(writer: PdfWriter, lines: list[str]) -> None:
    page = writer.add_blank_page(width=612, height=792)
    font = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font})}
    )
    content = DecodedStreamObject()
    content.set_data(_content_stream(lines))
    page[NameObject("/Contents")] = writer._add_object(content)


def _flatten_content(content: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.append(content.get("title", "Forensic Investigation Report"))
    lines.append(f"Report ID: {content.get('report_id', '—')}")
    lines.append(f"Version: {content.get('report_version', '—')}")
    lines.append(f"Generated: {content.get('generated_at', '—')}")
    lines.append("")

    sections = content.get("sections", {})
    summary = sections.get("executive_summary", {})
    if summary:
        lines.append("EXECUTIVE SUMMARY")
        lines.append(f"Case verdict: {summary.get('case_verdict', '—')}")
        lines.append(f"Risk score: {summary.get('risk_score', '—')}")
        lines.append(f"Confidence: {summary.get('confidence', '—')}")
        lines.append(f"Evidence count: {summary.get('evidence_count', 0)}")
        lines.append(f"Analyzed: {summary.get('analyzed_evidence', 0)}")
        lines.append(f"Not analyzed: {summary.get('not_analyzed_evidence', 0)}")
        lines.append("")

    inventory = sections.get("evidence_inventory", [])
    if inventory:
        lines.append("EVIDENCE INVENTORY")
        for item in inventory:
            lines.append(
                f"{item.get('evidence_number')} | {item.get('filename')} | "
                f"{item.get('coverage_status')} | "
                f"SHA-256: {item.get('sha256_hash', '')[:16]}..."
            )
        lines.append("")

    explainability = sections.get("explainability", {})
    if explainability:
        lines.append("EXPLAINABILITY")
        lines.append(str(explainability.get("why", ""))[:200])
        lines.append(explainability.get("jury_note", ""))
        lines.append("")

    limitations = sections.get("confidence_and_limitations", {}).get("limitations", [])
    if limitations:
        lines.append("LIMITATIONS")
        for item in limitations[:20]:
            lines.append(f"- {item}")

    return lines


def build_report_pdf(content: dict[str, Any]) -> bytes:
    """Render a simple text-based PDF from structured report content."""

    lines = _flatten_content(content)
    writer = PdfWriter()
    chunk_size = 45
    for start in range(0, max(len(lines), 1), chunk_size):
        _add_page(writer, lines[start : start + chunk_size])
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
