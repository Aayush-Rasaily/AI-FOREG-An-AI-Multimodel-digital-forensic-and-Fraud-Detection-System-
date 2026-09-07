# Security validation (Phase 10I)

Automated checks live in `tests/test_release_validation.py` and Phase 10D
tests. This page records **what v1.0.0 verifies**.

| Control | Result |
| --- | --- |
| TLS configuration | `nginx-tls.conf.example` requires TLSv1.2/1.3 and HSTS |
| Security headers | `nosniff`, `DENY` frame, CSP, COOP/COEP/CORP, Permissions-Policy |
| Authentication | Unauthenticated `/cases` → 401; login issues Bearer; health stays public |
| Authorization | `POST /cases` maps to `case.create` |
| Secrets | Production profile fails closed on missing/weak JWT and debug-on |
| Upload security | Path traversal rejected; dangerous extensions blocked |
| Audit / redaction | Secret-like strings replaced with `[REDACTED]` |
| Dependency scans | Manifests required; CI `security.yml` fails on **critical** |

CI also runs pip-audit, npm audit (`--audit-level=critical`), dependency
review, and Trivy (filesystem + images).

See [security-hardening.md](security-hardening.md) and
[authentication.md](authentication.md).
