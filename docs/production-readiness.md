# Production readiness — AI-Forge v1.0.0

Operational sign-off for deploying AI-Forge. Application behavior is unchanged
in RC5/RC6; this page records **deployment and pipeline readiness**.

Related: [deployment-guide.md](deployment-guide.md),
[operations-guide.md](operations-guide.md),
[release-engineering.md](release-engineering.md),
[scalability.md](scalability.md),
[disaster-recovery.md](disaster-recovery.md).

## Review

| Area | Status |
| --- | --- |
| Production API image | Multi-stage, non-root `appuser`, `DEBUG=false`, healthcheck |
| Worker image | `deployment/docker/worker.Dockerfile`, Celery default CMD |
| Frontend image | Multi-stage nginx, read-only static assets |
| Compose | API, migrate, worker, frontend, postgres, redis, rabbitmq, optional nginx |
| TLS | `nginx-tls.conf.example` — HTTP→HTTPS, HSTS, gzip, `limit_req` |
| Environment | `.env.production.example` placeholders; production fails closed on secrets |
| CI quality gate | PR must pass backend, frontend, docs, security, docker |
| Releases | Tag `vX.Y.Z` matching `pyproject.toml`; GHCR images + GitHub Release |
| Monitoring | Liveness/readiness, Prometheus on the API service (not public edge) |
| Backup / restore | `deployment/scripts/backup.sh` / `restore.sh`; RPO/RTO in DR doc |

Celery Beat is **not** required: workers consume queued jobs; there is no
periodic Beat schedule in `celery_app`.

## Repeatable install

1. Copy `.env.production.example` → `.env.production` and replace secrets.
2. `./deployment/scripts/production_start.sh` (or Compose as documented).
3. Confirm migrate completed, API healthy, worker running.
4. `GET /api/v1/system/liveness` and `/readiness`.
5. Sign in and `POST /api/v1/system/release-check`.

## v1.0 verdict

The platform is **operationally ready** for a stable 1.0.0 release when CI is
green, secrets are injected from a vault (not git), TLS is terminated at the
edge, and a backup drill has been executed at least once.
