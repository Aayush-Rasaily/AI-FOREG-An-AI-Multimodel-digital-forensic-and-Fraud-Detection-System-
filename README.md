# AI_Forge

AI_Forge is an enterprise foundation for a multimodal digital forensics and
fraud intelligence platform. It is intended for banks, insurers, forensic
laboratories, law enforcement, cybersecurity teams, and other regulated
organizations.

This repository currently contains architecture and runtime boilerplate only.
It deliberately does not contain AI models, OCR, forensic workflows, fraud
rules, or business-domain implementations.

## Architecture

The backend follows Clean Architecture:

```text
backend/
├── app/
│   ├── api/             # HTTP transport and versioned routes
│   ├── application/    # Use-case and service boundaries
│   ├── core/           # Cross-cutting configuration and platform concerns
│   ├── domain/         # Framework-independent contracts and ports
│   ├── ai_engines/     # Future engine modules; intentionally empty
│   └── infrastructure/ # Database, cache, messaging, storage, and audit seams
└── alembic/             # Database migration environment
```

Dependencies point inward: API and infrastructure may depend on application
and domain abstractions, while domain code does not depend on FastAPI,
SQLAlchemy, Celery, or vendor SDKs. Future AI engines should implement the
domain engine contract and be registered through the extension boundary rather
than changing existing use cases.

See [`docs/architecture.md`](docs/architecture.md) for boundaries and
scalability guidance.

## Local development

Requirements:

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker and Docker Compose

Create local configuration and install development dependencies:

```bash
copy .env.example .env
uv sync --dev
```

Start the local dependency stack and API:

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. The health endpoint is
`GET /api/v1/health`, and the dependency-free liveness endpoint is
`GET /api/v1/health/live`. OpenAPI is available at `/docs` when `DEBUG=true`.

Run checks locally:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy backend
uv run pytest
```

## Configuration and secrets

Runtime settings are loaded from environment variables and an optional `.env`
file. `.env.example` contains placeholders only and must never be used as a
production secret store. Production deployments should inject secrets through
the platform's secret-management facility.

## Operational direction

The API is stateless and can scale horizontally behind a load balancer.
Long-running work belongs in Celery workers, with RabbitMQ as the broker and
Redis as the result backend/cache. PostgreSQL connections are pooled per
process, so pool limits must be sized against the database connection budget
when replicas or workers are added. Object storage, durable case artifacts,
outbox/idempotency patterns, observability, and authentication are intentionally
reserved for later architecture increments.

See [`docs/operations.md`](docs/operations.md) and
[`deployment/README.md`](deployment/README.md) before creating a production
deployment.

## License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE).
