# Administrator guide

For operators with `admin.manage_users`, `system.monitor`, and
`security.manage`. Investigators should use
[investigator-guide.md](investigator-guide.md).

## Identity

Authentication is required in production when `JWT_SECRET` is set. Default
roles: Administrator, Investigator, Analyst, Reviewer, Viewer. Permission
codes are listed in [authentication.md](authentication.md).

UI: `/users` (create/deactivate users, assign roles), `/security` (policy,
violations, case access), `/profile` (password change).

API: `POST /api/v1/users`, `PATCH /api/v1/users/{id}`, `GET /api/v1/sessions`,
`DELETE /api/v1/sessions/{id}`.

Password policy: 12–128 characters, mixed case, digit, special character,
Argon2id, lockout after repeated failures.

## Case access

Use `GET/PATCH /api/v1/cases/{case_id}/access` and the Security Governance
page to constrain who can open a case beyond role defaults.

## Platform health

- `/platform-health` — `platform_validation.*`
- `/analytics` — investigation analytics
- `/system`, `/deployment`, `/monitoring` — diagnostics, release identity,
  metrics

Run `POST /api/v1/system/diagnostics/run` and
`POST /api/v1/platform/validate` during change windows.

## Configuration

Secrets belong in the environment or a secret manager, never in git.
`.env.example` and `.env.production.example` are placeholders.

Production must disable debug, require JWT, and use a non-placeholder secret
of sufficient length ([security-hardening.md](security-hardening.md)).

## Backups and retention

Schedule `deployment/scripts/backup.sh`. Retention:
[disaster-recovery.md](disaster-recovery.md) and
[maintenance-guide.md](maintenance-guide.md).

## Interoperability

`/interoperability` exports/imports investigation packages
(`interop.export` / `interop.import`). Treat packages as sensitive; downloads
are rate-limited.
