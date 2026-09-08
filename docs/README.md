# Documentation index

Enterprise documentation for AI-Forge **v1.0.0**. Live OpenAPI remains at
`/docs` when `DEBUG=true`. This tree does not change runtime behavior.

## Start here

| Audience | Document |
| --- | --- |
| Everyone | [architecture-overview.md](architecture-overview.md) |
| Investigators | [user-guide.md](user-guide.md) / [investigator-guide.md](investigator-guide.md) |
| Administrators | [administrator-guide.md](administrator-guide.md) |
| Operators | [operations-guide.md](operations-guide.md) / [deployment-guide.md](deployment-guide.md) |
| Developers | [developer-guide.md](developer-guide.md) / [development.md](development.md) |
| Integrators | [api-reference.md](api-reference.md) |
| Reviewers | [forensic-methodology.md](forensic-methodology.md), [security-rc3.md](security-rc3.md) |

## Architecture

- [architecture-overview.md](architecture-overview.md) — system map, Clean Architecture, request lifecycle
- [backend-architecture.md](backend-architecture.md) — layers, processing, fusion, correlation, reporting
- [frontend-architecture.md](frontend-architecture.md) — SPA routes, data flow, RBAC
- [ai-architecture.md](ai-architecture.md) — registry, modality engines, jury fusion
- [database-schema.md](database-schema.md) — persistence map and relationships
- [architecture.md](architecture.md) — original boundary rules (still authoritative)

## Operations

- [operations-guide.md](operations-guide.md)
- [administrator-guide.md](administrator-guide.md)
- [deployment-guide.md](deployment-guide.md)
- [maintenance-guide.md](maintenance-guide.md)
- [operations.md](operations.md) — probes and in-cluster validation (Phase 8G)
- [deployment.md](deployment.md) — compose/k8s/nginx
- [monitoring.md](monitoring.md) / [system-monitoring.md](system-monitoring.md)
- [performance.md](performance.md) — Phase 10C indexes/cache
- [performance-rc2.md](performance-rc2.md) — RC2 gzip + benchmark suite
- [disaster-recovery.md](disaster-recovery.md)
- [security-hardening.md](security-hardening.md)
- [security-rc3.md](security-rc3.md) — RC3 review outcomes
- [release.md](release.md) / [release-engineering.md](release-engineering.md)
- [release-checklist.md](release-checklist.md) — v1.0.0 sign-off
- [production-readiness.md](production-readiness.md) — RC6 operational review
- [release-engineering.md](release-engineering.md) — CI/CD and tagging
- [versions.md](versions.md) — engine and policy identifiers
- [benchmark-summary.md](benchmark-summary.md)
- [security-validation.md](security-validation.md)
- [disaster-recovery-validation.md](disaster-recovery-validation.md)
- [known-limitations.md](known-limitations.md)

## Investigators

- [user-guide.md](user-guide.md)
- [investigator-guide.md](investigator-guide.md)
- [forensic-methodology.md](forensic-methodology.md)
- [evidence-management.md](evidence-management.md)
- [ai-analysis-guide.md](ai-analysis-guide.md)
- [reporting-guide.md](reporting-guide.md)
- [case-evidence.md](case-evidence.md)
- [processing-pipeline.md](processing-pipeline.md)
- [fusion-ai.md](fusion-ai.md)
- [correlation-engine.md](correlation-engine.md)
- [timeline-engine.md](timeline-engine.md)
- [forensic-reporting.md](forensic-reporting.md) / [reporting.md](reporting.md)

## Developers

- [developer-guide.md](developer-guide.md)
- [development.md](development.md)
- [contributing.md](contributing.md)
- [support.md](support.md)
- [rc7-certification.md](rc7-certification.md)
- [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
- [coding-standards.md](coding-standards.md)
- [authentication.md](authentication.md)

## API

- [api-reference.md](api-reference.md) — every `/api/v1` operation
