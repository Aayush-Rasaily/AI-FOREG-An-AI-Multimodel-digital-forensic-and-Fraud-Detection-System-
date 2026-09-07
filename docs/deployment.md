# Deployment (Phase 8G + Phase 10A)

Narrative guide: [deployment-guide.md](deployment-guide.md).

Production infrastructure for AI-Forge: container images, Compose/Kubernetes
manifests, Nginx reverse proxy, environment validation, startup verification,
and graceful shutdown.

This layer is **additive**. Investigation logic, AI algorithms, forensic
engines, evidence processing, and existing APIs remain unchanged except for
startup/shutdown wiring required for production safety.

Phase 8G application package: `backend/app/deployment/`  
Phase 10A infrastructure tree: `deployment/`

## Architecture

```
deployment/
  docker/          backend.Dockerfile, frontend.Dockerfile
  compose/         docker-compose.production.yml (+ monitoring overlay)
  k8s/             Namespace, Deployments, Services, Postgres, Redis, Ingress
  nginx/           Edge reverse proxy + SPA frontend.conf
  scripts/         production_start/stop, migrate, backup

Application
  backend/app/core/environment.py   env/secrets/storage verification
  backend/app/core/config.py        Development/Testing/Production settings
  lifespan                          startup checks + graceful shutdown
```

```
Client → Nginx (TLS/gzip/cache) → Frontend (static) + /api → API
                                      │
                       Postgres / Redis / RabbitMQ / storage / models
```

## Production deployment (Docker Compose)

1. Copy `.env.production.example` → `.env.production` and set secrets.
2. Start:

```bash
# Linux/macOS
chmod +x deployment/scripts/*.sh
./deployment/scripts/production_start.sh

# Or manually
docker compose -f deployment/compose/docker-compose.production.yml \
  --env-file .env.production up -d --build
```

3. Optional monitoring overlay:

```bash
docker compose \
  -f deployment/compose/docker-compose.production.yml \
  -f deployment/compose/docker-compose.monitoring.yml \
  --profile monitoring \
  --env-file .env.production up -d
```

4. Confirm probes:

- `GET /api/v1/system/liveness`
- `GET /api/v1/system/readiness`
- Frontend: `http://127.0.0.1:8080/`

Legacy root compose files (`docker-compose.prod.yml`, `Dockerfile.prod`) remain
supported for backward compatibility.

## Docker images

| Image | Dockerfile |
| --- | --- |
| API / worker / migrate | `deployment/docker/backend.Dockerfile` |
| Frontend (nginx SPA) | `deployment/docker/frontend.Dockerfile` |

Build examples:

```bash
docker build -f deployment/docker/backend.Dockerfile -t ai-forge-api:prod .
docker build -f deployment/docker/frontend.Dockerfile \
  --build-arg VITE_API_BASE_URL=/api/v1 \
  -t ai-forge-frontend:prod .
```

## Kubernetes

Manifests under `deployment/k8s/`:

1. `kubectl apply -f deployment/k8s/namespace.yaml`
2. Create `ai-forge-secrets` / `ai-forge-config` (not committed).
3. Apply postgres, redis, backend, frontend, ingress.

Ingress terminates TLS via `ai-forge-tls` and routes `/api` → backend, `/` → frontend.

## Nginx

| File | Role |
| --- | --- |
| `deployment/nginx/frontend.conf` | SPA container: gzip, immutable asset cache, `/api` proxy |
| `deployment/nginx/nginx.conf` | Edge profile: upstreams + optional TLS on :443 |

Brotli is optional (custom nginx builds with `ngx_brotli`). Standard images use gzip.

## SSL / TLS

Compose edge profile:

```bash
mkdir -p certs
# place fullchain.pem + privkey.pem
docker compose -f deployment/compose/docker-compose.production.yml \
  --profile edge --env-file .env.production up -d
```

Kubernetes: provision `ai-forge-tls` secret referenced by `ingress.yaml`.

## Environment variables

See `.env.production.example` and `.env.example`.

| Variable | Purpose |
| --- | --- |
| `APP_ENV` | `local` / `development` / `test` / `staging` / `production` |
| `DEBUG` | Must be `false` in production |
| `DATABASE_URL` | SQLAlchemy async URL |
| `REDIS_URL` | Cache / Celery result |
| `STORAGE_ROOT` | Evidence storage |
| `TEMP_STORAGE_PATH` | App temp directory |
| `AI_MODEL_ROOT` | Optional model weights directory |
| `JWT_SECRET` | Required in production (enables auth) |

Pydantic settings profiles:

- `DevelopmentSettings` — `.env.development`
- `TestingSettings` — `.env.test` / sqlite-friendly defaults
- `ProductionSettings` — `.env.production` + hardened defaults

`backend/app/core/environment.py` validates required vars, detects missing /
placeholder secrets, verifies storage/temp/model write access, and (at
startup) checks database + Redis before accepting traffic in production.

## Frontend configuration

| File | Use |
| --- | --- |
| `frontend/.env.development` | Vite dev proxy + API base |
| `frontend/.env.production` | Production API base (`/api/v1`) |

Vite production builds enable asset splitting, compressed-size reporting, and
immutable cache headers via nginx for hashed static assets.

## Upgrade procedure

1. Record release metadata (`GET /system/release`) and run `POST /system/release-check`.
2. Create backup: `./deployment/scripts/backup.sh`
3. Pull new images / code; run `./deployment/scripts/migrate.sh`
4. Restart with `./deployment/scripts/production_start.sh`
5. Verify liveness then readiness; confirm Administration → Deployment Status.

Expected migration head: `20260914_0033` (see `EXPECTED_MIGRATION_HEAD`).

## Rollback procedure

1. `./deployment/scripts/production_stop.sh`
2. Redeploy previous image tags / git commit.
3. If a migration must be reversed, restore from the database dump under
   `data/deployment/backups/<stamp>/` **before** Alembic downgrade.
4. Re-run readiness and release-check before returning traffic.

## Graceful shutdown

On SIGTERM the API lifespan:

1. Marks shutdown requested
2. Cleans temporary probe files
3. Disposes the SQLAlchemy engine
4. Closes the Redis client pool

Compose / Kubernetes set `stop_grace_period` / `terminationGracePeriodSeconds`
so in-flight requests can drain.

## Scripts

| Script | Action |
| --- | --- |
| `deployment/scripts/production_start.sh` | Build + up + wait for liveness |
| `deployment/scripts/production_stop.sh` | Stop + down |
| `deployment/scripts/migrate.sh` | Alembic upgrade head |
| `deployment/scripts/backup.sh` | Metadata + optional `pg_dump` |

See also: [operations.md](operations.md), [release.md](release.md),
[platform-validation.md](platform-validation.md).
