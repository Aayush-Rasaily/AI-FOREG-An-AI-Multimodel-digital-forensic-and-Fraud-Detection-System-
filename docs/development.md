# Development

## Dependency direction

New use cases belong in `backend/app/application`. Domain contracts belong in
`backend/app/domain/ports`. Concrete database, broker, cache, object-storage,
or provider code belongs in `backend/app/infrastructure`. HTTP translation
belongs in `backend/app/api`.

The composition root is `backend/app/main.py` for the API and
`backend/app/infrastructure/messaging/celery_app.py` for workers. Avoid
creating infrastructure clients inside domain or application modules.

## Database changes

Create migrations with Alembic after persistence models exist. Review every
migration for lock duration, backward compatibility, index strategy, and
rollback behavior. Run migrations once as a release operation; do not run them
from every API replica.

## Quality gates

Use uv to keep dependencies reproducible:

```bash
uv sync --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Tests must cover contracts and failure behavior without requiring live
infrastructure unless explicitly marked as integration tests. Never place
credentials, real evidence, personally identifiable information, or
production connection strings in tests.
