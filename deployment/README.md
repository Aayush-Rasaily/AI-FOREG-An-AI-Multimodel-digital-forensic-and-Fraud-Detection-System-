# Deployment infrastructure (Phase 10A)

Production-ready container, Compose, Kubernetes, Nginx, and ops scripts.

Application readiness APIs remain in `backend/app/deployment/` (Phase 8G).

## Quick start

```bash
cp .env.production.example .env.production
# edit secrets
./deployment/scripts/production_start.sh
```

Full documentation: [docs/deployment.md](../docs/deployment.md)
