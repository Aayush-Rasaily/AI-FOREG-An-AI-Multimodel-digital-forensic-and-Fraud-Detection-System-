# Phase 9F — Digital Evidence Integrity Monitoring

Deterministic continuous verification of evidence integrity across the
investigation lifecycle. Extends—does not replace—chain of custody, audit
logging, validation, and evidence management.

## Architecture

```
Evidence · Custody · Audit · Storage · AI artifacts · Reports
        ↓
Integrity Engine (collect existing outputs only)
        ↓
Verifier (hash / size / MIME / custody / provenance / …)
        ↓
Drift detector (vs prior monitor fingerprints)
        ↓
Alerts + Timeline + Metrics
        ↓
Persist (integrity_* tables)
```

**Never** re-runs AI models and **never** modifies evidence automatically.

## Checks

| Code | Purpose |
|------|---------|
| SHA256_CONSISTENCY | Custody hashes vs registered evidence hash |
| FILE_SIZE_CONSISTENCY | Storage object size vs registered size |
| MIME_CONSISTENCY | MIME present on evidence record |
| METADATA_DRIFT | Fingerprint change vs prior run |
| TIMESTAMP_CONSISTENCY | created_at / updated_at ordering |
| CUSTODY_CONTINUITY | Custody events present and monotonic |
| STORAGE_LOCATION | Storage key resolvable / object present |
| DUPLICATE_DETECTION | Duplicate SHA-256 within case snapshot |
| MISSING_PROVENANCE | Core provenance fields present |
| MISSING_AUDIT | Audit events reference evidence |
| MISSING_AI_ARTIFACTS | Stored AI findings present (advisory) |
| MISSING_REPORTS | Forensic reports present (advisory) |

## Persistence

Migration: `20260912_0031_add_integrity_monitoring.py`

Tables: `integrity_monitor_runs`, `integrity_checks`, `integrity_alerts`,
`integrity_drift_records`

## API

| Method | Path |
|--------|------|
| POST | `/cases/{case_id}/integrity-check` |
| GET | `/cases/{case_id}/integrity` |
| GET | `/cases/{case_id}/integrity/latest` |
| GET | `/cases/{case_id}/integrity/preview` |
| GET | `/cases/{case_id}/integrity/alerts` |
| GET | `/cases/{case_id}/integrity/drift` |
| GET | `/cases/{case_id}/integrity/history` |
| GET | `/integrity/{run_id}` |

Permissions: `integrity.run` · `integrity.view`

Preview validates without persistence. POST creates a new run each time and
uses the prior run’s fingerprints as the drift baseline.

## Deterministic Design

- Check / alert / drift keys are SHA-256 digests of stable inputs.
- Evidence and related IDs are sorted lexicographically.
- Scoring is a pure function of check and alert outcomes.
- Engine version `9f.1.0` · policy version `1.0`.

## Limitations

- Storage size/hash recomputation requires a configured storage backend; when
  unavailable, storage checks are `SKIP` (not auto-fail).
- Missing AI artifacts / reports are informational or warnings, not legal
  findings.
- Does not replace Phase 7E audit integrity endpoints.

## Frontend

Workspace tab **Integrity** shows dashboard metrics, alerts, drift viewer,
integrity timeline, and verification history with empty/loading/error states.
