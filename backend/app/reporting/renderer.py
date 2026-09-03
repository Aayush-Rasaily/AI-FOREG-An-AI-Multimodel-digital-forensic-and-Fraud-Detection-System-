"""Multi-format report renderer (JSON, Markdown, HTML). PDF is out of scope for 7D."""

from __future__ import annotations

import json
from typing import Any, Literal

from backend.app.reporting.provenance import SECTION_ORDER, canonical_json
from backend.app.reporting.templates import render_html_document

ReportFormat = Literal["json", "md", "html"]


def _md_heading(level: int, text: str) -> str:
    return f'{"#" * level} {text}\n\n'


def _md_kv(data: dict[str, Any]) -> str:
    lines = [f"- **{key}**: {value}" for key, value in data.items()]
    return "\n".join(lines) + ("\n\n" if lines else "\n")


def render_markdown(content: dict[str, Any]) -> str:
    """Render investigation report as Markdown."""

    sections = content.get("sections") or {}
    chunks: list[str] = [
        _md_heading(1, str(content.get("title") or "Investigation Report")),
        _md_kv(
            {
                "Report ID": content.get("report_id"),
                "Generated": content.get("generated_at"),
                "Engine": content.get("engine_version"),
                "Report version": content.get("report_version"),
                "Checksum": content.get("report_checksum"),
            }
        ),
    ]
    titles = {
        "case_summary": "Case Summary",
        "evidence_inventory": "Evidence Inventory",
        "metadata_summary": "Metadata Summary",
        "ocr_summary": "OCR Summary",
        "pattern_extraction_summary": "Pattern Extraction Summary",
        "timeline": "Timeline",
        "forensic_findings": "Forensic Findings",
        "evidence_comparison": "Evidence Comparison",
        "image_ai": "Image AI",
        "document_ai": "Document AI",
        "signature_ai": "Signature AI",
        "video_ai": "Video AI",
        "audio_ai": "Audio AI",
        "fusion_assessment": "Fusion Assessment",
        "correlation_summary": "Correlation Summary",
        "entity_graph_summary": "Entity Graph Summary",
        "overall_confidence": "Overall Confidence",
        "risk_assessment": "Risk Assessment",
        "conflicts": "Conflicts",
        "provenance_summary": "Provenance Summary",
        "chain_of_custody_summary": "Chain of Custody Summary",
        "appendix_raw_findings": "Appendix — Raw Findings",
    }
    for key in SECTION_ORDER:
        chunks.append(_md_heading(2, titles.get(key, key)))
        value = sections.get(key)
        if value is None:
            chunks.append("_Section unavailable (analysis not present)._\n\n")
            continue
        if isinstance(value, dict):
            summary = {
                k: (len(v) if isinstance(v, list) else v)
                for k, v in value.items()
                if k != "items"
            }
            chunks.append(_md_kv(summary))
            items = value.get("items")
            if isinstance(items, list):
                for item in items[:40]:
                    if isinstance(item, dict):
                        label = (
                            item.get("summary")
                            or item.get("display_name")
                            or item.get("description")
                            or item.get("correlation_type")
                            or item.get("canonical_id")
                            or json.dumps(item, sort_keys=True, default=str)
                        )
                        chunks.append(f"- {label}\n")
                    else:
                        chunks.append(f"- {item}\n")
                chunks.append("\n")
        elif isinstance(value, list):
            for item in value[:40]:
                chunks.append(f"- {item}\n")
            chunks.append("\n")
        else:
            chunks.append(f"{value}\n\n")
    return "".join(chunks)


def render_report(content: dict[str, Any], fmt: ReportFormat) -> tuple[bytes, str, str]:
    """Return (bytes, media_type, filename_suffix) for one format."""

    report_id = str(content.get("report_id") or "report")
    if fmt == "json":
        payload = canonical_json(content).encode("utf-8")
        return payload, "application/json", f"investigation-report-{report_id}.json"
    if fmt == "md":
        payload = render_markdown(content).encode("utf-8")
        return payload, "text/markdown; charset=utf-8", (
            f"investigation-report-{report_id}.md"
        )
    if fmt == "html":
        payload = render_html_document(content).encode("utf-8")
        return payload, "text/html; charset=utf-8", (
            f"investigation-report-{report_id}.html"
        )
    raise ValueError(f"Unsupported report format: {fmt}")
