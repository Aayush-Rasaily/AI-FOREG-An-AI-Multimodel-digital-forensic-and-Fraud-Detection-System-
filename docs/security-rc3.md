# Security review — Release Cycle 3 (RC3)

Production security hardening and validation for AI-Forge **v1.0.0**.
No forensic engines, schemas, or investigation APIs were redesigned.

Related: [security-hardening.md](security-hardening.md),
[security-validation.md](security-validation.md),
[authentication.md](authentication.md),
[security-governance.md](security-governance.md).

## Review outcomes

| Area | Result | Notes |
| --- | --- | --- |
| FastAPI auth + RBAC | Pass | All `/api/v1` routes use `require_request_authorization`. Public set is `PUBLIC_PATHS` only. |
| HTTP 401 / 403 / 404 | Pass | Missing token → `UNAUTHENTICATED` (401). Missing permission → `FORBIDDEN` (403). Missing case → 404. Failures are logged without secrets. |
| Pydantic / mass assignment | Pass | Auth and case write models use `extra="forbid"`. Services bind schema fields only. |
| Injection / SQL | Pass | SQLAlchemy ORM; `text("SELECT 1")` and sequence `nextval` are parameterized/static. |
| Uploads / evidence | Pass | Basename-only names, SHA-256, allow-listed types, no execution of uploads, archive traversal blocked. |
| Secrets / config | Pass | Placeholders in `.env.example` only. Production fails closed on missing/weak `JWT_SECRET` and `DEBUG=true`. |
| CORS / OpenAPI | Pass | `allow_credentials=False`. OpenAPI `/docs` and `/openapi.json` disabled when `DEBUG=false`. |
| Rate limits / headers | Pass | Phase 10D middleware unchanged in behavior. |
| Logging / audit | Pass | JSON logs + redaction; 401/403 recorded with method/path/status. Evidence actions remain on the audit trail. |
| Frontend | Pass | `ProtectedRoute` / `RoleGuard`; React text rendering; tokens in sessionStorage unless remember-me. |
| Containers / edge | Pass | API image `USER appuser`; trusted proxy CIDRs (not `*`); public proxies return 404 for `/api/v1/metrics`. Scrape the API ClusterIP instead. |
| Dependencies | Pass | CI `security.yml` fails on **critical** pip-audit / npm audit / Trivy. |

## Residual / operator-owned items (not product defects)

- **Remember-me** keeps refresh tokens in `localStorage`. Prefer session-only sign-in on shared workstations.
- **Prometheus** must scrape `http://<api-service>:8000/api/v1/metrics` on the cluster network, not the public HTTPS vhost.
- **`--forwarded-allow-ips`** trusts RFC1918 plus loopback. If your ingress uses another CIDR, override the container command.
- **Case list** is permission-scoped (`case.view`), not automatically isolated per case unless Security Governance case-access records are used.
- Nginx master still binds port 80 as root in the official Alpine image; static files are owned by `nginx` and not writable.

## Tests

- `tests/test_rc3_security.py`
- `tests/test_phase10d_security.py`
- `tests/test_phase8a_authentication.py`
- `tests/test_release_validation.py`
- `frontend/src/test/phase_rc3_security.test.tsx`

## Remediation in this cycle

- Log authorization denials with correlation-safe extras.
- Reject unknown fields on login, user, and case write payloads.
- Stop trusting all `X-Forwarded-*` sources in the API image.
- Do not expose Prometheus metrics through public Nginx `/api/` locations.
- Document production posture for v1.0 operators.
