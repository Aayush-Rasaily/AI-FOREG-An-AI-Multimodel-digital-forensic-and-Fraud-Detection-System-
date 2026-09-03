# Phase 7F — System Administration, Monitoring & Operational Health

## Overview

Enterprise-grade operational management providing administrators visibility into system health, background processing, storage utilization, AI model availability, and application performance.

No forensic or AI analysis logic is modified.

## Architecture

```
health.py       →  service.py  →  system_admin API
metrics.py      →  service.py
jobs.py         →  service.py
storage.py      →  service.py
diagnostics.py  →  service.py  →  repository.py  →  SystemDiagnosticsRun ORM
monitoring.py   →  combined overview
```

## Modules

| File | Purpose |
|---|---|
| `health.py` | Service, database, Redis, resource health |
| `metrics.py` | Deterministic counters (evidence, cases, reports, etc.) |
| `jobs.py` | Background job aggregation across pipelines |
| `storage.py` | Storage backend utilization |
| `diagnostics.py` | Configuration, dependency, and infrastructure checks |
| `monitoring.py` | Combined operational overview |
| `service.py` | Application service layer |
| `repository.py` | Diagnostics run persistence |
| `schemas.py` | Pydantic API schemas |
| `policy.py` | Version constants, diagnostic check list |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/system/health` | Health snapshot |
| GET | `/system/metrics` | Operational metrics |
| GET | `/system/jobs` | Background job summary |
| GET | `/system/storage` | Storage utilization |
| GET | `/system/diagnostics` | Current diagnostics (non-persisted) |
| POST | `/system/diagnostics/run` | Run and persist diagnostics |

## Job Categories Monitored

- Extraction, AI, Fusion, Timeline, Correlation, Entity Resolution, Reports, Processing

## Diagnostic Checks

- Configuration validation
- Database connectivity
- Storage verification
- Migration verification
- AI model availability
- Queue health
- Cache verification
- Dependency checks

## Frontend

`SystemDashboardPage` at `/system` provides:

- Health cards (service, database, Redis, resources)
- Metrics panel
- Job monitor
- Storage usage
- Diagnostics with run button
- Refresh control

## Determinism

- Metrics are count-based queries with stable ordering
- Health snapshots use fixed field structure
- Diagnostics checks run in defined order
