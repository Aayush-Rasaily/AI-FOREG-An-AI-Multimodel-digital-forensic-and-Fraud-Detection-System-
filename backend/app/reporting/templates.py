"""HTML templates for investigation reports (PDF-ready structure)."""

from __future__ import annotations

from html import escape
from typing import Any


def _section_html(title: str, body: str) -> str:
    return (
        f'<section class="report-section">'
        f"<h2>{escape(title)}</h2>"
        f"{body}"
        f"</section>"
    )


def _kv_table(data: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><th>{escape(str(key))}</th><td>{escape(str(value))}</td></tr>"
        for key, value in data.items()
    )
    return f'<table class="kv">{rows}</table>'


def _list_items(items: list[Any], *, empty: str = "None recorded.") -> str:
    if not items:
        return f"<p>{escape(empty)}</p>"
    lis = "".join(f"<li>{escape(str(item))}</li>" for item in items)
    return f"<ul>{lis}</ul>"


def render_html_document(content: dict[str, Any]) -> str:
    """Render a complete HTML investigation report document."""

    sections = content.get("sections") or {}
    title = str(content.get("title") or "Investigation Report")
    meta = {
        "Report ID": content.get("report_id"),
        "Generated": content.get("generated_at"),
        "Engine": content.get("engine_version"),
        "Report version": content.get("report_version"),
        "Checksum": content.get("report_checksum"),
    }
    parts: list[str] = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8"/>',
        f"<title>{escape(title)}</title>",
        "<style>"
        "body{font-family:Georgia,serif;margin:2rem;color:#111;line-height:1.45}"
        "h1{font-size:1.8rem}h2{font-size:1.25rem;margin-top:1.6rem;"
        "border-bottom:1px solid #ccc;padding-bottom:.3rem}"
        "table.kv{border-collapse:collapse;width:100%;margin:.5rem 0}"
        "table.kv th,table.kv td{border:1px solid #ddd;padding:.4rem .6rem;"
        "text-align:left;vertical-align:top}"
        "table.kv th{width:28%;background:#f6f6f6}"
        ".meta{color:#444;font-size:.95rem}"
        "</style></head><body>",
        f"<h1>{escape(title)}</h1>",
        f'<div class="meta">{_kv_table(meta)}</div>',
    ]

    title_map = {
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

    for key, heading in title_map.items():
        value = sections.get(key)
        if value is None:
            body = "<p>Section unavailable (analysis not present).</p>"
        elif isinstance(value, dict):
            body = _kv_table(
                {
                    k: (
                        len(v)
                        if isinstance(v, list)
                        else v
                    )
                    for k, v in value.items()
                    if k != "items"
                }
            )
            items = value.get("items")
            if isinstance(items, list) and items:
                preview = [
                    item.get("summary")
                    or item.get("display_name")
                    or item.get("description")
                    or item.get("correlation_type")
                    or item.get("canonical_id")
                    or item
                    for item in items[:25]
                ]
                body += _list_items(preview)
        elif isinstance(value, list):
            body = _list_items(value[:50])
        else:
            body = f"<p>{escape(str(value))}</p>"
        parts.append(_section_html(heading, body))

    parts.append("</body></html>")
    return "\n".join(parts)
