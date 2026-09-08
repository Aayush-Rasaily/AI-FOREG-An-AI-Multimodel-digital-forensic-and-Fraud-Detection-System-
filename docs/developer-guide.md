# Developer guide

How to contribute to AI-Forge without breaking Clean Architecture or
forensic guarantees. Coding rules: [coding-standards.md](coding-standards.md).
Process: [contributing.md](contributing.md). Local setup:
[development.md](development.md).

## Repository structure

```text
backend/app/        API, application, domain, infrastructure, engines
backend/alembic/    Schema migrations (head 20260915_0034 in v1.0.0)
frontend/            Vite + React investigation SPA
deployment/          Docker, Compose, Kubernetes, Nginx, ops scripts
docs/                Architecture, ops, user, and release documentation
tests/               Backend pytest
.github/workflows/   CI/CD quality gates
```

## Clean Architecture

- Domain and application layers do not import FastAPI, SQLAlchemy engines, or
  React.
- HTTP adapters live in `backend/app/api`.
- Persistence and brokers live in `backend/app/infrastructure`.
- AI engines are reached through the registry, not copied into fusion or
  reporting.

## Testing strategy

- Backend: pytest under `tests/` (auth, uploads, e2e, RC3 security).
- Frontend: Vitest + Testing Library (`frontend/src/test/`).
- Do not commit real evidence, secrets, or production URLs.

Commands: [development.md](development.md#testing).

## Adding an AI analyzer

1. Implement the engine contract and register it.
2. Persist runs/findings with a dedicated Alembic revision when the schema
   must change (none in RC3/RC4).
3. Expose HTTP adapters; fusion reads **stored** findings only.
4. Document unavailable capabilities instead of inventing scores.

See [ai-architecture.md](ai-architecture.md).

## Creating migrations

```bash
uv run alembic -c backend/alembic.ini revision --autogenerate -m "describe"
uv run alembic -c backend/alembic.ini upgrade head
```

Review lock time, rollback, and indexes. Update
`EXPECTED_MIGRATION_HEAD` only when the train intentionally moves.

## Extending APIs

Keep `/api/v1` envelopes, error codes, and RBAC mapping in
`backend/app/auth/permissions.py`. Add Pydantic models with
`extra="forbid"` on write payloads. Update [api-reference.md](api-reference.md).

## Frontend conventions

- Route protection via `ProtectedRoute` / `RoleGuard`.
- API access through `frontend/src/services/api`.
- No `dangerouslySetInnerHTML` for investigator content.
- Tokens: sessionStorage by default; localStorage only for remember-me.
