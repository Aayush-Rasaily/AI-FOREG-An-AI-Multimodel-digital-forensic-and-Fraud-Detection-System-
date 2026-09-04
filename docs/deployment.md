# Deployment (Phase 8G)

Production infrastructure, health probes, and reproducible deploy tooling
for AI-Forge. This layer is **additive** — existing `/health`, Phase 7F
`/system/health|metrics|…`, and Phase 8D monitoring endpoints are unchanged.

## Architecture

```
Docker Compose (prod)
  ├── migrate   → alembic upgrade head
  ├── api       → uvicorn (liveness: /api/v1/system/liveness)
  ├── worker    → celery
  ├── frontend  → nginx + static build (proxies /api)
  ├── postgres / redis / rabbitmq
```

Application package: `backend/app/deployment/`

| Module | Role |
| --- | --- |
| `configuration.py` | Profiles, safe export, integrity checks |
| `validation.py` | DB / Redis / storage / disk / env / AI / migrations |
| `health.py` / `readiness.py` | Liveness & readiness payloads |
| `startup.py` | Startup validation + graceful shutdown flag |
| `release.py` | Version / schema / policy / git metadata |
| `backup.py` / `recovery.py` | Local backup **metadata** (no cloud) |
| `service.py` | API composition |

## Production setup

1. Copy `.env.production.example` → `.env.production` and set secrets.
2. Build and start:

```bash
# Linux/macOS
./scripts/deploy.sh

# Windows
.\scripts\deploy.ps1
```

Or manually:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

3. Confirm probes:

- `GET /api/v1/system/liveness`
- `GET /api/v1/system/readiness`
- Existing compose health: `/api/v1/health/live` (dev stack)

## Configuration

Profiles: `local` | `development` | `test` | `staging` | `production`

Production requires:

- `APP_ENV=production`
- `DEBUG=false`
- `DATABASE_URL`, `REDIS_URL`, `STORAGE_ROOT`
- `JWT_SECRET` (enables `auth_required`)

Safe configuration is exposed at `GET /api/v1/system/configuration`
(no secrets). Integrity findings flag debug/auth/database/storage issues.

## Health endpoints

| Endpoint | Auth | Purpose |
| --- | --- | --- |
| `GET /system/liveness` | Public | Process alive (no dependency I/O) |
| `GET /system/readiness` | Public | Aggregated operational readiness |
| `GET /health/live` | Public | Legacy/dev probe (unchanged) |
| `GET /system/startup-validation` | `system.monitor` | Last startup config check |
| `POST /system/validate` | `system.monitor` | Full operational validation |
| `POST /security/validate` | security perms | **Different** — governance chain (8F) |

## Database migration automation

- Compose `migrate` service runs `alembic upgrade head` before API/worker.
- Host scripts: `scripts/migrate.sh` / `scripts/migrate.ps1`
- Expected migration head for this release train: `20260906_0025`

## Static asset pipeline

```bash
./scripts/build-frontend.sh
# or frontend image via Dockerfile.prod (node build → nginx)
```

Frontend production image proxies `/api/` to the `api` service.

## Upgrade procedure

1. Record release metadata (`GET /system/release`) and run `POST /system/release-check`.
2. Create backup metadata (release-check writes local markers under `storage_root/deployment/backups/`).
3. Pull new images / code; run migrations (`migrate` service or script).
4. Restart API/worker with new image; verify liveness then readiness.
5. Confirm Administration → Deployment Status UI.

## Rollback procedure

1. Stop API/worker on the failed revision.
2. Redeploy previous image tag / git commit.
3. If a migration must be reversed, apply the documented Alembic downgrade for that revision **only after** restoring a database backup artifact referenced by backup metadata.
4. Re-run readiness and release-check before returning traffic.

See also: [release.md](release.md), [operations.md](operations.md).
