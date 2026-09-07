# Maintenance guide

Recurring work that keeps AI-Forge healthy without changing investigation
semantics.

## Daily / weekly

- Confirm readiness and monitoring dashboards.
- Review integrity alerts (`/api/v1/cases/{id}/integrity/alerts`).
- Confirm backup jobs and `verify_backup.sh` on a sample.
- Watch disk on `STORAGE_ROOT` (readiness fails below 5% free).

## Migrations

Apply Alembic in a maintenance window, **once per environment**. Do not run
migrations from every API replica. Verify:

```bash
uv run alembic -c backend/alembic.ini current
uv run alembic -c backend/alembic.ini heads
```

## Dependency and image hygiene

CI runs Ruff, MyPy, pytest, Vitest, pip-audit, npm audit, and Trivy
([security.yml](../.github/workflows/security.yml)). Patch **critical**
findings before promoting images.

## Model and cache maintenance

- Reload models with `POST /api/v1/models/reload` after weight updates.
- Redis is a cache: flush only if you accept extra DB load; never flush
  PostgreSQL to “clear AI”.
- Job queues: drain before stopping workers.

## Storage lifecycle

Use retention scripts (`deployment/scripts/cleanup.sh`) only on **derived**
objects allowed by policy. Original evidence deletion is a legal/custody
decision, not a convenience cleanup.

## Certificates and secrets

Rotate TLS certs at the edge. Rotate `JWT_SECRET` only with a planned
re-login of all users. Keep secret length and non-placeholder rules from
[security-hardening.md](security-hardening.md).

## Hotfixes

Follow the hotfix branch + patch tag process in
[release-engineering.md](release-engineering.md). Keep the change additive
and backward compatible.
