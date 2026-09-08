# Example API requests (v1.0.0)

Base URL: `http://localhost:8000/api/v1`  
Auth: `Authorization: Bearer <access_token>` when `JWT_SECRET` is set.

## Health (public)

```bash
curl -sS http://localhost:8000/api/v1/health/live
```

## Login

```bash
curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"YOUR_PASSWORD\",\"remember_me\":false}"
```

## Create a case

```bash
curl -sS -X POST http://localhost:8000/api/v1/cases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Synthetic training case\",\"priority\":\"MEDIUM\"}"
```

Envelope and errors: [api-reference.md](../docs/api-reference.md).
OpenAPI UI is at `/docs` only when `DEBUG=true`.
