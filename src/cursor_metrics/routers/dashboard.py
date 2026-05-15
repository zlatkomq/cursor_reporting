"""Dashboard router — HTML views rendered via Jinja2 + HTMX."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from cursor_metrics.database import get_db
from cursor_metrics.dependencies import get_current_user
from cursor_metrics.repositories.metrics_repo import MetricsRepository
from cursor_metrics.repositories.workflow_repo import WorkflowRepository
from cursor_metrics.services.metrics_service import MetricsService
from cursor_metrics.services.pricing_service import PricingService
from cursor_metrics.services.workflow_service import WorkflowService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="", tags=["dashboard"])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def _is_htmx(request: Request) -> bool:
    return request.headers.get("HX-Request") == "true"


def _build_metrics_service(session: AsyncSession) -> MetricsService:
    return MetricsService(
        repository=MetricsRepository(session),
        pricing_service=PricingService(session),
    )


def _build_workflow_service(session: AsyncSession) -> WorkflowService:
    return WorkflowService(repository=WorkflowRepository(session))


async def _get_overview_data(session: AsyncSession) -> dict:
    """Build the full overview context dict including model_distribution and avg_response_ms."""
    service = _build_metrics_service(session)
    overview = await service.get_overview_with_trends()

    repo = MetricsRepository(session)
    since = datetime.utcnow() - timedelta(days=30)
    models = await repo.events_by_model(since)

    overview["model_distribution"] = {m["model"]: m["event_count"] for m in models}

    durations = [m["avg_duration_ms"] for m in models if m.get("avg_duration_ms") is not None]
    overview["avg_response_ms"] = (
        round(sum(durations) / len(durations), 1) if durations else 0.0
    )

    return overview


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    tab: str = Query(default="overview"),
    current_user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Render the main dashboard page with tab routing."""
    if tab == "funnel":
        wf_service = _build_workflow_service(session)
        summary = await wf_service.get_summary()
        stage_details = await wf_service.get_stage_details("spec")

        context = {
            "request": request,
            "current_user": current_user,
            "funnel": summary,
            "stage_details": stage_details,
            "active_tab": "funnel",
            "tab_template": "partials/funnel_content.html",
            "now": datetime.utcnow(),
        }

        if _is_htmx(request):
            return templates.TemplateResponse(request, "partials/funnel_content.html", context=context)
        return templates.TemplateResponse(request, "dashboard.html", context=context)

    overview = await _get_overview_data(session)

    context = {
        "request": request,
        "current_user": current_user,
        "overview": overview,
        "active_tab": "overview",
        "tab_template": "partials/overview_content.html",
    }

    if _is_htmx(request):
        return templates.TemplateResponse(request, "partials/overview_content.html", context=context)
    return templates.TemplateResponse(request, "dashboard.html", context=context)


@router.get("/dashboard/overview", response_class=HTMLResponse)
async def dashboard_overview(
    request: Request,
    current_user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """HTMX partial endpoint for the overview tab."""
    overview = await _get_overview_data(session)

    context = {
        "request": request,
        "current_user": current_user,
        "overview": overview,
        "active_tab": "overview",
    }
    return templates.TemplateResponse(request, "partials/overview_content.html", context=context)


@router.get("/dashboard/funnel", response_class=HTMLResponse)
async def dashboard_funnel(
    request: Request,
    current_user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """HTMX partial endpoint for the funnel tab."""
    wf_service = _build_workflow_service(session)
    summary = await wf_service.get_summary()
    stage_details = await wf_service.get_stage_details("spec")

    context = {
        "request": request,
        "current_user": current_user,
        "funnel": summary,
        "stage_details": stage_details,
        "active_tab": "funnel",
        "now": datetime.utcnow(),
    }
    return templates.TemplateResponse(request, "partials/funnel_content.html", context=context)


@router.get("/dashboard/funnel-projects", response_class=HTMLResponse)
async def dashboard_funnel_projects(
    request: Request,
    stage: str = Query(default="spec"),
    current_user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """HTMX partial endpoint for stage-filtered projects table."""
    wf_service = _build_workflow_service(session)
    stage_details = await wf_service.get_stage_details(stage)

    context = {
        "request": request,
        "current_user": current_user,
        "stage_details": stage_details,
        "now": datetime.utcnow(),
    }
    return templates.TemplateResponse(request, "partials/funnel_projects.html", context=context)


@router.get("/dashboard/by-model")
async def redirect_by_model() -> RedirectResponse:
    """Redirect legacy by-model route to the main dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard/by-developer")
async def redirect_by_developer() -> RedirectResponse:
    """Redirect legacy by-developer route to the main dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)


@router.get("/dashboard/by-command")
async def redirect_by_command() -> RedirectResponse:
    """Redirect legacy by-command route to the main dashboard."""
    return RedirectResponse(url="/dashboard", status_code=302)
