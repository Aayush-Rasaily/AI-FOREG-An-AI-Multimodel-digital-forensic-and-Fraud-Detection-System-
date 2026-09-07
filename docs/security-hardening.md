# Enterprise Security Hardening (Phase 10D)

Additive security controls for production AI-Forge deployments.
**No forensic logic, AI model, investigation workflow, or evidence-processing
algorithm changes.** Existing Phase 8F governance under `backend/app/security/`
remains intact; Phase 10D modules extend the same package.

## Controls

| Control | Module |
| --- | --- |
| HTTP security headers + HSTS | `security/headers.py`, middleware |
| Content Security Policy | `security/csp.py` |
| Rate limiting (Redis + memory) | `security/ratelimit.py` |
| Upload hardening | `security/uploads.py` |
| Secret validation | `security/secrets.py` |
| Log redaction | `security/secrets.redact_secrets` + `core/logging.py` |
| Dependency scanning | `security/dependency_scan.py`, `scripts/security_scan.sh` |
| Hardening audit helpers | `security/audit.py` |

## HTTP headers

API responses set (via `setdefault`, so edge proxies may override):

- `Strict-Transport-Security` (production/staging over HTTPS)
- `Content-Security-Policy` (`default-src 'none'` for API)
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: no-referrer`
- `Permissions-Policy` (camera/mic/geo disabled)
- `Cross-Origin-Resource-Policy: same-origin`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`
- `Cache-Control: no-store`

Frontend nginx should emit a SPA-friendly CSP (`frontend_content_security_policy`).

## Rate limiting

Configurable categories with burst + sustained windows:

- Authentication
- Evidence upload
- AI analysis POSTs
- Report generation
- Search
- Export / interoperability

Limits are keyed by client IP and (when present) Authorization material.
Redis is preferred; in-memory fallback keeps local/test environments working.
Disable with `RATE_LIMIT_ENABLED=false` (tests default off).

## Upload security

Before ingestion, uploads reject:

- Null bytes / control characters
- Path traversal and absolute paths
- Dangerous double extensions
- Executable extensions
- Oversized payloads
- MIME/extension policy violations
- ZIP member traversal for DOCX archives

## Secret management

Production startup refuses to boot when required secrets fail validation
(`JWT_SECRET`, database/redis configuration, weak/placeholder secrets).
Extended checks also warn about optional API/encryption keys.

## Secure logging

`JsonFormatter` redacts passwords, tokens, API keys, cookies, Authorization
headers, and JWT-shaped strings before writing log lines.

## Dependency security

```bash
bash scripts/security_scan.sh
```

Writes JSON/text reports under `reports/security/`. Missing `pip-audit` /
`npm audit` tools are skipped but manifests are still validated.

## Deployment recommendations

1. Terminate TLS at the reverse proxy (TLS 1.2+); enable HSTS at the edge.
2. Set `APP_ENV=production`, `DEBUG=false`, and inject secrets via a vault/KMS.
3. Restrict CORS origins to known frontend hosts.
4. Keep Redis available for distributed rate limiting across API replicas.
5. Run `scripts/security_scan.sh` in CI and review `reports/security/`.
6. Place the API and workers on a private network; expose only the proxy.
7. Enforce short access-token TTL (≤ 60 minutes) and rotate refresh tokens.

## Firewall guidance

- Allow inbound 443 (HTTPS) to the reverse proxy only.
- Deny direct public access to PostgreSQL, Redis, RabbitMQ, and worker ports.
- Allow egress only for required package mirrors / model registries.
- Separate management/SSH access onto a bastion or VPN.

## TLS / reverse proxy

Use `deployment/nginx/nginx-tls.conf.example` as a starting point:

- `ssl_protocols TLSv1.2 TLSv1.3;`
- Forward `X-Forwarded-Proto` so the API can emit HSTS correctly
- Keep `client_max_body_size` aligned with `MAX_UPLOAD_SIZE_MB`
- Prefer edge headers for SPA CSP; API CSP remains restrictive

## Production checklist

- [ ] Secrets injected; no placeholders
- [ ] `JWT_SECRET` ≥ 32 characters
- [ ] TLS certificates valid and auto-renewed
- [ ] HSTS enabled at proxy and/or API
- [ ] Rate limiting enabled with Redis
- [ ] CORS origins explicitly listed
- [ ] Security scan reports reviewed
- [ ] Logs verified free of secrets
- [ ] Backup / restore tested
- [ ] Phase 10B monitoring scrapes healthy
