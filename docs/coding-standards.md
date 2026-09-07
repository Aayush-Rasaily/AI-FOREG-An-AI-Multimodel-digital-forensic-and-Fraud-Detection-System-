# Coding standards

## Backend (Python 3.12)

- Formatter/linter: Ruff. Types: MyPy on `backend/`.
- Prefer explicit types on public functions.
- Application services orchestrate; they do not embed SQL or HTTP.
- Domain modules must not import FastAPI, SQLAlchemy engines, or Celery.
- API handlers stay thin: validate → service → `ApiResponse`.
- Async job starts return `202` and persist status.
- Never log secrets, tokens, or raw evidence bytes.

## Frontend (TypeScript)

- Route pages through `AppRoutes.tsx`; keep data fetching in hooks/clients.
- Do not compute forensic hashes or findings in the browser.
- Handle loading, empty, error, and unauthorized states.
- Lazy-load heavy workspace panels.

## Testing

- Pytest for API/domain/application contracts.
- Vitest for UI behavior with mocked APIs.
- Name phase-specific tests `test_phase*.py` / `phase*.test.tsx` when adding
  a gated increment.
- Deterministic clocks and temp directories; no live GPU requirement for
  default CI.

## Security

- Enforce permissions server-side (`backend/app/auth/permissions.py`).
- Validate uploads with the server allow-list.
- Production: `JWT_SECRET` required, debug off.

## Git

- Conventional-ish subjects (`feat:`, `fix:`, `docs:`) help changelog
  generation in release.yml.
- Do not rewrite `main` history.
