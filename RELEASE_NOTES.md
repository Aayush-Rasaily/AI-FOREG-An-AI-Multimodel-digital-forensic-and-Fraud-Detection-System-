# AI-Forge 1.0.0 release notes

**Released:** 2026-09-07  
**Version:** 1.0.0 (Semantic Versioning)  
**Schema / Alembic head:** `20260915_0034`

This is the first production-ready train of AI-Forge. It is **backward
compatible** with Phases 1–10 APIs and investigation workflows. No forensic
engines, AI models, or schemas were rewritten for this release.

Release cycles **RC3–RC8** (security, documentation, CI/CD, production ops,
release-candidate certification, and public packaging) are included in 1.0.0.
They add no investigation features.

## What is included

- Investigation workspace: cases, immutable evidence, processing, extraction
- Forensic analysis and modality AI (image, document, video, audio, signature)
- Multimodal fusion jury, correlation, entities, timeline, reports, exports
- JWT/RBAC, security headers, rate limits, upload validation, audit
- Compose/Kubernetes/Nginx deployment, HPA/workers, backup/restore
- GitHub Actions CI/CD with SemVer image tags (`latest`, version, SHA)
- RC3 security review ([docs/security-rc3.md](docs/security-rc3.md))
- RC4 documentation set ([docs/README.md](docs/README.md))
- RC5 CI/CD ([docs/release-engineering.md](docs/release-engineering.md))
- RC6 production readiness ([docs/production-readiness.md](docs/production-readiness.md))
- RC7 certification ([docs/rc7-certification.md](docs/rc7-certification.md))
- Sample assets ([samples/README.md](samples/README.md))

## Images

- `ghcr.io/<owner>/ai-forge-api:1.0.0`
- `ghcr.io/<owner>/ai-forge-api-worker:1.0.0`
- `ghcr.io/<owner>/ai-forge-frontend:1.0.0`

Also tag `latest` and the 12-character git SHA.

## Validation

Automated gates: Ruff, MyPy, pytest (`tests/test_end_to_end.py`,
`tests/test_release_validation.py`, `tests/test_rc3_security.py`), Vitest,
production frontend build, Alembic head, OpenAPI, container builds, security
scans.

Operator checklist: [docs/release-checklist.md](docs/release-checklist.md).
Known limitations: [docs/known-limitations.md](docs/known-limitations.md).

## Upgrade from 0.1.0

1. Backup using `deployment/scripts/backup.sh`.
2. Deploy 1.0.0 images.
3. Confirm Alembic is already at `20260915_0034` (no new schema in 10I/RC3/RC4).
4. Run `POST /api/v1/system/release-check`.
5. Point Prometheus at the API service metrics path (public proxy returns 404).

## Rollback

Redeploy previous image tags. Restore the database only if a later incompatible
migration was applied (none ships in 1.0.0). See
[docs/disaster-recovery.md](docs/disaster-recovery.md).
