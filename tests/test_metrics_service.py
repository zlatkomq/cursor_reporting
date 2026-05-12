"""Tests for cursor_metrics.services.metrics_service — MetricsService."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import pytest

from cursor_metrics.services.metrics_service import MetricsService

if TYPE_CHECKING:
    pass


def _build_service(
    *,
    total_events: int = 500,
    active_devs: int = 5,
    top_model: str | None = "claude-4-opus",
    daily_counts: list[tuple[date, int]] | None = None,
    by_developer: list[dict] | None = None,
    by_model: list[dict] | None = None,
    estimate_cost: Decimal = Decimal("1.50"),
) -> tuple[MetricsService, AsyncMock, AsyncMock]:
    """Build a MetricsService with fully mocked repo and pricing."""
    repo = AsyncMock()
    repo.count_events.return_value = total_events
    repo.count_active_developers.return_value = active_devs
    repo.top_model.return_value = top_model
    repo.daily_event_counts.return_value = [
        (date(2026, 5, 1), 120),
        (date(2026, 5, 2), 130),
    ] if daily_counts is None else daily_counts
    repo.events_by_developer.return_value = [
        {
            "email": "alice@example.com",
            "event_count": 300,
            "top_model": "claude-4-opus",
            "avg_duration_ms": 450.0,
            "last_active": "2026-05-10T12:00:00",
        },
        {
            "email": "bob@example.com",
            "event_count": 200,
            "top_model": "gpt-4o",
            "avg_duration_ms": 520.0,
            "last_active": "2026-05-09T08:00:00",
        },
    ] if by_developer is None else by_developer
    repo.events_by_model.return_value = [
        {"model": "claude-4-opus", "event_count": 300, "developer_count": 3, "avg_duration_ms": 450.0},
        {"model": "gpt-4o", "event_count": 200, "developer_count": 2, "avg_duration_ms": 520.0},
    ] if by_model is None else by_model

    pricing = AsyncMock()
    pricing.estimate_cost.return_value = estimate_cost

    return MetricsService(repo, pricing), repo, pricing


class TestGetOverview:
    """Tests for MetricsService.get_overview."""

    @pytest.mark.asyncio()
    async def test_returns_correct_structure(self) -> None:
        svc, _repo, _pricing = _build_service()

        result = await svc.get_overview(days=7)

        assert result["period_days"] == 7
        assert result["total_events"] == 500
        assert result["active_developers"] == 5
        assert result["top_model"] == "claude-4-opus"
        assert "estimated_cost_usd" in result
        assert "daily_counts" in result

    @pytest.mark.asyncio()
    async def test_daily_counts_formatted(self) -> None:
        svc, _repo, _pricing = _build_service(
            daily_counts=[(date(2026, 5, 1), 42)],
        )

        result = await svc.get_overview(days=30)

        assert result["daily_counts"] == [{"date": "2026-05-01", "count": 42}]

    @pytest.mark.asyncio()
    async def test_estimated_cost_sums_models(self) -> None:
        svc, _repo, pricing = _build_service(estimate_cost=Decimal("2.00"))

        result = await svc.get_overview(days=30)

        assert pricing.estimate_cost.call_count == 2
        assert result["estimated_cost_usd"] == pytest.approx(4.0)

    @pytest.mark.asyncio()
    async def test_calls_repo_with_correct_since(self) -> None:
        svc, repo, _pricing = _build_service()

        with patch("cursor_metrics.services.metrics_service.datetime") as mock_dt:
            from datetime import datetime, timedelta

            now = datetime(2026, 5, 12, 12, 0, 0)
            mock_dt.utcnow.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            await svc.get_overview(days=7)

            expected_since = now - timedelta(days=7)
            repo.count_events.assert_awaited_once_with(expected_since)


class TestGetByDeveloper:
    """Tests for MetricsService.get_by_developer."""

    @pytest.mark.asyncio()
    async def test_wraps_developer_list(self) -> None:
        devs = [
            {"email": "alice@example.com", "event_count": 300, "top_model": "claude-4-opus", "avg_duration_ms": 450.0, "last_active": "2026-05-10"},
        ]
        svc, _repo, _pricing = _build_service(by_developer=devs)

        result = await svc.get_by_developer(days=14)

        assert result["period_days"] == 14
        assert result["developers"] == devs

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_developers(self) -> None:
        svc, _repo, _pricing = _build_service(by_developer=[])

        result = await svc.get_by_developer(days=30)

        assert result["developers"] == []


class TestGetByModel:
    """Tests for MetricsService.get_by_model."""

    @pytest.mark.asyncio()
    async def test_enriches_with_cost(self) -> None:
        models = [
            {"model": "claude-4-opus", "event_count": 300, "developer_count": 3, "avg_duration_ms": 450.0},
        ]
        svc, _repo, pricing = _build_service(by_model=models, estimate_cost=Decimal("3.50"))

        result = await svc.get_by_model(days=30)

        assert len(result["models"]) == 1
        entry = result["models"][0]
        assert entry["model"] == "claude-4-opus"
        assert entry["event_count"] == 300
        assert entry["developer_count"] == 3
        assert entry["estimated_cost_usd"] == pytest.approx(3.5)
        assert entry["avg_duration_ms"] == 450.0
        pricing.estimate_cost.assert_awaited_once_with("claude-4-opus", 300)

    @pytest.mark.asyncio()
    async def test_returns_period_days(self) -> None:
        svc, _repo, _pricing = _build_service()

        result = await svc.get_by_model(days=60)

        assert result["period_days"] == 60


class TestGetOverviewEmpty:
    """Edge-case: zero events / no data."""

    @pytest.mark.asyncio()
    async def test_handles_zero_events(self) -> None:
        svc, _repo, _pricing = _build_service(
            total_events=0,
            active_devs=0,
            top_model=None,
            daily_counts=[],
            by_model=[],
        )

        result = await svc.get_overview(days=30)

        assert result["total_events"] == 0
        assert result["active_developers"] == 0
        assert result["top_model"] is None
        assert result["estimated_cost_usd"] == pytest.approx(0.0)
        assert result["daily_counts"] == []
