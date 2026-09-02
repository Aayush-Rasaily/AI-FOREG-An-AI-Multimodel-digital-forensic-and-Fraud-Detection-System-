# Phase 7A — Investigation Timeline Engine

## Objective

Phase 7A introduces a deterministic investigation timeline that reconstructs chronological events across case evidence while preserving provenance and chain of custody. It extends the completed Phase 6 architecture without replacing existing analyzers or case intelligence synthesis.

## Architecture

```
Evidence / Custody / Processing / AI / Fusion / Reports
                    ↓
           TimelineEngine.build()
                    ↓
      Normalization → Confidence → Ordering → Conflict Detection
                    ↓
         InvestigationTimeline (run)
                    ↓
      timeline_events + timeline_conflicts
                    ↓
              Timeline API
                    ↓
            TimelinePanel (UI)
```

### Backend module

| File | Role |
|------|------|
| `backend/app/timeline/engine.py` | Collect events from persisted sources |
| `backend/app/timeline/normalization.py` | UTC normalization, timezone handling |
| `backend/app/timeline/confidence.py` | Deterministic confidence scoring |
| `backend/app/timeline/ordering.py` | Deterministic event ordering |
| `backend/app/timeline/provenance.py` | Provenance payload builders |
| `backend/app/timeline/service.py` | Queue/run/persist timeline reconstruction |
| `backend/app/timeline/repository.py` | Database access |

### Persistence

| Table | Purpose |
|-------|---------|
| `investigation_timelines` | One timeline reconstruction run per case history entry |
| `timeline_events` | Chronological events with normalized timestamps |
| `timeline_conflicts` | Detected timestamp inconsistencies |

Migration: `20260901_0014_add_timeline.py`

## Event Sources

The engine reuses existing persisted data only:

- Evidence registration and updates
- Processing jobs and extraction records
- Chain of custody events
- Forensic and modality AI runs (image, document, signature, video, audio)
- Fusion analysis runs
- Case intelligence runs
- Forensic reports
- Extracted metadata timestamps (EXIF, filesystem, document)

Nothing is fabricated. Missing timestamps are represented as `timestamp_missing` events.

## Confidence Policy

| Source | Base confidence |
|--------|-----------------|
| Signed document timestamp | 0.98 |
| Filesystem timestamp | 0.95 |
| Camera EXIF | 0.90 |
| Processing / custody | 0.85 |
| Fusion / case intelligence / report | 0.80 |
| Modality AI | 0.75 |
| Manual investigator note | 0.60 |
| Unknown metadata | 0.30 |

Deductions:

- Missing timezone: −0.10
- Naive timestamp: −0.05

## Ordering

Events are sorted deterministically by:

1. `normalized_timestamp` (missing timestamps last)
2. Confidence (descending)
3. Source priority
4. `event_id` (UUID tie-breaker)

## Conflict Detection

| Conflict type | Trigger |
|---------------|---------|
| `multiple_timestamps` | Multiple metadata timestamps for one artifact |
| `filesystem_before_exif` | Filesystem time precedes EXIF capture time |
| `future_timestamp` | Event timestamp is in the future |
| `clock_drift` | Extreme spread across evidence timestamps |
| `timezone_mismatch` | Conflicting timezones on same evidence |
| `duplicate_event` | Duplicate event IDs detected |

Conflicts are persisted and exposed via API. They are never silently discarded.

## Provenance

Each event includes provenance references to upstream records such as:

- `evidence_id`
- `sha256_hash`
- `processing_job_id`
- `fusion_run_id`
- `case_intelligence_run_id`
- `report_id`
- `custody_event_id`

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/v1/cases/{case_id}/timeline` | Queue timeline reconstruction |
| GET | `/api/v1/cases/{case_id}/timeline` | List timeline history |
| GET | `/api/v1/cases/{case_id}/timeline/latest` | Latest timeline with events |
| GET | `/api/v1/timeline/{timeline_id}` | One timeline run |
| GET | `/api/v1/timeline/{timeline_id}/conflicts` | Timeline conflicts |

Case intelligence timeline (Phase 6G) remains available at:

- `GET /api/v1/cases/{case_id}/intelligence/timeline`

## Concurrency

Partial unique index on `investigation_timelines` prevents multiple active (`QUEUED`/`RUNNING`) reconstructions per case. Repeat completed runs are allowed and preserved in history.

## Known Limitations

- Metadata timestamps depend on what prior processing/extraction persisted
- Media-local audio/video timelines remain separate per-analysis endpoints
- Performance baseline not formally benchmarked
- Phase 7B cross-evidence correlation not started

## Phase 7B

Phase 7B (Cross-Evidence Correlation) was **not** started.
