# Phase 9G — Investigation Analytics & Operational Metrics

Deterministic operational analytics for investigators and administrators.
Aggregates persisted investigation data only — **no forecasting** and
**no machine learning**.

## Architecture

```
Cases · Evidence · AI runs · Fusion · Timeline · Correlations
Knowledge Graph · Decision Support · Case Review · Integrity
Processing · Reports · Audit · Users
        ↓
Aggregation (SQL counts / averages)
        ↓
Metrics · Dashboard sections · Trend series
        ↓
Persist (analytics_* tables)
```

## Metrics

| Key | Description |
|-----|-------------|
| cases_opened | Total cases |
| cases_completed | COMPLETED + ARCHIVED |
| cases_in_progress | OPEN / IN_PROGRESS / ON_HOLD |
| evidence_processed | Evidence row count |
| ai_analyses_completed | Image+document+video+audio analysis runs |
| fusion_runs | Fusion analysis runs |
| timeline_events | Timeline event records |
| correlation_counts | Evidence correlations |
| knowledge_graph_size | Graph entities |
| workflow_completion_pct | Avg decision-support workflow_completion |
| review_completion_pct | Avg case-review review_completion_pct |
| integrity_alerts | Integrity alert rows |
| processing_duration_seconds_avg | Avg completed processing job duration |
| reports_generated | Forensic reports |
| user_activity | Audit event count |
| storage_usage_bytes | Sum of evidence.file_size |
| queue_utilization | Active (QUEUED/RUNNING) / total processing jobs |

## Persistence

Migration: `20260913_0032_add_investigation_analytics.py`

Tables: `analytics_runs`, `analytics_snapshots`, `analytics_metrics`,
`analytics_dashboards`

## API

| Method | Path |
|--------|------|
| POST | `/analytics/refresh` |
| GET | `/analytics` |
| GET | `/analytics/dashboard` |
| GET | `/analytics/cases` |
| GET | `/analytics/evidence` |
| GET | `/analytics/ai` |
| GET | `/analytics/workflow` |
| GET | `/analytics/integrity` |
| GET | `/analytics/export` |

Permissions: `analytics.run` · `analytics.view`

`GET /analytics` returns the latest persisted run, or a live non-persisted
compute if none exists. `POST /analytics/refresh` always persists a new run.

Trends are built from prior snapshot payloads (deterministic history), not
predictions.

## Frontend

Sidebar **Analytics** (`/analytics`): KPI cards, trend charts, case/AI/workflow/
evidence/integrity sections, JSON export.

## Limitations

- SQLite/Postgres epoch extract for processing duration may differ slightly by dialect.
- Empty databases yield zeros; live GET without refresh is not persisted.
- Does not replace Phase 8 monitoring dashboards (system health / bottlenecks).
