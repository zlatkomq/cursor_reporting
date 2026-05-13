"""Reports router — GET endpoints for querying aggregated metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query

from cursor_metrics.database import get_db
from cursor_metrics.dependencies import get_current_user
from cursor_metrics.repositories.metrics_repo import MetricsRepository
from cursor_metrics.services.metrics_service import MetricsService
from cursor_metrics.services.pricing_service import PricingService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1", tags=["reports"])


def _build_metrics_service(session: AsyncSession) -> MetricsService:
    repo = MetricsRepository(session)
    pricing = PricingService(session)
    return MetricsService(repository=repo, pricing_service=pricing)


@router.get("/metrics")
async def get_metrics_overview(
    days: int = Query(default=30),
    _user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    if days not in (7, 30, 90):
        raise HTTPException(status_code=422, detail="days must be 7, 30, or 90")
    svc = _build_metrics_service(session)
    return await svc.get_overview(days=days)


@router.get("/metrics/by-developer")
async def get_metrics_by_developer(
    days: int = Query(default=30),
    _user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    if days not in (7, 30, 90):
        raise HTTPException(status_code=422, detail="days must be 7, 30, or 90")
    svc = _build_metrics_service(session)
    return await svc.get_by_developer(days=days)


@router.get("/metrics/by-model")
async def get_metrics_by_model(
    days: int = Query(default=30),
    _user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict:
    if days not in (7, 30, 90):
        raise HTTPException(status_code=422, detail="days must be 7, 30, or 90")
    svc = _build_metrics_service(session)
    return await svc.get_by_model(days=days)
