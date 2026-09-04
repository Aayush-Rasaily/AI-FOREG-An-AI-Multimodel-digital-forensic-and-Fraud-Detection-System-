# Monitoring, Audit Analytics & Operational Intelligence (Phase 8D)

Phase 8D adds a deterministic operational monitoring layer for AI-Forge.
It aggregates **persisted** processing, AI, investigation, audit, and
report data into health assessments, KPIs, and an operational dashboard.

It does **not** modify Phase 7F `/system/*` endpoints or analysis engines.

## Architecture

```
MonitoringService
    └── MonitoringEngine.compute()
          ├── analytics (processing / AI / investigation KPIs)
          ├── audit (user activity / API usage proxies)
          └── health assessment
    └── refresh() persists:
          monitoring_snapshots
          audit_statistics
          system_health_records
```

## Health policy

Status values: `HEALTHY` | `WARNING` | `DEGRADED` | `CRITICAL`

Derived from:

- processing failure rate
- AI modality failure rate
- API 5xx rates (when present in audit metadata)
- queue backlog (queued + running jobs)
- unavailable AI modalities

Thresholds live in `backend/app/monitoring/policy.py`.

## KPI definitions

| KPI | Source |
| --- | --- |
| Average processing time | `ProcessingJob.started_at` → `completed_at` |
| Average AI runtime | `InferenceJob.latency_ms` / run timestamps |
| Average report generation | `ForensicReport` timing |
| Average fusion / correlation | respective run timestamps |
| P95 latency | nearest-rank percentile over measured durations |
| Success / failure / retry rates | processing job status + attempt counts |

## Audit metrics

Derived from `audit_events` only (no credentials/secrets stored):

- busiest investigators / cases
- inactive investigations (`updated_at` older than 14 days)
- operation and category counts
- API usage proxies via operation names
- recent activity feed

HTTP request latency is **not** persisted by middleware; API latency is
`null` unless audit metadata includes status/latency fields.

## Refresh process

`POST /api/v1/monitoring/refresh` recomputes aggregates and writes one
snapshot + health record + audit statistics row. Subsequent GETs return
the latest snapshot when present; otherwise they compute live.

## API endpoints

| Method | Path |
| --- | --- |
| GET | `/api/v1/monitoring/dashboard` |
| GET | `/api/v1/monitoring/system-health` |
| GET | `/api/v1/monitoring/processing` |
| GET | `/api/v1/monitoring/ai` |
| GET | `/api/v1/monitoring/api` |
| GET | `/api/v1/monitoring/activity` |
| GET | `/api/v1/monitoring/bottlenecks` |
| GET | `/api/v1/monitoring/audit-summary` |
| POST | `/api/v1/monitoring/refresh` |

Permission: `system.monitor`.

## Migration

`20260904_0023_add_monitoring.py` (spec’s `20260901_0016` already used
by entity resolution).

## Frontend

Route `/monitoring` → Monitoring Dashboard (health, processing, AI, cases,
reports, API usage, audit analytics, activity, bottlenecks, trends).

## Determinism

Identical persisted inputs produce identical metric values and ordered
lists. No LLMs and no fabricated metrics.
