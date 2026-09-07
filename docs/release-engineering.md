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
| Security | `.github/workflows/security.yml` | called by CI |
| Docker | `.github/workflows/docker.yml` | called by CI (build) and Release (publish) |
| Release | `.github/workflows/release.yml` | tags `v*.*.*` or manual dispatch |

CI fails immediately when any reusable job fails (`quality-gate` requires all).

### Quality gates (every PR / push)

- Ruff lint + format
- MyPy
- Backend pytest
- Frontend Vitest
- Frontend production build
- Alembic single-head verification
- OpenAPI 3.x schema validation
- pip-audit / npm audit (critical)
- Dependency review on pull requests
- Filesystem + container Trivy scans (critical, unfixed)
- Backend and frontend Docker image builds

## Branching strategy

```
main            production-ready, protected
feature/*       additive work via pull request
fix/*           backward-compatible defect fixes
hotfix/*        production emergency; merge to main and tag a patch
```

- Pull requests are the only path onto `main`.
- Do not rewrite forensic/AI/investigation engines in release PRs.
- Protect `main` with required checks: `CI / Quality gate`.

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
- `ghcr.io/<owner>/ai-forge-frontend`

Multi-platform (`linux/amd64,linux/arm64`) on publish; CI builds `linux/amd64`.

## Release workflow

1. Merge to `main` with green CI.
2. Bump `pyproject.toml` version (and keep `CHANGELOG.md` in the same PR when possible).
3. Tag `vX.Y.Z` and push the tag.
4. `release.yml` re-runs CI, generates notes/changelog artifacts, creates a GitHub Release, and publishes containers.
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
- [security-hardening.md](security-hardening.md) — dependency scans
