"""Business logic for the Workflow Funnel tab."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cursor_metrics.repositories.workflow_repo import WorkflowRepository

CANONICAL_STAGES = ("spec", "design", "uix", "tasks", "implement", "review")


class WorkflowService:
    """Wraps :class:`WorkflowRepository` with funnel-oriented business logic."""

    def __init__(self, repository: WorkflowRepository) -> None:
        self._repo = repository

    async def get_funnel_data(self) -> list[dict]:
        """Build a six-stage funnel with counts and percentages."""
        rows = await self._repo.count_by_stage()
        counts: dict[str, int] = dict(rows)

        first_count = counts.get(CANONICAL_STAGES[0], 0)
        return [
            {
                "stage": stage,
                "count": counts.get(stage, 0),
                "percentage": (round(counts.get(stage, 0) / first_count * 100, 1) if first_count > 0 else 0.0),
            }
            for stage in CANONICAL_STAGES
        ]

    async def get_stage_details(self, stage: str) -> dict:
        """Return detailed information for a single stage."""
        return {
            "stage": stage,
            "projects": await self._repo.projects_by_stage(stage),
            "active_count": await self._repo.count_active_in_stage(stage),
            "avg_days": await self._repo.avg_time_in_stage(stage),
        }

    async def get_summary(self) -> dict:
        """Return a high-level project summary including the funnel."""
        return {
            "total_projects": await self._repo.total_projects(),
            "blocked_count": await self._repo.count_blocked(),
            "funnel": await self.get_funnel_data(),
        }
