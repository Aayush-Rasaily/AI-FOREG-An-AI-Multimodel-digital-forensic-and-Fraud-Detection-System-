# AI-Forge 1.0.0 release notes

**Released:** 2026-09-07  
**Version:** 1.0.0 (Semantic Versioning)  
**Schema / Alembic head:** `20260915_0034`

This is the first production-ready train of AI-Forge. It is **backward
compatible** with Phases 1–10 APIs and investigation workflows. No forensic
engines, AI models, or schemas were rewritten for this release.

## What is included

- Investigation workspace: cases, immutable evidence, processing, extraction
- Forensic analysis and modality AI (image, document, video, audio, signature)
- Multimodal fusion jury, correlation, entities, timeline, reports, exports
- JWT/RBAC, security headers, rate limits, upload validation, audit
- Compose/Kubernetes/Nginx deployment, HPA/workers, backup/restore
- GitHub Actions CI/CD with SemVer image tags (`latest`, version, SHA)

## Images

- `ghcr.io/<owner>/ai-forge-api:1.0.0`
- `ghcr.io/<owner>/ai-forge-frontend:1.0.0`

Also tag `latest` and the 12-character git SHA.

## Validation

Automated gates: Ruff, MyPy, pytest (`tests/test_end_to_end.py`,
`tests/test_release_validation.py`), Vitest, production frontend build,
Alembic head, OpenAPI, container builds, security scans.

Operator checklist: [docs/release-checklist.md](docs/release-checklist.md).

## Upgrade from 0.1.0

1. Backup using `deployment/scripts/backup.sh`.
2. Deploy 1.0.0 images.
3. Confirm Alembic is already at `20260915_0034` (no new schema in 10I).
4. Run `POST /api/v1/system/release-check`.

## Rollback

Redeploy previous image tags. Restore the database only if a later incompatible
migration was applied (none ships in 1.0.0). See
[docs/disaster-recovery.md](docs/disaster-recovery.md).
