# Release checklist — AI-Forge v1.0.0

Sign-off sheet for production cutover. Schema head remains
`20260915_0034`. Phase 10I adds **validation only**.

Version files: `VERSION`, `pyproject.toml`, `frontend/package.json`,
`CHANGELOG.md`, `RELEASE_NOTES.md`.

## Infrastructure

- [ ] PostgreSQL, Redis, and (if used) RabbitMQ are sized and backed up
- [ ] Object/local storage is writable; `STORAGE_ROOT` has >15% free
- [ ] TLS at the edge (`deployment/nginx/nginx-tls.conf.example`)
- [ ] Images tagged `1.0.0`, `latest`, and git SHA
- [ ] Kubernetes HPA/PDB or Compose replica counts set
- [ ] Secrets injected from a vault — not from git

## Monitoring

- [ ] `GET /api/v1/system/liveness` and `/readiness` wired as probes
- [ ] Prometheus scrape of `GET /api/v1/metrics`
- [ ] `/monitoring` dashboard reachable for `system.monitor`
- [ ] Alert on readiness failure, disk, and backup job failure

## Security

- [ ] `JWT_SECRET` ≥ 32 chars, non-placeholder; debug off in production
- [ ] Security headers present (see [security-validation.md](security-validation.md))
- [ ] Upload allow-list and size caps confirmed
- [ ] Rate limits enabled with Redis in production
- [ ] pip-audit / npm audit / Trivy criticals resolved or waived
- [ ] Audit log retention meets policy

## Testing

- [ ] `uv run ruff check backend tests`
- [ ] `uv run ruff format --check backend tests`
- [ ] `uv run mypy backend`
- [ ] `uv run pytest tests -q`
- [ ] Frontend `npm test` and `npm run build`
- [ ] `tests/test_end_to_end.py` and `tests/test_release_validation.py` green

## Deployment

- [ ] Alembic `heads` is a single `20260915_0034`
- [ ] Migrations applied **once**
- [ ] `POST /api/v1/system/release-check` is `PASSED`
- [ ] Rollback image tags recorded

## Backups

- [ ] Successful `backup.sh` + `verify_backup.sh` in this environment
- [ ] Restore drill documented ([disaster-recovery-validation.md](disaster-recovery-validation.md))
- [ ] Retention/cleanup schedule

## Documentation

- [ ] [docs/README.md](README.md) index reviewed
- [ ] Operator runbooks: operations, deployment, DR, security
- [ ] Investigator guides current

## Sign-off

| Role | Name | Date | Result |
| --- | --- | --- | --- |
| Engineering | | | |
| Security | | | |
| Operations | | | |
| Product / investigation lead | | | |

Release is **deployment-ready** only when all boxes are checked and tests pass.
