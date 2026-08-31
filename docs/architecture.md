# Architecture

## Boundaries

The system is organized around dependency direction:

```text
API adapters ───────┐
                    ├──> Application orchestration ───> Domain contracts
Infrastructure ────┘
```

- **Domain** owns stable concepts and ports. It must remain independent of
  FastAPI, SQLAlchemy, Celery, Redis, and cloud providers.
- **Application** coordinates use cases and depends on domain ports. It must
  not know how an adapter stores data or sends messages.
- **Infrastructure** implements ports for PostgreSQL, Redis, RabbitMQ, and
  external providers.
- **API** translates HTTP requests/responses and delegates to application
  services. HTTP concerns must not leak into the domain.
- **AI engines** are extension modules. Each engine should implement the
  domain `AIEngine` protocol and be selected through explicit registration or
  dependency injection. Existing use cases must not import concrete engines.
- The domain also owns ports for streamed artifact storage, idempotency,
  reliable event publication, and immutable audit logging. Phase 3 adds a
  local storage adapter and database-backed custody records for application
  preservation; durable/compliance-grade adapters remain deployment decisions.

## Scalability guardrails

The API process is stateless and safe to replicate. Long-running or
CPU/GPU-bound work must execute outside the request process through Celery.
Workers should be independently scaled by queue and workload class. RabbitMQ
is the broker; Redis is reserved for cache and task results.

At million-analysis scale, the foundation must be extended with:

1. Replace local evidence storage with durable object storage for evidence
   artifacts instead of database blobs.
2. Implement idempotency keys and an outbox/inbox strategy for reliable event
   delivery.
3. Partitioning and retention policies for analysis metadata and audit events.
4. Per-tenant quotas, workload queues, backpressure, and dead-letter handling.
5. OpenTelemetry-compatible traces, metrics, and centralized log retention.
6. Authentication, authorization, tenant isolation, encryption, and an
   implementation of the immutable chain-of-custody audit port.

These are deliberate architecture increments, not hidden inside the
boilerplate. Adding them later must preserve the inward dependency direction.

## Engine extension rule

Engine-specific dependencies belong in the engine module or service boundary,
not in the core API package. A future engine should provide its adapter,
capability metadata, health behavior, and versioned contract independently.
The platform should select it through a registry or injected factory, allowing
new engines to be deployed without changing existing orchestration code.
