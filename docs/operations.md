# Operations

## Local services

Docker Compose starts the API, Celery worker, PostgreSQL, Redis, and
RabbitMQ. The API exposes `GET /api/v1/health` with database status and
`GET /api/v1/health/live` as a dependency-free process liveness probe.
Health degradation is reported in-band so startup never depends on PostgreSQL.

Phase 3 stores development evidence originals under the configured
`STORAGE_ROOT` (default `data/`). Docker Compose mounts this location as the
`evidence-data` volume. This local adapter is not an evidentiary compliance
boundary; production should use immutable/WORM-capable object storage,
encryption, retention, and access controls.

## Production requirements

- Build from a pinned, vulnerability-scanned image and run as a non-root user.
- Inject secrets through a managed secret store; never commit `.env`.
- Set database pool limits from the total connection budget across API replicas,
  workers, migrations, and administrative tools.
- Run migrations as a controlled release step, never concurrently from every
  API replica.
- Use separate queues and worker pools for materially different workloads.
- Configure durable broker policies, retry limits, dead-letter queues, and
  idempotent task handlers before processing regulated evidence.
- Export structured logs, metrics, traces, and audit events to the
  organization-approved observability platform.
- Add network policy, TLS, identity, authorization, tenant isolation, backup,
  disaster recovery, and retention controls before production use.

## Failure behavior

Unexpected exceptions are logged with a request correlation identifier and
returned to clients as a generic error. Expected application exceptions must
use stable machine-readable error codes. No response should expose stack
traces, credentials, raw evidence, or downstream connection details.
