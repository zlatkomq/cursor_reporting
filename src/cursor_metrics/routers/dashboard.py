"""Dashboard router — HTML views rendered via Jinja2 + HTMX."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from cursor_metrics.database import get_db
from cursor_metrics.dependencies import get_current_user
from cursor_metrics.repositories.metrics_repo import MetricsRepository
from cursor_metrics.services.metrics_service import MetricsService
from cursor_metrics.services.pricing_service import PricingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="", tags=["dashboard"])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _build_metrics_service(session: AsyncSession) -> MetricsService:
    return MetricsService(
        repository=MetricsRepository(session),
        pricing_service=PricingService(session),
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_overview(
    request: Request,
    current_user: str = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> HTMLResponse:
    """Render the main dashboard overview page."""
    service = _build_metrics_service(session)
    overview = await service.get_overview(days)

    daily_dates = [entry["date"] for entry in overview["daily_counts"]]
    daily_counts = [entry["count"] for entry in overview["daily_counts"]]

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        context={
            "current_user": current_user,
            "overview": overview,
            "current_days": days,
            "daily_dates": daily_dates,
            "daily_counts": daily_counts,
        },
    )


@router.get("/dashboard/by-model", response_class=HTMLResponse)
async def dashboard_by_model(
    request: Request,
    current_user: str = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> HTMLResponse:
    """Render the by-model usage and cost page."""
    service = _build_metrics_service(session)
    data = await service.get_by_model(days)

    return templates.TemplateResponse(
        request,
        "by_model.html",
        context={
            "current_user": current_user,
            "data": data,
            "models": data["models"],
            "current_days": days,
            "filter_url": "/dashboard/by-model",
        },
    )


@router.get("/dashboard/by-developer", response_class=HTMLResponse)
async def by_developer_page(
    request: Request,
    current_user: str = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> HTMLResponse:
    """Render the by-developer rankings page."""
    service = _build_metrics_service(session)
    data = await service.get_by_developer(days=days)

    return templates.TemplateResponse(
        request,
        "by_developer.html",
        context={
            "current_user": current_user,
            "developers": data["developers"],
            "current_days": data["period_days"],
            "filter_url": "/dashboard/by-developer",
        },
    )
