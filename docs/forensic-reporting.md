# Phase 6H — Forensic Investigation Reporting

## Architecture

Phase 6H transforms structured forensic results from Phases 6A–6G into stable, auditable investigation reports.

```
Case + Evidence → Aggregation → Report Builder → PDF + Snapshot → API
```

Package: `backend/app/reporting/`

## Report snapshot

Each generated report stores an immutable JSON snapshot including:

- Case metadata
- Evidence inventory and SHA-256 hashes
- Forensic findings summaries
- Phase 6F fusion and jury assessments
- Phase 6G case intelligence (when available)
- Explainability, limitations, and provenance

Later case changes do not alter completed reports.

## Report generation

1. `POST /api/v1/cases/{case_id}/reports` queues generation (202)
2. Background task aggregates data and builds structured sections
3. Deterministic PDF rendered via `pypdf`
4. PDF stored with SHA-256 integrity hash

## Report sections

Sections are included only when underlying data exists:

- Case information
- Executive summary
- Evidence inventory and integrity
- Modality analysis summaries
- Multimodal jury assessment (AI-generated)
- Case-level intelligence
- Relationships, conflicts, timeline
- Risk assessment and limitations
- Provenance / chain of custody
- Technical appendix

## Explainability

Structured answers for:

- Why (verdict rationale from case intelligence)
- Supporting/contradictory findings
- Conflicts and uncertainties
- Limitations from existing analysis states

Risk score and confidence are labeled separately.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/cases/{case_id}/reports` | Queue report (202) |
| GET | `/api/v1/cases/{case_id}/reports` | List reports |
| GET | `/api/v1/cases/{case_id}/reports/latest` | Latest report |
| GET | `/api/v1/reports/{report_id}` | One report |
| GET | `/api/v1/reports/{report_id}/status` | Status |
| GET | `/api/v1/reports/{report_id}/download` | PDF download |

## Database

Migration `20260831_0013_add_forensic_reports.py` adds `forensic_reports`.

## Limitations

- Report quality depends on available fusion and case intelligence runs
- PDF is text-based and deterministic; not a styled legal template
- Hash re-verification of evidence files is not performed during generation
