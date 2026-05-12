"""FastAPI application with health-check endpoint."""

from __future__ import annotations

import structlog
from fastapi import FastAPI
from sqlalchemy import text

from cursor_metrics.config import get_settings
from cursor_metrics.database import async_engine
from cursor_metrics.models.metrics import HealthCheckResponse

logger = structlog.get_logger()

app = FastAPI(
    title="Cursor Metrics",
    version=get_settings().APP_VERSION,
)


@app.get("/", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Return application health including database connectivity."""
    settings = get_settings()
    db_status = "connected"

    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        logger.warning("database_health_check_failed", exc_info=True)
        db_status = "disconnected"

    return HealthCheckResponse(
        status="ok",
        version=settings.APP_VERSION,
        database=db_status,
    )
