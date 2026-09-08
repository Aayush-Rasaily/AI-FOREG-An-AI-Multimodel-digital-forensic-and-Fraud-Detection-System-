# Production Celery worker image (same runtime as the API, different process).
# Build from repository root:
#   docker build -f deployment/docker/worker.Dockerfile -t ai-forge-worker:prod .

FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.12

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-install-project --no-dev

COPY backend ./backend
COPY configs ./configs
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production \
    DEBUG=false

WORKDIR /app

RUN pip install --no-cache-dir uv==0.11.12

COPY --from=builder /app /app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data /app/data/tmp /app/models \
    && chown --recursive appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=5 \
  CMD python -c "from backend.app.infrastructure.messaging.celery_app import celery_app; celery_app"

CMD ["uv", "run", "--no-dev", "celery", "-A", "backend.app.infrastructure.messaging.celery_app:celery_app", "worker", "--loglevel=INFO", "--concurrency=2"]
