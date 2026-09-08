# Changelog

All notable releases of AI-Forge follow [Semantic Versioning](https://semver.org/).

## 1.0.0 — 2026-09-07

### Security

- RC3: production security review; 401/403 logging; `extra="forbid"` on auth
  and case write models; API image no longer trusts all forwarded IPs;
  public Nginx hides `/api/v1/metrics`.

### Documentation

- RC4: user, administrator, developer, deployment, and forensic methodology
  guides aligned to the implemented v1.0 platform.

### Features

- First production-ready release of the AI-Forge platform (Phases 1–10I).
- Case/evidence preservation, processing, extraction, forensic and modality AI,
  multimodal fusion, correlation, timeline, reporting, and interoperability.
- Enterprise identity (JWT/RBAC), monitoring, production deployment,
  performance, security hardening, scalability, disaster recovery, and CI/CD.

### Other

- Phase 10H enterprise documentation set.
- Phase 10I end-to-end validation, benchmarks, and release checklist.
- RC1 quality cleanup and RC2 performance validation.
- RC5: CI docs workflow, Dependabot, Alembic upgrade/downgrade, artifact
  retention, Gitleaks, worker image in Docker CI.
- RC6: production worker Dockerfile, TLS redirect and edge rate limit,
  production-readiness review.
- RC7: release-candidate certification and UAT checklist.
- RC8: public v1.0 packaging (SECURITY, CoC, ROADMAP, sample assets).

## 0.1.0 — 2026-09-07

### Other

- Pre-release enterprise train covering Phases 1–10G scaffolding.
