"""Tests for cursor_metrics.services.workflow_service — WorkflowService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from cursor_metrics.services.workflow_service import WorkflowService

CANONICAL_STAGES = ["spec", "design", "uix", "tasks", "implement", "review"]


def _build_service(
    *,
    count_by_stage: list[tuple[str, int]] | None = None,
    projects_by_stage: list | None = None,
    count_active_in_stage: int = 2,
    avg_time_in_stage: float | None = 3.5,
    total_projects: int = 10,
    count_blocked: int = 1,
) -> tuple[WorkflowService, AsyncMock]:
    """Build a WorkflowService with a fully mocked repository."""
    repo = AsyncMock()
    repo.count_by_stage.return_value = (
        count_by_stage
        if count_by_stage is not None
        else [("spec", 10), ("design", 8), ("uix", 6), ("tasks", 5), ("implement", 3), ("review", 1)]
    )
    repo.projects_by_stage.return_value = projects_by_stage if projects_by_stage is not None else []
    repo.count_active_in_stage.return_value = count_active_in_stage
    repo.avg_time_in_stage.return_value = avg_time_in_stage
    repo.total_projects.return_value = total_projects
    repo.count_blocked.return_value = count_blocked

    return WorkflowService(repo), repo


class TestGetFunnelData:
    """Tests for WorkflowService.get_funnel_data."""

    @pytest.mark.asyncio()
    async def test_returns_all_six_stages(self) -> None:
        svc, _repo = _build_service()
        result = await svc.get_funnel_data()

        assert len(result) == 6
        assert [r["stage"] for r in result] == CANONICAL_STAGES

    @pytest.mark.asyncio()
    async def test_counts_match_repo(self) -> None:
        svc, _repo = _build_service(
            count_by_stage=[("spec", 20), ("design", 15)],
        )
        result = await svc.get_funnel_data()

        by_stage = {r["stage"]: r["count"] for r in result}
        assert by_stage["spec"] == 20
        assert by_stage["design"] == 15
        assert by_stage["uix"] == 0
        assert by_stage["tasks"] == 0
        assert by_stage["implement"] == 0
        assert by_stage["review"] == 0

    @pytest.mark.asyncio()
    async def test_percentages_relative_to_first_stage(self) -> None:
        svc, _repo = _build_service(
            count_by_stage=[("spec", 10), ("design", 5), ("review", 2)],
        )
        result = await svc.get_funnel_data()

        assert result[0]["percentage"] == 100.0  # spec: 10/10
        assert result[1]["percentage"] == 50.0  # design: 5/10
        assert result[5]["percentage"] == 20.0  # review: 2/10

    @pytest.mark.asyncio()
    async def test_percentage_zero_when_first_stage_is_zero(self) -> None:
        svc, _repo = _build_service(count_by_stage=[])
        result = await svc.get_funnel_data()

        for r in result:
            assert r["percentage"] == 0.0

    @pytest.mark.asyncio()
    async def test_missing_stages_default_to_zero(self) -> None:
        svc, _repo = _build_service(count_by_stage=[("implement", 3)])
        result = await svc.get_funnel_data()

        by_stage = {r["stage"]: r for r in result}
        assert by_stage["spec"]["count"] == 0
        assert by_stage["implement"]["count"] == 3


class TestGetStageDetails:
    """Tests for WorkflowService.get_stage_details."""

    @pytest.mark.asyncio()
    async def test_returns_correct_structure(self) -> None:
        projects = [{"name": "alpha"}, {"name": "beta"}]
        svc, repo = _build_service(
            projects_by_stage=projects,
            count_active_in_stage=4,
            avg_time_in_stage=7.2,
        )

        result = await svc.get_stage_details("design")

        assert result["stage"] == "design"
        assert result["projects"] == projects
        assert result["active_count"] == 4
        assert result["avg_days"] == 7.2
        repo.projects_by_stage.assert_awaited_once_with("design")
        repo.count_active_in_stage.assert_awaited_once_with("design")
        repo.avg_time_in_stage.assert_awaited_once_with("design")

    @pytest.mark.asyncio()
    async def test_avg_days_none(self) -> None:
        svc, _repo = _build_service(avg_time_in_stage=None)

        result = await svc.get_stage_details("spec")

        assert result["avg_days"] is None


class TestGetSummary:
    """Tests for WorkflowService.get_summary."""

    @pytest.mark.asyncio()
    async def test_returns_correct_structure(self) -> None:
        svc, _repo = _build_service(total_projects=15, count_blocked=3)
        result = await svc.get_summary()

        assert result["total_projects"] == 15
        assert result["blocked_count"] == 3
        assert isinstance(result["funnel"], list)
        assert len(result["funnel"]) == 6

    @pytest.mark.asyncio()
    async def test_funnel_is_same_as_get_funnel_data(self) -> None:
        svc, _repo = _build_service()
        summary = await svc.get_summary()
        funnel = await svc.get_funnel_data()

        assert [r["stage"] for r in summary["funnel"]] == [r["stage"] for r in funnel]
