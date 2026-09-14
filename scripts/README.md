# Scripts

Operational scripts for Phase 8G production readiness and native local development.

| Script | Purpose |
| --- | --- |
| `dev.ps1` | Native Windows: check PostgreSQL, migrate, start Uvicorn (no Docker) |
| `migrate.sh` / `migrate.ps1` | Apply Alembic migrations to `head` |
| `deploy.sh` / `deploy.ps1` | Build and start `docker-compose.prod.yml` |
| `build-frontend.sh` / `build-frontend.ps1` | Production static asset build (`frontend/dist`) |
| `security_scan.sh` | Dependency / secret scan helper |
| `benchmarks/run.py` | RC2 in-process latency/AI/report benchmarks |

`migrate.ps1` / `migrate.sh` load `.env` when present, otherwise
`.env.production`. Set `ENV_FILE` to override.

See `docs/deployment.md`, `docs/operations.md`, and `docs/development.md`.
