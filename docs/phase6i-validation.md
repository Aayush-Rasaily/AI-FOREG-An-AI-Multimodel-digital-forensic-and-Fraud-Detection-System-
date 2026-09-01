# Phase 6I — End-to-End Validation & Production Hardening

## Objective

Phase 6I validates the complete Phase 6 architecture without adding new modalities or detection engines. It confirms the pipeline from evidence ingestion through report generation operates reliably, traceably, and with safe failure behavior.

## Validation Map

```
Evidence Upload
    ↓ SHA-256 + Custody
Processing / Extraction
    ↓
Forensic Analysis + Modality AI (6A–6E)
    ↓
Phase 6F Fusion + AI Jury
    ↓
Phase 6G Case Intelligence
    ↓
Phase 6H Forensic Report (immutable snapshot + PDF)
    ↓
Provenance / Audit Chain
```

## Validation Strategy

| Area | Approach |
|------|----------|
| E2E pipeline | API integration test through fusion → intelligence → report |
| Evidence integrity | SHA-256 unchanged after processing |
| Provenance | Report links case, fusion runs, evidence hashes |
| Determinism | Normalization dedup; report sections stable excluding timestamps/IDs |
| Versioning | Engine/policy version constants verified |
| Concurrency | Active duplicate job rejection (409 / ConflictError) |
| Idempotency | Repeat fusion/intelligence/report preserves history |
| API contracts | 404/422 structured errors, no tracebacks |
| Migrations | Linear Alembic chain 0001→0013 |
| Frontend safety | Partial/malformed API payloads do not crash panels |

## Failure Handling

- Domain errors use safe client messages (`FusionAnalysisError`, `CaseIntelligenceError`, `ReportingError`)
- Unexpected exceptions logged server-side; API returns generic safe codes
- Unavailable modalities never treated as fraud or clean evidence
- Incomplete reports cannot be downloaded

## Determinism Notes

Legitimately non-deterministic fields:

- UUIDs (`id`, `report_id`, `fusion_run_id`, etc.)
- Timestamps (`created_at`, `generated_at`, etc.)

Deterministic components:

- Finding normalization IDs
- Relationship deduplication ordering
- Report section structure for identical inputs
- Policy version constants

## Risk / Confidence Policy

Risk score, confidence, jury agreement, and evidence coverage are distinct metrics. Reports include an explicit `confidence_note` separating risk from confidence.

## Concurrency Behavior

Partial unique indexes prevent multiple active jobs per case/evidence:

- `processing_jobs` — `(evidence_id, job_type)` when QUEUED/RUNNING
- `case_intelligence_runs` — `(case_id)` when QUEUED/RUNNING
- `forensic_reports` — `(case_id)` when QUEUED/GENERATING

Application layer pre-checks plus `IntegrityError` catch for race safety.

## Test Suite

Backend: `tests/test_phase6i_validation_hardening.py` (16 tests)

Frontend: `frontend/src/test/phase6i.test.tsx` (2 tests)

## Known Limitations

- Performance baseline is observational via pytest duration, not formal benchmarking
- Large-file stress tests rely on existing upload limits in `Settings`
- PDF report format is text-based, not a styled legal template
- Windows-specific file locking is covered indirectly via existing storage tests

## Phase 7

Phase 7 was NOT started. Phase 6I is validation and hardening only.
