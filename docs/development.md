# Development

Phase 10H documentation index: [README.md](README.md). Contributor map:
[developer-guide.md](developer-guide.md). Standards:
[coding-standards.md](coding-standards.md). Contributions:
[contributing.md](contributing.md).

## Setup (native — no Docker)

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 22,
**native PostgreSQL**.

Redis, RabbitMQ, and Celery are optional for normal API + evidence + AI work
when `JOB_QUEUE_MODE=local` (default). Docker is optional and reserved for
Compose / production packaging.

```powershell
copy .env.example .env
# Point DATABASE_URL at localhost PostgreSQL (not the Compose hostname "postgres")
# Set JWT_SECRET and AUTH_BOOTSTRAP_PASSWORD in .env before the first login
# (see Authentication credentials below).

uv sync --dev
uv run alembic -c backend/alembic.ini upgrade head
uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Or: `.\scripts\dev.ps1`

Frontend:

```powershell
cd frontend
npm ci
npm run dev
```

`VITE_API_BASE_URL` defaults to `/api/v1` (Vite proxies `/api` to
`VITE_BACKEND_URL`, default `http://127.0.0.1:8000`).

CORS for direct browser→API calls should include Vite origins
(`http://localhost:5173` / `http://127.0.0.1:5173`) via `CORS_ORIGINS` in `.env`.

## Authentication credentials

Login is backend JWT + database users (see [authentication.md](authentication.md)).
The React login page never embeds credentials.

1. Copy `.env.example` → `.env` (gitignored) and set `JWT_SECRET`.
2. On first auth request, if username `admin` is missing, the API seeds
   Administrator `admin` / `admin` with an Argon2id hash (never plaintext).
3. Sign in at `/login`, or create a Viewer account at `/register`.
4. Change the default admin password via `/profile` after first login.

Do not commit a real `.env`.

## Project structure

```text
backend/app/     Clean Architecture API (see backend-architecture.md)
frontend/         Vite investigation SPA
deployment/       Docker, Compose, k8s, nginx, scripts
docs/             Enterprise documentation
tests/            Backend pytest
.github/          CI/CD workflows
```

## Dependency direction

New use cases belong in `backend/app/application`. Domain contracts belong in
`backend/app/domain/ports`. Concrete database, broker, cache, object-storage,
or provider code belongs in `backend/app/infrastructure`. HTTP translation
belongs in `backend/app/api`.

The composition root is `backend/app/main.py` for the API and
`backend/app/infrastructure/messaging/celery_app.py` for workers. Avoid
creating infrastructure clients inside domain or application modules.

## Background jobs

- Default: `JOB_QUEUE_MODE=local` — FastAPI `BackgroundTasks` (no broker).
- Distributed: set `JOB_QUEUE_MODE=celery`, run Redis + RabbitMQ, then:

```powershell
uv run celery -A backend.app.infrastructure.messaging.celery_app:celery_app worker --loglevel=INFO --concurrency=2
```

## Testing

```bash
uv run ruff check backend tests
uv run ruff format --check backend tests
uv run mypy backend
uv run pytest tests -q --tb=short
cd frontend && npm test && npm run build
```

Tests must cover contracts and failure behavior without requiring live
infrastructure unless explicitly marked as integration tests. Never place
credentials, real evidence, personally identifiable information, or
production connection strings in tests.

Settings in unit tests typically use `app_env="test"` or `"local"`, SQLite
async URLs, and `rate_limit_enabled=False`.

## Migrations

Create migrations with Alembic after persistence models exist. Review every
migration for lock duration, backward compatibility, index strategy, and
rollback behavior. Run migrations once as a release operation; do not run
them from every API replica.

```bash
uv run alembic -c backend/alembic.ini revision --autogenerate -m "describe"
uv run alembic -c backend/alembic.ini upgrade head
```

On Windows, Alembic already selects `WindowsSelectorEventLoopPolicy` so
psycopg async works with native PostgreSQL.

Pin `EXPECTED_MIGRATION_HEAD` when the release train moves. CI verifies a
single matching head.

## Adding AI modules

1. Implement the engine/factory contract; register in the model registry.
2. Persist runs and findings in dedicated tables + Alembic.
3. Add HTTP adapters; do not import concrete engines from unrelated use cases.
4. Fusion must consume stored findings only.
5. Document unavailable capabilities explicitly.

See [ai-architecture.md](ai-architecture.md).

## Extending the platform

- New investigation products: application service → repository → endpoint →
  optional UI panel.
- New storage backends: implement the storage port; wire via
  `storage_factory`.
- New worker queues: [scalability.md](scalability.md).
- Do not rewrite forensic/AI algorithms to “fit” a feature. Prefer additive
  modules.

## Quality gates (CI)

Ruff, MyPy, pytest, Vitest, production frontend build, Alembic heads,
OpenAPI 3.x, Dockerfiles, and security scans. See
[release-engineering.md](release-engineering.md).
