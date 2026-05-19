"""Tests for MetricsService.get_overview_with_trends."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from cursor_metrics.services.metrics_service import MetricsService


def _make_service(
    *,
    count_events: int = 100,
    total_tokens: dict | None = None,
    models: list[dict] | None = None,
    estimate_cost: Decimal = Decimal("1.25"),
    daily_token_counts: list[tuple[str, int]] | None = None,
    recent_events: list | None = None,
) -> tuple[MetricsService, AsyncMock, AsyncMock]:
    repo = AsyncMock()
    repo.count_events.return_value = count_events
    repo.total_tokens.return_value = total_tokens or {
        "input_tokens": 5000,
        "output_tokens": 3000,
        "cache_read_tokens": 1000,
        "cache_write_tokens": 500,
    }
    repo.events_by_model.return_value = models if models is not None else [
        {
            "model": "claude-4-opus",
            "event_count": 60,
            "developer_count": 2,
            "avg_duration_ms": 400.0,
            "total_input_tokens": 3000,
            "total_output_tokens": 2000,
            "total_cache_read_tokens": 500,
            "total_cache_write_tokens": 0,
        },
        {
            "model": "gpt-4o",
            "event_count": 40,
            "developer_count": 1,
            "avg_duration_ms": 300.0,
            "total_input_tokens": 2000,
            "total_output_tokens": 1000,
            "total_cache_read_tokens": 500,
            "total_cache_write_tokens": 0,
        },
    ]
    repo.daily_token_counts.return_value = daily_token_counts if daily_token_counts is not None else [
        ("2026-05-01", 1200),
        ("2026-05-02", 1500),
    ]
    repo.recent_events.return_value = recent_events if recent_events is not None else [
        MagicMock(id=1),
        MagicMock(id=2),
    ]

    pricing = AsyncMock()
    pricing.estimate_cost.return_value = estimate_cost

    return MetricsService(repo, pricing), repo, pricing


class TestGetOverviewWithTrends:
    """Tests for MetricsService.get_overview_with_trends."""

    @pytest.mark.asyncio()
    async def test_returns_all_expected_keys(self) -> None:
        svc, _repo, _pricing = _make_service()

        result = await svc.get_overview_with_trends(days=30)

        expected_keys = {
            "total_requests",
            "total_tokens",
            "total_cost",
            "active_models",
            "daily_tokens",
            "recent_events",
        }
        assert set(result.keys()) == expected_keys

    @pytest.mark.asyncio()
    async def test_total_requests_from_count_events(self) -> None:
        svc, repo, _pricing = _make_service(count_events=42)

        result = await svc.get_overview_with_trends(days=14)

        assert result["total_requests"] == 42
        repo.count_events.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_total_tokens_sums_input_and_output(self) -> None:
        svc, _repo, _pricing = _make_service(
            total_tokens={
                "input_tokens": 4000,
                "output_tokens": 2000,
                "cache_read_tokens": 100,
                "cache_write_tokens": 50,
            },
        )

        result = await svc.get_overview_with_trends(days=30)

        assert result["total_tokens"] == 6000

    @pytest.mark.asyncio()
    async def test_total_cost_sums_across_models(self) -> None:
        svc, _repo, pricing = _make_service(estimate_cost=Decimal("1.50"))

        result = await svc.get_overview_with_trends(days=30)

        assert pricing.estimate_cost.call_count == 4
        assert result["total_cost"] == pytest.approx(3.0)

    @pytest.mark.asyncio()
    async def test_active_models_counts_distinct(self) -> None:
        svc, _repo, _pricing = _make_service()

        result = await svc.get_overview_with_trends(days=30)

        assert result["active_models"] == 2

    @pytest.mark.asyncio()
    async def test_daily_tokens_from_repo(self) -> None:
        tokens = [("2026-05-10", 800), ("2026-05-11", 900)]
        svc, repo, _pricing = _make_service(daily_token_counts=tokens)

        result = await svc.get_overview_with_trends(days=7)

        assert result["daily_tokens"] == tokens
        repo.daily_token_counts.assert_awaited_once_with(7)

    @pytest.mark.asyncio()
    async def test_recent_events_from_repo(self) -> None:
        event = MagicMock(
            timestamp="2026-05-15T12:00:00",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=50,
            cache_read_tokens=10,
            cache_write_tokens=0,
            duration_ms=1234,
        )
        events = [event]
        svc, repo, _pricing = _make_service(recent_events=events)

        result = await svc.get_overview_with_trends(days=30)

        assert result["recent_events"] == [
            {
                "timestamp": "2026-05-15T12:00:00",
                "model": "gpt-4o",
                "total_tokens": 150,
                "cost": 1.25,
                "duration_ms": 1234,
            }
        ]
        repo.recent_events.assert_awaited_once_with(limit=10)

    @pytest.mark.asyncio()
    async def test_default_days_is_30(self) -> None:
        svc, repo, _pricing = _make_service()

        await svc.get_overview_with_trends()

        repo.daily_token_counts.assert_awaited_once_with(30)

    @pytest.mark.asyncio()
    async def test_empty_data(self) -> None:
        svc, _repo, _pricing = _make_service(
            count_events=0,
            total_tokens={
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_tokens": 0,
                "cache_write_tokens": 0,
            },
            models=[],
            daily_token_counts=[],
            recent_events=[],
        )

        result = await svc.get_overview_with_trends(days=30)

        assert result["total_requests"] == 0
        assert result["total_tokens"] == 0
        assert result["total_cost"] == pytest.approx(0.0)
        assert result["active_models"] == 0
        assert result["daily_tokens"] == []
        assert result["recent_events"] == []
