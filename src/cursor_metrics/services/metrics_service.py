"""Business logic for aggregating and querying telemetry metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cursor_metrics.repositories.metrics_repo import MetricsRepository
    from cursor_metrics.services.pricing_service import PricingService


class MetricsService:
    """Aggregation and business logic layer for telemetry metrics.

    Sits between the API routers and the :class:`MetricsRepository`,
    transforming raw query results into domain-level responses.
    """

    def __init__(self, repository: MetricsRepository, pricing_service: PricingService) -> None:
        self._repository = repository
        self._pricing = pricing_service

    async def get_overview(self, days: int = 30) -> dict:
        """Return stat card values + daily counts for the period."""
        since = datetime.utcnow() - timedelta(days=days)

        total_events = await self._repository.count_events(since)
        active_developers = await self._repository.count_active_developers(since)
        top_model = await self._repository.top_model(since)
        daily_counts = await self._repository.daily_event_counts(since)
        models = await self._repository.events_by_model(since)

        total_cost = Decimal(0)
        for m in models:
            total_cost += await self._pricing.estimate_cost(m["model"], m["event_count"])

        return {
            "period_days": days,
            "total_events": total_events,
            "active_developers": active_developers,
            "top_model": top_model,
            "estimated_cost_usd": float(total_cost),
            "daily_counts": [{"date": str(d), "count": c} for d, c in daily_counts],
        }

    async def get_by_developer(self, days: int = 30) -> dict:
        """Return developer rankings sorted by event count."""
        since = datetime.utcnow() - timedelta(days=days)
        developers = await self._repository.events_by_developer(since)
        return {"period_days": days, "developers": developers}

    async def get_by_model(self, days: int = 30) -> dict:
        """Return model usage with cost estimates."""
        since = datetime.utcnow() - timedelta(days=days)
        models = await self._repository.events_by_model(since)

        enriched = []
        for m in models:
            cost = await self._pricing.estimate_cost(m["model"], m["event_count"])
            enriched.append(
                {
                    "model": m["model"],
                    "event_count": m["event_count"],
                    "developer_count": m["developer_count"],
                    "estimated_cost_usd": float(cost),
                    "avg_duration_ms": m["avg_duration_ms"],
                }
            )

        return {"period_days": days, "models": enriched}
