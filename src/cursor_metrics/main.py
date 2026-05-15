"""FastAPI application with health-check endpoint."""

from __future__ import annotations

from pathlib import Path

import structlog
from fastapi import FastAPI
from sqlalchemy import text
from starlette.staticfiles import StaticFiles

from cursor_metrics.config import get_settings
from cursor_metrics.database import async_engine
from cursor_metrics.models.metrics import HealthCheckResponse
from cursor_metrics.routers.auth import router as auth_router
from cursor_metrics.routers.dashboard import router as dashboard_router
from cursor_metrics.routers.ingest import router as ingest_router
from cursor_metrics.routers.reports import router as reports_router

logger = structlog.get_logger()

app = FastAPI(
    title="Cursor Metrics",
    version=get_settings().APP_VERSION,
)
app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(ingest_router)
app.include_router(reports_router)

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


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
