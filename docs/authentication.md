# Authentication, Authorization & RBAC (Phase 8A)

AI-Forge Phase 8A adds enterprise identity and role-based access control
without modifying forensic analysis, AI engines, timeline, correlation,
entity resolution, or reporting logic.

## Authentication flow

1. Client submits `POST /api/v1/auth/login` with username, password, and optional `remember_me`.
2. Server validates credentials (Argon2id), enforces lockout and IP throttling, and opens a session.
3. Server returns a short-lived JWT access token and a refresh token.
4. Client sends `Authorization: Bearer <access_token>` on subsequent API calls.
5. When the access token expires, client calls `POST /api/v1/auth/refresh`.
6. Logout revokes the current session and associated refresh tokens.

Authentication is enforced when `JWT_SECRET` is configured. Existing Phase 1–7
test suites remain compatible when the secret is unset.

## JWT lifecycle

| Token | Lifetime (default) | Storage |
| --- | --- | --- |
| Access | 15 minutes | Client memory / storage |
| Refresh | 7 days (30 days with remember me) | Hashed in `refresh_tokens` |

Access tokens include `sub` (user id), `sid` (session id), `typ=access`, `iat`, `exp`, and `jti`.
Refresh tokens use `typ=refresh` and are rotated on each refresh.

Session revocation immediately invalidates subsequent access-token use even if the JWT has not expired.

## Permission model

Permissions are deterministic string codes, for example:

- `case.create`, `case.view`, `case.edit`, `case.delete`
- `evidence.upload`, `evidence.view`, `evidence.delete`
- `ai.run`, `ai.view`
- `fusion.run`, `fusion.view`
- `timeline.run`, `timeline.view`
- `correlation.run`, `correlation.view`
- `entity.run`, `entity.view`
- `report.generate`, `report.view`, `report.download`, `report.approve`
- `audit.view`
- `admin.manage_users`
- `system.monitor`
- `comment.create`

Server-side enforcement maps HTTP method + path to a required permission and rejects unauthorized callers with `403 FORBIDDEN`.

## RBAC matrix

| Capability | Administrator | Investigator | Analyst | Reviewer | Viewer |
| --- | --- | --- | --- | --- | --- |
| Manage users | Yes | No | No | No | No |
| System monitor | Yes | No | No | No | No |
| Case CRUD | Yes | Yes | View | View | View |
| Evidence upload/delete | Yes | Yes | View | View | View |
| Run AI / fusion | Yes | Yes | Yes | View | No |
| Generate reports | Yes | Yes | View | View / approve / download | View |
| Audit view | Yes | Yes | No | Yes | No |

## Password policy

- Length 12–128 characters
- Must include uppercase, lowercase, digit, and special character
- Argon2id hashing with automatic rehash support
- Failed login counter with temporary account lockout
- IP failure throttling window

## Session management

Sessions track:

- login timestamp
- last activity
- expiration
- device name / browser
- IP address
- remember-me flag
- revocation timestamp

Supported operations:

- list current sessions
- revoke one session
- revoke all sessions for the current user
- password change revokes other sessions

## Security considerations

- Bearer tokens in the `Authorization` header (CSRF not applicable to this transport)
- Refresh tokens stored only as SHA-256 hashes
- Generic login failure messages
- Account lockout after repeated failures
- Permission checks are always server-side
- Health liveness endpoints remain public
- OAuth / LDAP / SSO / MFA are out of scope for Phase 8A

## API surface

- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/password`
- `POST|GET|PATCH|DELETE /users`
- `GET /roles`
- `GET /permissions`
- `GET|DELETE /sessions`

## Frontend

- Login page
- Profile page (password + sessions)
- User management page (Administrator)
- Protected routes and role guards
- Permission-aware navigation
- Unauthorized page and session-expired refresh handling

## Bootstrap

When `JWT_SECRET` and `AUTH_BOOTSTRAP_PASSWORD` are set and no users exist,
the service seeds built-in roles/permissions and creates the bootstrap administrator
(`AUTH_BOOTSTRAP_USERNAME`, default `admin`).
