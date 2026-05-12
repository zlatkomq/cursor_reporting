# ---- Build stage: resolve dependencies with uv ----
FROM python:3.12-slim AS build

RUN pip install --no-cache-dir uv==0.5.*

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv venv /app/.venv && \
    uv sync --no-dev --frozen

# ---- Runtime stage: slim production image ----
FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/false --create-home appuser

WORKDIR /app

COPY --from=build /app/.venv /app/.venv

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

USER appuser

ENTRYPOINT ["uvicorn", "cursor_metrics.main:app", "--host", "0.0.0.0", "--port", "8000"]
