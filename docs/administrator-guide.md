# Administrator guide

For operators with `admin.manage_users`, `system.monitor`, and
`security.manage`. Investigators should use
[user-guide.md](user-guide.md) and
[investigator-guide.md](investigator-guide.md).

## Installation

Follow [deployment-guide.md](deployment-guide.md). Apply Alembic once per
environment (`20260915_0034` for v1.0.0). Do not run migrations from every
API replica.

## Identity

Authentication is required in production when `JWT_SECRET` is set. Default
roles: Administrator, Investigator, Analyst, Reviewer, Viewer. Permission
codes are listed in [authentication.md](authentication.md).

UI: `/users` (create/deactivate users, assign roles), `/security` (policy,
violations, case access), `/profile` (password change).

API: `POST /api/v1/users`, `PATCH /api/v1/users/{id}`, `GET /api/v1/sessions`,
`DELETE /api/v1/sessions/{id}`.

Password policy: 12–128 characters, mixed case, digit, special character,
Argon2id, lockout after repeated failures.

## Case access

Use `GET/PATCH /api/v1/cases/{case_id}/access` and the Security Governance
page to constrain who can open a case beyond role defaults.

## Configuration and environment variables

Secrets belong in the environment or a secret manager, never in git.
`.env.example` and `.env.production.example` are placeholders.

Production must set `APP_ENV=production`, `DEBUG=false`, a non-placeholder
`JWT_SECRET` (≥ 32 characters), PostgreSQL, Redis, and storage roots.
See [security-hardening.md](security-hardening.md) and
[security-rc3.md](security-rc3.md).

## Database migrations

```bash
uv run alembic -c backend/alembic.ini upgrade head
```

Compose uses the `migrate` service. Verify a single Alembic head before
cutover.

## Worker management

Celery workers consume RabbitMQ (or the configured broker). Scale replicas
via Compose or the Kubernetes worker Deployment / HPA
([scalability.md](scalability.md)). Restart workers after image upgrades;
they share the same schema as the API.

## Monitoring

- `/platform-health` — `platform_validation.*`
- `/analytics` — investigation analytics
- `/system`, `/deployment`, `/monitoring` — diagnostics, release identity,
  in-app metrics

Prometheus should scrape **`GET /api/v1/metrics` on the API ClusterIP**, not
the public HTTPS proxy (RC3). Probes: `GET /api/v1/system/liveness` and
`/readiness`.

Run `POST /api/v1/system/diagnostics/run` and
`POST /api/v1/platform/validate` during change windows.

## Backup and restore

Schedule `deployment/scripts/backup.sh`. Verify with
`deployment/scripts/verify_backup.sh`. Restore is destructive — follow
[disaster-recovery.md](disaster-recovery.md).

## Scaling

Horizontal API and worker replicas, Redis cache, and optional object storage
are documented in [scalability.md](scalability.md). Sticky sessions are not
required.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| 401 on `/cases` | `JWT_SECRET` set; user signed in; clock skew on JWT `exp` |
| 403 on create/upload | Role lacks the mapped permission |
| Readiness failed | PostgreSQL, Redis, disk for `STORAGE_ROOT` |
| Upload 415 / 413 | Allow-list and `MAX_UPLOAD_SIZE_MB` |
| Worker idle | Broker URL, queue names, worker Deployment replicas |
| Metrics 404 on HTTPS | Expected on public Nginx; scrape the API service |

## Interoperability

`/interoperability` exports/imports investigation packages
(`interop.export` / `interop.import`). Treat packages as sensitive; downloads
are rate-limited.
