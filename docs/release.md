# Release Management (Phase 8G)

Release identity and gate checks for AI-Forge production deployments.

## Release metadata

`GET /api/v1/system/release` returns:

| Field | Source |
| --- | --- |
| `application_version` | `APP_VERSION` / Settings |
| `schema_version` / `migration_version` | Expected Alembic head (`20260906_0025`) |
| `policy_versions` | Deployment, workflow, security, monitoring, audit |
| `ai_engine_versions` | Registered AI stacks on `app.state` |
| `build_metadata` | `BUILD_ID` / CI id + deployment engine |
| `git_commit` | `GIT_COMMIT` env or `git rev-parse HEAD` |

Compact version: `GET /api/v1/system/version`.

Engine constants:

- Deployment engine: `8g.1.0`
- Deployment policy: `1.0`

## Release process

1. Tag / record git commit; set `GIT_COMMIT` and `BUILD_ID` in the deploy environment.
2. Build production images (`Dockerfile.prod`, frontend `Dockerfile.prod`).
3. Run migrations to head.
4. Start API; confirm `liveness` then `readiness`.
5. Authenticate as an operator with `system.monitor`.
6. Run `POST /api/v1/system/release-check` (or use Administration → Deployment Status).
7. Ship only when status is `PASSED` (or accept `DEGRADED` with documented warnings in non-strict environments).

## Release check contents

`POST /system/release-check` performs:

1. Creates local backup metadata markers (database / report archive / configuration export).
2. Full operational validation (`POST /system/validate`).
3. Disaster recovery verification and restore readiness (metadata-level).
4. Returns combined status + release identity + backup records.

## UI

Administration → **Deployment** (`/deployment`):

- Health Overview
- Deployment panel (validate / release-check)
- Release panel
- Configuration panel

## Versioning policy

- Application version follows `APP_VERSION` (semver-style string).
- Schema/migration version is the Alembic revision id at head for the release train.
- Policy versions are independent per domain (workflow, security, monitoring, audit, deployment).
- Do not rewrite historical policy engines when bumping deployment policy.

## Related docs

- [deployment.md](deployment.md) — infrastructure and upgrade/rollback
- [operations.md](operations.md) — day-2 validation and probes
