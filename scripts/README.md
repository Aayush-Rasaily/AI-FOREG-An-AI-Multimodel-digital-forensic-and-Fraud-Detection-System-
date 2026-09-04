# Scripts

Operational scripts for Phase 8G production readiness.

| Script | Purpose |
| --- | --- |
| `migrate.sh` / `migrate.ps1` | Apply Alembic migrations to `head` |
| `deploy.sh` / `deploy.ps1` | Build and start `docker-compose.prod.yml` |
| `build-frontend.sh` / `build-frontend.ps1` | Production static asset build (`frontend/dist`) |

Set `ENV_FILE` to override the default `.env.production`.

See `docs/deployment.md` and `docs/operations.md` for full procedures.
