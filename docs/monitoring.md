# Observability & Monitoring (Phase 10B)

Production observability for AI-Forge: Prometheus metrics, readiness probes,
structured JSON logging enrichment, and optional OpenTelemetry instrumentation.

**No forensic / AI / investigation logic changes** — instrumentation only.

Phase 8D KPI dashboards under `/api/v1/monitoring/*` remain unchanged.
Phase 10B adds infrastructure telemetry beside them.

## Architecture

```
backend/app/monitoring/
  metrics.py       KPI helpers + Prom recording re-exports
  prometheus.py    Registry + /metrics exposition
  tracing.py       OpenTelemetry setup (optional)
  health.py        Readiness aggregation for /health/ready
  logging.py       case/evidence/user/trace context vars
  telemetry.py     Bootstrap wiring

deployment/compose/docker-compose.monitoring.yml
  Prometheus · Grafana · Loki · Promtail

deployment/monitoring/grafana/dashboards/
  api · ai · processing · database · system
```

## Metrics

Expose Prometheus text:

| Path | Auth |
| --- | --- |
| `GET /metrics` | Public (root scrape) |
| `GET /api/v1/metrics` | Public |

Tracked series (prefix `ai_forge_`):

- HTTP requests / latency
- AI execution, processing, OCR, video, audio, fusion, correlation, report durations
- Queue length
- DB query + Redis op counters
- Process memory / CPU gauges
- GPU availability
- Model load counters

Recording helpers:

```python
from backend.app.monitoring.metrics import (
    observe_domain_duration,
    observe_request,
    set_queue_length,
    record_model_load,
)
```

## Health endpoints

| Path | Purpose |
| --- | --- |
| `GET /api/v1/health` | App + DB health (existing) |
| `GET /api/v1/health/live` | Liveness (existing) |
| `GET /api/v1/health/ready` | **New** readiness: DB, Redis, storage, AI engines, disk, memory |

Also retained: `/api/v1/system/liveness` and `/api/v1/system/readiness` (Phase 8G).

## Structured logging

JSON logs (existing `JsonFormatter`) now include when available:

- `request_id`
- `case_id` / `evidence_id` (from URL path)
- `user_id` (from `request.state.user` when set)
- `duration_ms` / `status_code` / `method` / `path`
- `trace_id` (OpenTelemetry, when tracing enabled)
- `exception` (on errors)

## OpenTelemetry

Disabled by default (no behavioral change / no exporter noise).

Enable with:

```bash
export AI_FORGE_ENABLE_TRACING=true
# or configure OTEL_TRACES_EXPORTER
```

Instruments (when enabled): FastAPI, SQLAlchemy, Redis, HTTPX.
Background tasks can use `record_background_task(name)` from `telemetry.py`.

## Monitoring stack

```bash
docker compose \
  -f deployment/compose/docker-compose.production.yml \
  -f deployment/compose/docker-compose.monitoring.yml \
  --profile monitoring \
  --env-file .env.production up -d
```

| Service | Port (default bind) |
| --- | --- |
| Prometheus | `127.0.0.1:9090` |
| Grafana | `127.0.0.1:3000` |
| Loki | `127.0.0.1:3100` |

Prometheus scrapes `http://api:8000/api/v1/metrics` (Prometheus text — not the
authenticated JSON `/system/metrics` admin endpoint).

Grafana dashboards provisioned automatically under folder **AI-Forge**.

## Distinction from Phase 8D `/system/metrics`

| Endpoint | Format | Auth | Use |
| --- | --- | --- | --- |
| `/metrics`, `/api/v1/metrics` | Prometheus text | Public | Scrapers |
| `/api/v1/system/metrics` | JSON | `system.monitor` | Admin UI |
| `/api/v1/monitoring/*` | JSON KPIs | `system.monitor` | Ops dashboard |

## Limitations

- Domain duration histograms only increase when callers use recording helpers
  (middleware always records HTTP metrics).
- GPU gauge reflects CUDA availability via optional `torch` import.
- Tracing is opt-in; default production path has zero exporter overhead.
