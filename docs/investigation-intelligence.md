# Investigation Intelligence & Case Narrative (Phase 8C)

Phase 8C adds a deterministic investigation intelligence layer that
synthesizes **already persisted** evidence, forensic findings, AI/fusion
outputs, timelines, correlations, entity graphs, reports, custody, and
audit-linked case metadata into an explainable case narrative.

It does **not** modify or re-run detectors, extractors, fusion, timeline,
correlation, entity, reporting, or monitoring engines.

## Architecture

```
InvestigationIntelligenceService
        │
        ▼
InvestigationIntelligenceEngine
  Collect → Normalize → Prioritize → Summarize
        → Narrative → Recommendations → Persist
```

Collection reuses `reporting.aggregation.aggregate_report_data`, which
reads only stored rows (same approach as Phase 6H reports).

## API paths

Phase 6G already owns `/cases/{id}/intelligence`. Phase 8C therefore
exposes:

| Method | Path |
| --- | --- |
| `POST` | `/api/v1/cases/{case_id}/investigation-summaries` |
| `GET` | `/api/v1/cases/{case_id}/investigation-summaries` |
| `GET` | `/api/v1/cases/{case_id}/investigation-summaries/latest` |
| `GET` | `/api/v1/investigation-summaries/{summary_id}` |

## Pipeline

1. **Collect** — case, evidence, findings, fusion, case intelligence,
   timeline, correlation, entity graph snapshots
2. **Normalize** — stable sort keys for deterministic output
3. **Prioritize** — severity-ranked key findings
4. **Summarize** — overview, timeline, correlations, AI/fusion
5. **Narrative** — section paragraphs, each with provenance links
6. **Recommendations** — deterministic next steps
7. **Persist** — `investigation_summaries` row

## Scoring & confidence

Overall risk: `low` / `medium` / `high` / `critical` from peak fusion
risk scores, case-intelligence risk, and finding severity.

Overall confidence: integer `0–100` from coverage, agreement, analysis
completeness, finding confidence, fusion confidence, and a missing-analysis
penalty.

## Narrative & provenance

Every paragraph stores:

`evidence_ids`, `finding_ids`, `fusion_ids`, `timeline_ids`,
`correlation_ids`, `entity_ids`, `report_ids`, `audit_ids`

No LLMs. No fabricated conclusions. Identical inputs produce identical
section content (timestamps/IDs differ per generation).

## Recommendations

Examples: complete missing analyses, obtain higher resolution, verify
signature manually, interview document source, recover metadata, collect
reference recording, acquire CCTV, review correlations, export report.

## Persistence

Table `investigation_summaries` (migration `20260903_0022`).

## Frontend

Investigation Workspace **Summary** tab → `InvestigationSummaryPanel`.

## Limitations

- Reads stored outputs only; gaps in prior analysis remain gaps.
- Path namespace differs from Phase 6G `/intelligence` to preserve compatibility.
- Does not replace court-ready Phase 6H PDF reports.
