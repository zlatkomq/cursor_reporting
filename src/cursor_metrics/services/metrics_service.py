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

    async def get_overview(self, days: int = 30, command: str | None = None) -> dict:
        """Return stat card values + daily counts for the period."""
        since = datetime.utcnow() - timedelta(days=days)

        total_events = await self._repository.count_events(since, command_name=command)
        active_developers = await self._repository.count_active_developers(since, command_name=command)
        top_model = await self._repository.top_model(since, command_name=command)
        daily_counts = await self._repository.daily_event_counts(since, command_name=command)
        models = await self._repository.events_by_model(since, command_name=command)
        token_totals = await self._repository.total_tokens(since, command_name=command)

        total_cost = Decimal(0)
        for m in models:
            total_cost += await self._pricing.estimate_cost(
                m["model"],
                m["event_count"],
                input_tokens=m.get("total_input_tokens"),
                output_tokens=m.get("total_output_tokens"),
                cache_read_tokens=m.get("total_cache_read_tokens"),
            )

        return {
            "period_days": days,
            "total_events": total_events,
            "active_developers": active_developers,
            "top_model": top_model,
            "estimated_cost_usd": float(total_cost),
            "total_input_tokens": token_totals["input_tokens"],
            "total_output_tokens": token_totals["output_tokens"],
            "total_cache_read_tokens": token_totals["cache_read_tokens"],
            "total_cache_write_tokens": token_totals["cache_write_tokens"],
            "daily_counts": [{"date": str(d), "count": c} for d, c in daily_counts],
        }

    async def get_by_developer(self, days: int = 30, command: str | None = None) -> dict:
        """Return developer rankings sorted by event count."""
        since = datetime.utcnow() - timedelta(days=days)
        developers = await self._repository.events_by_developer(since, command_name=command)
        return {"period_days": days, "developers": developers}

    async def get_by_model(self, days: int = 30, command: str | None = None) -> dict:
        """Return model usage with cost estimates."""
        since = datetime.utcnow() - timedelta(days=days)
        models = await self._repository.events_by_model(since, command_name=command)

        enriched = []
        for m in models:
            cost = await self._pricing.estimate_cost(
                m["model"],
                m["event_count"],
                input_tokens=m.get("total_input_tokens"),
                output_tokens=m.get("total_output_tokens"),
                cache_read_tokens=m.get("total_cache_read_tokens"),
            )
            enriched.append(
                {
                    "model": m["model"],
                    "event_count": m["event_count"],
                    "developer_count": m["developer_count"],
                    "estimated_cost_usd": float(cost),
                    "avg_duration_ms": m["avg_duration_ms"],
                    "total_input_tokens": m.get("total_input_tokens", 0),
                    "total_output_tokens": m.get("total_output_tokens", 0),
                    "total_cache_read_tokens": m.get("total_cache_read_tokens", 0),
                }
            )

        return {"period_days": days, "models": enriched}

    async def get_available_commands(self, days: int = 30) -> list[str]:
        """Return distinct command names seen in the period."""
        since = datetime.utcnow() - timedelta(days=days)
        return await self._repository.distinct_commands(since)

    async def get_by_command(self, days: int = 30) -> dict:
        """Return per-command aggregates with cost estimates."""
        since = datetime.utcnow() - timedelta(days=days)
        rows = await self._repository.events_by_command(since)

        enriched = []
        for row in rows:
            total_tokens = row["total_input_tokens"] + row["total_output_tokens"]
            enriched.append(
                {
                    "command_name": row["command_name"],
                    "event_count": row["event_count"],
                    "total_input_tokens": row["total_input_tokens"],
                    "total_output_tokens": row["total_output_tokens"],
                    "total_cache_read_tokens": row["total_cache_read_tokens"],
                    "total_tokens": total_tokens,
                }
            )

        return {"period_days": days, "commands": enriched}
