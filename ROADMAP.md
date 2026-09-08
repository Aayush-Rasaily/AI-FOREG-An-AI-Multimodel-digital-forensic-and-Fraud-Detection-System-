# Roadmap

AI-Forge **v1.0.0** is the first production-ready public release (Phases 1–10
and release cycles RC1–RC8).

## Shipped in 1.0.0

- Case and immutable evidence preservation (SHA-256, custody)
- Processing, extraction, forensic and modality AI
- Deterministic multimodal fusion, correlation, timeline, reporting
- JWT/RBAC, security hardening, audit, interoperability
- Compose/Kubernetes deployment, CI/CD, backup/restore

## Not in 1.0.0

These are **out of scope** for this release (see
[docs/known-limitations.md](docs/known-limitations.md)):

- SSO / MFA
- Additional licensed detectors
- Multi-tenant isolation at extreme scale
- External SIEM connectors
- Celery Beat (not required; workers consume queued jobs)

## After 1.0

Future work must stay additive: inward Clean Architecture dependencies,
immutable originals, and no silent re-scoring inside fusion or reporting.
Patch releases (`1.0.x`) are reserved for defects and security fixes.
Minor releases (`1.x`) may add backward-compatible capabilities.

Versioning policy: [docs/release-engineering.md](docs/release-engineering.md).
Issues: `.github/ISSUE_TEMPLATE/`. Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
