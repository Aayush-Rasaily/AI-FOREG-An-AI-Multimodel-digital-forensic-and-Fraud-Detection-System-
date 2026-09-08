# Release Engineering (Phase 10G)

Automated CI/CD for AI-Forge. **No forensic logic, AI model, API, or schema
changes** — this phase only automates quality gates, images, and packaging.

Phase 8G runtime release checks (`docs/release.md`) remain the in-cluster
gate. This document covers GitHub Actions, SemVer, and image publishing.

## Workflows

| Workflow | Path | Trigger |
| --- | --- | --- |
| CI | `.github/workflows/ci.yml` | push to `main`, pull requests |
| Backend | `.github/workflows/backend.yml` | called by CI |
| Frontend | `.github/workflows/frontend.yml` | called by CI |
| Docs | `.github/workflows/docs.yml` | called by CI |
| Security | `.github/workflows/security.yml` | called by CI |
| Docker | `.github/workflows/docker.yml` | called by CI (build) and Release (publish) |
| Release | `.github/workflows/release.yml` | tags `v*.*.*` or manual dispatch |

Dependabot: `.github/dependabot.yml` (weekly pip, npm, Actions, Docker).

CI fails immediately when any reusable job fails (`quality-gate` requires all).

### Quality gates (every PR / push)

- Ruff lint + format
- MyPy
- Backend pytest (JUnit artifact)
- Frontend TypeScript (`npm run lint`), Vitest, production build
- Documentation set present
- Alembic single-head verification **and** upgrade / `downgrade -1` / upgrade on PostgreSQL 16
- OpenAPI 3.x schema validation
- Version consistency (`pyproject.toml`, `VERSION`, `frontend/package.json`)
- `uv lock --check`
- pip-audit / npm audit (critical)
- Gitleaks secret detection
- Dependency review on pull requests
- Filesystem + container Trivy scans (critical, unfixed)
- Docker Compose production `config`
- Backend, frontend, and worker Docker image builds

## Branching strategy

```
main            production-ready, protected
feature/*       additive work via pull request
fix/*           backward-compatible defect fixes
hotfix/*        production emergency; merge to main and tag a patch
```

- Pull requests are the only path onto `main`.
- Do not rewrite forensic/AI/investigation engines in release PRs.
- Protect `main` with required checks: **CI / Quality gate**.

## Artifact retention

GitHub Actions artifacts (default **14 days**):

| Artifact | Source |
| --- | --- |
| `backend-ci-reports` | pytest JUnit XML |
| `frontend-dist` | production Vite bundle |
| `pip-audit-report` | `reports/security/` |
| `ai-forge-<version>` | release notes, `version.json`, container manifest |

## Local pipeline reproduction

```bash
uv lock --check
uv sync --locked --dev
uv run ruff check backend tests
uv run ruff format --check backend tests
uv run mypy backend
uv run pytest tests -q --tb=short
uv run alembic -c backend/alembic.ini upgrade head
cd frontend && npm ci && npm run lint && npm test && npm run build
docker compose -f deployment/compose/docker-compose.production.yml --env-file .env.production.example config
```

## Troubleshooting CI

| Symptom | Check |
| --- | --- |
| Quality gate skipped | A required job failed; open that job log |
| Alembic round-trip failed | Migration `downgrade` on PostgreSQL 16; do not ship dual heads |
| Gitleaks failed | Remove live secrets; placeholders belong in `*.example` files |
| Docker job failed | Dockerfile path, Compose `:?` env vars, Trivy **critical** |
| Release job failed | Tag `vX.Y.Z` must equal `pyproject.toml` version |

## Versioning policy (SemVer)

Declared in `pyproject.toml` and `VERSION` (`1.0.0`).

| Increment | When |
| --- | --- |
| MAJOR | Breaking API, schema, or workflow changes (explicit product decision) |
| MINOR | Additive backward-compatible capabilities |
| PATCH | Fixes, CI, docs, operational hardening |

Pre-release identifiers (`1.2.3-rc.1`) are allowed. Git tags are `vMAJOR.MINOR.PATCH`.
The release job fails if the tag does not match `pyproject.toml`.

Image tags published to GHCR:

- `latest`
- semantic version (`0.1.0`)
- 12-character commit SHA

Images:

- `ghcr.io/<owner>/ai-forge-api`
- `ghcr.io/<owner>/ai-forge-api-worker`
- `ghcr.io/<owner>/ai-forge-frontend`

Multi-platform (`linux/amd64,linux/arm64`) on publish; CI builds `linux/amd64`.

## Release workflow

1. Merge to `main` with green CI.
2. Bump `pyproject.toml` version (and keep `CHANGELOG.md` in the same PR when possible).
3. Tag `vX.Y.Z` and push the tag.
4. `release.yml` re-runs CI, attaches notes **from CHANGELOG.md**, creates a GitHub Release, and publishes containers.
5. Deploy using Phase 8G/10A runbooks (`docs/release.md`, `docs/deployment.md`).
6. Run in-cluster `POST /api/v1/system/release-check`.

Manual dispatch of `release.yml` accepts a version input without a leading `v`.

## Hotfix workflow

1. Branch `hotfix/x.y.z` from the production tag or current `main`.
2. Minimal, backward-compatible fix.
3. PR into `main`; CI must pass.
4. Patch bump + tag `vX.Y.Z`.
5. Deploy with the same rollback notes as a standard release.

## Rollback process

1. Redeploy the previous image tags (`:X.Y.Z` or SHA).
2. If a forward-incompatible migration shipped, restore the pre-deploy database dump (`docs/disaster-recovery.md`).
3. Confirm liveness/readiness and `release-check`.
4. Do not re-run AI or rewrite forensic artifacts to “undo” a release.

## Helpers

`backend/app/cicd/` provides SemVer parsing, Alembic/OpenAPI gates, changelog
generation, and version metadata JSON used by GitHub Actions. Application
runtime behavior is unchanged.

## Related docs

- [release.md](release.md) — in-cluster release identity
- [deployment.md](deployment.md) — compose/k8s/nginx
- [disaster-recovery.md](disaster-recovery.md) — restore/rollback
- [production-readiness.md](production-readiness.md) — v1.0 ops sign-off
- [security-hardening.md](security-hardening.md) — dependency scans
