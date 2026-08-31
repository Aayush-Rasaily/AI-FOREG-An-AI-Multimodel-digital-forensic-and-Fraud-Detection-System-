FROM python:3.12-slim AS runtime

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

RUN useradd --create-home --uid 10001 appuser \
    && chown --recursive appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
