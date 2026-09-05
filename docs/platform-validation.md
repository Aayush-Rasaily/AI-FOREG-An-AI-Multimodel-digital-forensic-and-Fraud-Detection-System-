# Investigation Platform Validation (Phase 9H)

## Validation Architecture

Phase 9H adds a **deterministic, read-only** platform readiness framework under
`backend/app/platform_validation/`. It consolidates checks across migrations,
ORM metadata, API route registration, OpenAPI generation, evidence/custody,
AI module imports, timeline/correlation/knowledge graph, investigation
intelligence, workflow, case review, integrity monitoring, analytics, reports,
audit logging, configuration, and storage accessibility.

Validation **never mutates investigation data** and **never re-runs AI models**.
Results are explainable (per-check status + message + details) and optionally
persisted for auditability.

```
POST /platform/validate
        │
        ▼
PlatformValidationService.validate()
        │
        ▼
PlatformValidationEngine.plan()
        │
        ├── migration_checker
        ├── consistency (ORM / tables)
        ├── api_checker + OpenAPI
        ├── compatibility (module imports + versions)
        ├── configuration / storage (read-only)
        └── scoring → readiness level
        │
        ▼
Persist runs / results / issues
```

Distinct from Phase 8G `/system/readiness` and `/system/validate` (deployment
ops). Phase 9H uses the `/platform/*` namespace and `platform_validation_*`
tables.

## Compatibility Rules

| Rule | Behavior |
|------|----------|
| Additive only | New tables/APIs; no regression of Phases 1–9G |
| Expected migration head | Must equal `EXPECTED_MIGRATION_HEAD` (`20260914_0033`) |
| Down revision | Platform validation revises `20260913_0032` (analytics) |
| Required API paths | Catalog in `policy.REQUIRED_API_PATHS` must be registered |
| OpenAPI | Schema must generate with `info` and non-empty `paths` |
| Module imports | ORM symbols must import; no inference jobs started |
| Engine versions | Integrity `9f.x`, Analytics `9g.x`, Validation `9h.x` reported |

## Readiness Criteria

| Level | Condition |
|-------|-----------|
| `READY` | All checks `PASS` |
| `DEGRADED` | One or more `WARN`, zero `FAIL` |
| `NOT_READY` | Any `FAIL` |

**Score** = average of weights (`PASS=1.0`, `WARN=0.5`, `FAIL=0.0`) × 100.

## Health Metrics

Health reports include:

- readiness score and level
- pass / warn / fail / total counts
- category rollups (migrations, api, orm, evidence, ai, …)
- engine / policy versions
- flags: `ai_rerun=false`, `data_mutation=false`

## REST API

| Method | Path | Permission |
|--------|------|------------|
| POST | `/platform/validate` | `platform_validation.run` |
| GET | `/platform/validation` | `platform_validation.view` |
| GET | `/platform/validation/latest` | `platform_validation.view` |
| GET | `/platform/validation/{run_id}` | `platform_validation.view` |
| GET | `/platform/readiness` | `platform_validation.view` |
| GET | `/platform/health/report` | `platform_validation.view` |

## Persistence

Migration: `20260914_0033_add_platform_validation.py`

Tables:

- `platform_validation_runs`
- `platform_validation_results`
- `platform_validation_issues`

## Frontend

Navigation: **Platform Health** → `/platform-health`

Panels: readiness summary, validation results, issue viewer, health report,
compatibility panel.

## Limitations

- Does not replace Phase 8G deployment readiness or live infra probes (Redis,
  disk thresholds).
- Storage check is **read-only** (no write probes) to honor no-mutation.
- Does not execute forensic pipelines, integrity case scans, or analytics
  refreshes — only verifies modules/tables/APIs exist and are consistent.
- OpenAPI validation uses in-process schema generation; it does not require
  `/openapi.json` to be publicly enabled in production.
