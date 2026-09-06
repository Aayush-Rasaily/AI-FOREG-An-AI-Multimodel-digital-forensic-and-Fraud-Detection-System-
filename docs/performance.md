# Performance Optimization (Phase 10C)

Operational performance work for production-scale AI-Forge workloads.
**No forensic logic, scoring, custody, hashing, or AI algorithm changes.**

## Goals

| Area | Target |
| --- | --- |
| API (non-AI) average latency | < 150 ms |
| Database average query | < 50 ms |
| Frontend Lighthouse Performance | ≥ 90 |
| Production bundle | code-split + vendor chunks |
| AI models | no unnecessary reloads; shared registry + cache |
| Large files | streamed in chunks off the event loop |

## Benchmark methodology

1. **API latency** — Hit representative non-AI endpoints (`/health`, `/cases`, `/evidence` list) under local ASGI with warm process; record p50/p95 from Prometheus `ai_forge_http_request_duration_seconds` (Phase 10B).
2. **AI latency** — Use DummyModel / infrastructure check jobs; measure load vs cache-hit inference via `AIInferenceEngine` benchmark dict (`cache_hit`, `load_time_ms`, `inference_latency_ms`).
3. **Memory / CPU** — Sample process RSS and CPU via OS tools or Grafana system dashboard during report aggregation and model list storms.
4. **Database** — Enable SQL echo in staging only; use composite indexes from migration `20260915_0034` and compare plan times for evidence-by-case and latest-run-per-evidence patterns.
5. **Frontend bundle** — `npm run build` and inspect Vite compressed sizes / chunk graph (`vendor-react`, `vendor-query`, route + workspace panel chunks).
6. **Regression** — Existing Phase 1–9 behavioral tests must remain green; Phase 10C adds micro-benchmarks that assert helper/registry invariants, not absolute wall-clock SLOs in CI.

## Optimization summary

### Backend

- **Indexes** — Additive Alembic revision `20260915_0034` for evidence, processing jobs, audit, findings, analysis runs, fusion runs.
- **Query batching** — Report aggregation loads latest fusion/forensic runs and findings in bulk (`IN` + window `row_number`) instead of per-evidence N+1 loops.
- **Pagination helpers** — Shared `apply_pagination` / `count_rows` utilities.
- **Bulk helpers** — `bulk_add` / `bulk_update_mappings` for multi-row staging.
- **Connection pool** — `db_pool_recycle` (default 1800s) on non-SQLite engines.
- **Concurrency** — Bounded `ThreadPoolExecutor` (`infrastructure/concurrency.py`) installed as asyncio default executor; used for PDF chunk reads.
- **Redis JSON cache** — Short-TTL cache for safe read-only AI model list metadata only (never findings/scores/custody).
- **Streaming** — Report PDF download yields 1 MiB chunks via `run_in_thread` so sync storage I/O does not block the event loop.
- **Temp cleanup** — Existing lifespan cleanup retained; thread pool shut down on exit.

### AI

- **Shared registry metadata cache** — `ModelRegistry` stores `ModelMetadata` at register time; `list_metadata` / `discover_capabilities` no longer re-instantiate every model.
- **Lazy instance load** — `lookup()` still creates instances on first use; `CacheManager` avoids reload storms.
- **GPU fallback** — Device selection falls back to CPU when CUDA/MPS unavailable or free VRAM is critically low; engine retries load on CPU if GPU load fails.
- **Batch size cap** — Existing `max_batch_size` respected (no algorithm change).

### Frontend

- **Route splitting** — Existing lazy routes in `AppRoutes`.
- **Workspace panel lazy loading** — Heavy investigation tabs loaded with `React.lazy` + `Suspense`.
- **Query defaults** — Global `staleTime` 15s / `gcTime` 5m for request deduplication and fewer refetches.
- **Virtualized lists** — `VirtualList` windows large investigation lists.
- **Bundle splitting** — Vite `manualChunks` for react, TanStack Query, icons, and remaining vendor.

## Monitoring integration

Use Phase 10B Prometheus/Grafana:

- API latency histograms for non-AI SLO tracking
- AI/job duration series for model load vs inference
- System dashboard for CPU/memory during scale tests

Readiness (`/api/v1/health/ready`) remains uncached so orchestration probes see live dependency health.

## Acceptance notes

- APIs unchanged except optional cache of model list payloads (same schema).
- Migration head: `20260915_0034`.
- Fully backward compatible with Phases 1–9 capabilities.
