"""Business logic for aggregating and querying telemetry metrics."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cursor_metrics.repositories.metrics_repo import MetricsRepository


class MetricsService:
    """Aggregation and business logic layer for telemetry metrics.

    Sits between the API routers and the :class:`MetricsRepository`,
    transforming raw query results into domain-level responses.
    """

    def __init__(self, repository: MetricsRepository) -> None:
        self._repository = repository
