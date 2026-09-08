# Support and long-term maintenance — AI-Forge 1.0

## Supported environments

| Layer | Supported |
| --- | --- |
| OS | Linux (primary), Windows 10/11 (development), macOS (development) |
| Python | 3.12 |
| Node.js | 22 |
| PostgreSQL | 16+ |
| Redis | 7+ |
| RabbitMQ | 3.13+ (when using Celery) |
| Docker | Compose production file under `deployment/compose/` |

Production is validated on Linux containers. Windows/macOS are for local
development (`uv`, Vite, optional Docker Desktop).

## Versioning

Semantic Versioning. Tags are `vMAJOR.MINOR.PATCH`. The GitHub Release
workflow requires the tag to match `pyproject.toml`.

| Change | Version |
| --- | --- |
| Breaking API or schema | MAJOR |
| Additive compatible capability | MINOR |
| Defect or security fix | PATCH |

## Deprecation

v1.0 does not deprecate `/api/v1`. Future major versions will announce
deprecations in CHANGELOG and keep a migration window.

## Maintenance expectations

- Security issues: [SECURITY.md](../SECURITY.md)
- Quality gates on every PR: [release-engineering.md](release-engineering.md)
- No rewrite of forensic engines in patch releases

## Issues and contributions

- Bugs/features: `.github/ISSUE_TEMPLATE/`
- Process: [contributing.md](contributing.md) / [CONTRIBUTING.md](../CONTRIBUTING.md)
- Conduct: [CODE_OF_CONDUCT.md](../CODE_OF_CONDUCT.md)
