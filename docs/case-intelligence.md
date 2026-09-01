# Phase 6G — Case-Level Forensic Intelligence

## Architecture

Phase 6G aggregates **Phase 6F evidence-level fusion** results across all evidence in a case.

```
Case → Evidence A/B/C… → Phase 6F Fusion → Case Aggregation → Relationships → Consistency → Conflicts → Risk Policy → Case Assessment
```

Package: `backend/app/case_intelligence/`

## Evidence aggregation

`aggregation.py` loads the latest `FusionAnalysisRun` per evidence item via `FusionRepository`. Missing fusion is recorded as `not_analyzed`, never as clean.

## Evidence coverage

`coverage.py` tracks analyzed, not analyzed, inconclusive, insufficient, unavailable, failed, supporting, and contradictory counts.

## Relationship detection

`relationships.py` only reports relationships supported by existing data:

- Duplicate SHA-256 hash
- Comparison runs
- Signature verification runs
- Shared metadata (creator/author when present)
- Shared normalized evidence number

## Case risk policy

`policy.py` (`ENGINE_VERSION=1.0`, `POLICY_VERSION=1.0`):

- Does not average risk scores blindly
- Weights suspicious evidence by risk × confidence
- Boosts risk when multiple evidence items are suspicious
- Applies conflict penalty
- Unavailable/inconclusive evidence does not increase fraud risk
- Weak evidence cannot dominate strong contradictory evidence

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/cases/{case_id}/intelligence` | Queue case synthesis (202) |
| GET | `/api/v1/cases/{case_id}/intelligence` | List runs |
| GET | `/api/v1/cases/{case_id}/intelligence/latest` | Latest assessment |
| GET | `/api/v1/case-intelligence/{analysis_id}` | One run |
| GET | `/api/v1/cases/{case_id}/relationships` | Relationships |
| GET | `/api/v1/cases/{case_id}/conflicts` | Conflicts |
| GET | `/api/v1/cases/{case_id}/timeline` | Timeline |

## Database

Migration `20260831_0012_add_case_intelligence.py` adds case intelligence runs, participations, relationships, conflicts, and timeline events.

## Provenance

Case assessment provenance links to evidence IDs, fusion run IDs, policy version, and case metadata.

## Limitations

- Synthesis requires Phase 6F fusion for full evidence-level detail
- Relationship detection is conservative; no inferred links without source records
- Timeline only includes timestamps present in evidence/custody/fusion metadata
