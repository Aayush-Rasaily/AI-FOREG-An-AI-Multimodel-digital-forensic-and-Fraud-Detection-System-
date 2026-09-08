# Operations guide

Day-2 runbook for AI-Forge. Probes and validation details:
[operations.md](operations.md). Infrastructure:
[deployment-guide.md](deployment-guide.md).

## Deployment

1. Configure secrets (`JWT_SECRET`, database URL, storage credentials).
2. Apply Alembic to the expected head.
3. Start API, frontend, Redis, PostgreSQL, and workers.
4. Confirm `GET /api/v1/health/live` then `GET /api/v1/system/readiness`.
5. Authenticate and run `POST /api/v1/system/release-check`.

Compose and Kubernetes steps: [deployment.md](deployment.md).

## Scaling

- API is stateless; scale replicas behind Nginx/Ingress.
- Workers scale by queue class (see [scalability.md](scalability.md)).
- PostgreSQL pool size × replicas must stay under the database connection
  budget. Optional `DATABASE_READ_URL` for read offload.
- Redis for cache and rate limits; RabbitMQ when `JOB_QUEUE_MODE` is Celery.

## Upgrades

1. Green CI on `main`.
2. Backup database and storage ([disaster-recovery.md](disaster-recovery.md)).
3. Deploy new images (`:semver` or SHA tags).
4. Run migrations **once**.
5. Roll API/workers; confirm release-check.
6. If failed, redeploy previous image tags and restore only if a
   forward-incompatible migration shipped.

Release engineering: [release-engineering.md](release-engineering.md).

## Backups

Use `deployment/scripts/backup.sh`, `verify_backup.sh`, `restore.sh`, and
`cleanup.sh`. Python helpers live in `backend/app/recovery/`. Test restores
on a non-production copy. Do not “undo” a release by rewriting forensic
artifacts.

## Monitoring

| Signal | Where |
| --- | --- |
| Liveness / readiness | `/api/v1/system/liveness`, `/readiness` |
| Prometheus | `GET /api/v1/metrics` |
| Ops dashboard | `GET /api/v1/monitoring/*` |
| UI | `/monitoring`, `/system`, `/deployment` |

See [monitoring.md](monitoring.md) and [system-monitoring.md](system-monitoring.md).

## Maintenance

- Rotate `JWT_SECRET` and database passwords on a schedule; revoke sessions after JWT rotation.
- Apply OS and base-image updates via rebuilds of `deployment/docker/*`.
- Prune old backup stamps with `deployment/scripts/cleanup.sh`.
- Scale API and worker replicas independently ([scalability.md](scalability.md)).
- Weekly Dependabot PRs must pass **CI / Quality gate** before merge.

Production sign-off: [production-readiness.md](production-readiness.md).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Pod not ready | Readiness JSON; disk, DB, Redis, migrations |
| 401 on all calls | `JWT_SECRET`, clock skew, expired access token |
| 403 | Role/permission vs path |
| 429 | Rate-limit category; Redis connectivity |
| Jobs stuck | Worker logs, queue mode, storage permissions |
| Upload rejected | MIME/extension allow-list, size caps |
| AI unavailable | Model registry, device, explicit unavailable status |
| Duplicate Alembic heads | `alembic heads` — CI will fail until merged |

Never re-run AI solely to “fix” a deploy. Preserve originals and custody.
