# Phase 7D — Investigation Report Generator

## Overview

Deterministic report generation engine that compiles outputs from Phases 1–7C into investigator-ready reports. No new analysis or AI inference is performed.

## Architecture

```
aggregation.py  →  builder.py  →  engine.py  →  service.py  →  API
                    ↓
               provenance.py
                    ↓
               renderer.py  →  JSON / Markdown / HTML
```

### Modules

| File | Purpose |
|---|---|
| `aggregation.py` | Collects evidence, fusion, forensics, custody, case intelligence, correlation, entity resolution, and timeline data into a stable snapshot |
| `builder.py` | Builds 22 deterministic report sections from the snapshot |
| `engine.py` | Orchestrates aggregation → build → provenance → checksum |
| `renderer.py` | Renders content to JSON, Markdown, or HTML |
| `templates.py` | HTML template rendering |
| `provenance.py` | Canonical JSON, checksum, provenance builder |
| `policy.py` | Engine and report version constants |
| `service.py` | Application service (queue, run, CRUD) |
| `repository.py` | Database persistence for `ForensicReport` |
| `schemas.py` | Pydantic API schemas |

## Report Sections (22)

1. `case_summary` — Case information and executive summary
2. `evidence_inventory` — All evidence items with status
3. `metadata_summary` — File metadata per evidence
4. `ocr_summary` — OCR/text extraction status
5. `pattern_extraction_summary` — Pattern detection counts
6. `timeline` — Investigation timeline events (Phase 7A)
7. `forensic_findings` — All forensic findings across evidence
8. `evidence_comparison` — Reference comparison results
9. `image_ai` — Image AI analysis results
10. `document_ai` — Document AI analysis results
11. `signature_ai` — Signature verification results
12. `video_ai` — Video AI analysis results
13. `audio_ai` — Audio AI analysis results
14. `fusion_assessment` — Multimodal fusion verdicts and jury assessments
15. `correlation_summary` — Cross-evidence correlations (Phase 7B)
16. `entity_graph_summary` — Entity resolution graph (Phase 7C)
17. `overall_confidence` — Aggregate confidence assessment
18. `risk_assessment` — Risk scoring and verdict
19. `conflicts` — Contradictions and conflicts
20. `provenance_summary` — Analysis run IDs and evidence hashes
21. `chain_of_custody_summary` — Custody events per evidence
22. `appendix_raw_findings` — Raw analysis summaries

## Determinism

- All sections built from a frozen snapshot (no side effects)
- `generated_at` excluded from checksum calculation
- `canonical_json()` uses sorted keys and compact separators
- Same inputs always produce the same `report_checksum`

## Report Metadata

Each report includes:

- **Report ID** — UUID
- **Case ID** — Reference to parent case
- **Generated timestamp** — ISO 8601
- **Engine version** — `policy.ENGINE_VERSION`
- **Report version** — `policy.REPORT_VERSION`
- **Evidence hashes** — SHA-256 of all evidence at time of generation
- **Included analysis run IDs** — Fusion, correlation, entity, timeline, case intelligence
- **Report checksum** — SHA-256 of deterministic content

## Output Formats

| Format | Media Type | Notes |
|---|---|---|
| JSON | `application/json` | Canonical, sorted keys |
| Markdown | `text/markdown` | Human-readable with section headings |
| HTML | `text/html` | Styled document, PDF-ready structure |
| PDF | `application/pdf` | Generated via `pdf.py` (pypdf) |

## API

| Method | Path | Description |
|---|---|---|
| POST | `/cases/{case_id}/reports` | Queue report generation |
| GET | `/cases/{case_id}/reports` | List reports for a case |
| GET | `/cases/{case_id}/reports/latest` | Get latest report detail |
| GET | `/reports/{report_id}` | Get one report detail |
| GET | `/reports/{report_id}/status` | Get generation status |
| GET | `/reports/{report_id}/download?format=json` | Download JSON |
| GET | `/reports/{report_id}/download?format=md` | Download Markdown |
| GET | `/reports/{report_id}/download?format=html` | Download HTML |
| GET | `/reports/{report_id}/download` | Download PDF (default) |

## Frontend

The `ReportPanel` component provides:

- Generate report button
- Status badges (QUEUED, GENERATING, COMPLETED, FAILED)
- Download buttons for JSON, Markdown, HTML
- Expandable section previews
- Checksum display
- Report history list

Integrated into the Investigation Workspace as the "Report" tab.

## Limitations

- PDF generation uses basic text layout (pypdf)
- Sections for unavailable analyses show `{ available: false }`
- No re-analysis; reports reflect data at time of generation
