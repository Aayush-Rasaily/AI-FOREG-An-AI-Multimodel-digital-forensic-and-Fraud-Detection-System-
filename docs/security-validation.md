# Security validation (Phase 10I + RC3)

Automated checks live in `tests/test_release_validation.py`,
`tests/test_phase10d_security.py`, and `tests/test_rc3_security.py`.
This page records **what v1.0.0 verifies**. Full RC3 write-up:
[security-rc3.md](security-rc3.md).

| Control | Result |
| --- | --- |
| TLS configuration | `nginx-tls.conf.example` requires TLSv1.2/1.3 and HSTS |
| Security headers | `nosniff`, `DENY` frame, CSP, COOP/COEP/CORP, Permissions-Policy |
| Authentication | Unauthenticated `/cases` → 401; login issues Bearer; health stays public |
| Authorization | Viewer cannot `POST /cases` (403); `POST /cases` maps to `case.create` |
| Secrets | Production profile fails closed on missing/weak JWT and debug-on |
| Upload security | Path traversal rejected; dangerous extensions blocked |
| Mass assignment | Extra fields on login/case create rejected |
| OpenAPI | Hidden when `DEBUG=false` |
| Audit / redaction | Secret-like strings replaced with `[REDACTED]`; 401/403 logged |
| Edge metrics | Public Nginx returns 404 for `/api/v1/metrics` |
| Dependency scans | Manifests required; CI `security.yml` fails on **critical** |

CI also runs pip-audit, npm audit (`--audit-level=critical`), dependency
review, and Trivy (filesystem + images).

See [security-hardening.md](security-hardening.md) and
[authentication.md](authentication.md).
