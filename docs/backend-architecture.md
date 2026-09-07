# Backend architecture

Python 3.12 FastAPI application under `backend/app/`. Composition root:
`backend/app/main.py`. Worker composition:
`backend/app/infrastructure/messaging/celery_app.py`.

Companion: [architecture.md](architecture.md),
[architecture-overview.md](architecture-overview.md).

## Package map

```text
backend/app/
├── api/                 HTTP adapters, schemas, dependencies
├── application/         Use-case services
├── domain/              Ports and value objects
├── models/              SQLAlchemy persistence
├── auth/                JWT, RBAC, sessions
├── ai/                  Registry, inference engine, device
├── extraction/          Localization / OCR records
├── forensics/           Detector orchestration
├── fusion/              Multimodal jury
├── reporting/           Aggregation and renderers
├── infrastructure/      DB, cache, storage, Celery
├── scaling/             Queues, workers, storage factory
├── security/            Headers, uploads, rate limits
├── recovery/            Backup / restore helpers
├── cicd/                Release-gate helpers (CI only)
└── deployment/          Startup / release-check
```

Alembic lives in `backend/alembic/` with `backend/alembic.ini`. Expected
head is documented in `backend/app/deployment/release.py`
(`EXPECTED_MIGRATION_HEAD`).

## Request path

1. Nginx (production) terminates TLS and forwards `/api/`.
2. Middleware: request id, security headers, CORS, rate limit, audit hooks.
3. `require_request_authorization` maps method + path → permission.
4. Endpoint depends on an application service (`get_*_service`).
5. Service uses repositories / storage ports.
6. Response is always `ApiResponse` or `ErrorResponse`.

Async analysis endpoints return **202** and persist a run/job row. Clients
poll GET history or status routes.

## Processing pipeline

`POST /api/v1/evidence/{id}/process` queues a processing job. The orchestrator
hashes the original, classifies type, extracts basic metadata, and writes
preview/metadata/classification artifacts with their own hashes. Failures are
explicit; the original remains untouched.

Extraction (`/extract`) is a separate phase from forensic analysis
(`/analyze`) and from modality AI (`/image-analysis`, `/document-analysis`,
and so on).

## AI orchestration

`backend/app/ai/` owns registry, loader, cache, and inference jobs. Modality
packages persist findings and regions. Reloading a model is
`POST /api/v1/models/reload` — infrastructure, not a forensic rewrite.

## Multimodal fusion

`backend/app/fusion/` normalizes stored findings, runs the deterministic jury,
and stores conflicts. It does not re-execute modality engines.

## Correlation engine

`backend/app/correlation/` (and related entity/timeline packages) operate at
**case** scope. Runs are queued (`202`) and listed per case.

## Reporting engine

`backend/app/reporting/` aggregates persisted investigation products into
versioned report sections with provenance. Generation is queued; download is a
separate GET.

## Jobs and scale

Default `JOB_QUEUE_MODE=local` runs work in-process/background for development.
Production can use Celery queues by workload class (see
[scalability.md](scalability.md)). API processes stay stateless.

## Storage

`storage_factory` selects local disk, S3, Azure Blob, or GCS from settings.
Evidence originals and artifacts never live as unconstrained database blobs.
