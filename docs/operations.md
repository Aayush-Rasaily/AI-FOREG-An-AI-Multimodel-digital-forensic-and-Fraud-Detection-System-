# Operations (Phase 8G)

Day-2 operational validation and probes for AI-Forge.

## Probe map

| Probe | Path | Use |
| --- | --- | --- |
| Liveness | `GET /api/v1/system/liveness` | Orchestrator restart decisions |
| Readiness | `GET /api/v1/system/readiness` | Traffic admission |
| Legacy live | `GET /api/v1/health/live` | Existing compose healthchecks |
| Startup | `GET /api/v1/system/startup-validation` | Post-boot config snapshot |
| Validate | `POST /api/v1/system/validate` | Full ops check (authenticated) |

In **production**, readiness is true only when validation status is `PASSED`.
In other profiles, `DEGRADED` (warnings only) still counts as ready.

## Operational validation checks

Deterministic checks (sorted by name):

- `database` — SQL connectivity
- `redis` — ping when `REDIS_URL` set
- `storage` — writable `STORAGE_ROOT`
- `disk` — free space thresholds (5% fail / 15% warn)
- `required_env_vars` — production env completeness
- `ai_models` — registered AI stacks
- `migration_status` — Alembic revision vs expected head
- configuration integrity (`debug_disabled_in_production`, `auth_required_in_production`, `database_url`, `storage_root`)

## Graceful shutdown

Application lifespan calls `mark_shutdown_requested()` before disposing the
DB engine and Redis client. Compose production services use a 30s stop grace
period.

## Backup & recovery (metadata only)

No cloud backup integration ships in Phase 8G. Utilities write JSON markers under:

`{STORAGE_ROOT}/deployment/backups/`

Kinds:

- `database` — logical backup marker (operator runs `pg_dump` externally)
- `report_archive` — report path presence
- `configuration_export` — safe config snapshot

Recovery helpers:

- `verify_disaster_recovery` — metadata completeness
- `validate_restore_readiness` — documented restore prerequisites

`POST /system/release-check` creates a fresh set of markers then verifies DR.

## Configuration verification

`GET /system/configuration` returns profile summary, safe export, and findings.
Use it after environment changes and before promoting a release.

## Upgrade / rollback

Follow [deployment.md](deployment.md). Always capture release metadata and run
release-check before and after upgrades.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Readiness `not_ready` in production | Inspect `checks` on readiness/validate; fix FAIL rows |
| Redis WARN | Confirm `REDIS_URL` and redis health |
| Migration WARN | Run migrate script / compose migrate service |
| AI models FAIL | Ensure API process built AI stacks (normal `create_app`) |
| Auth FAIL in production | Set `JWT_SECRET` |

## Related docs

- [deployment.md](deployment.md)
- [release.md](release.md)
- [monitoring.md](monitoring.md) — Phase 8D KPIs (separate from probes)
