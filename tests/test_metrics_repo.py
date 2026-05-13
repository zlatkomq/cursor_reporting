"""Tests for cursor_metrics.repositories.metrics_repo — MetricsRepository query methods."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from cursor_metrics.repositories.metrics_repo import MetricsRepository

SINCE = datetime(2025, 1, 1)


@pytest.fixture()
def session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


class TestCountEvents:
    """count_events returns the total event count as an int."""

    @pytest.mark.asyncio()
    async def test_returns_count(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 42
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        count = await repo.count_events(SINCE)

        assert count == 42
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_zero_when_no_events(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 0
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        count = await repo.count_events(SINCE)

        assert count == 0


class TestCountActiveDevelopers:
    """count_active_developers returns distinct developer count."""

    @pytest.mark.asyncio()
    async def test_returns_distinct_count(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 5
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        count = await repo.count_active_developers(SINCE)

        assert count == 5
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_zero_when_no_developers(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one.return_value = 0
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        count = await repo.count_active_developers(SINCE)

        assert count == 0


class TestTopModel:
    """top_model returns the most-used model name or None."""

    @pytest.mark.asyncio()
    async def test_returns_model_name(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = "gpt-4"
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        model = await repo.top_model(SINCE)

        assert model == "gpt-4"
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_none_when_no_data(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        model = await repo.top_model(SINCE)

        assert model is None


class TestDailyEventCounts:
    """daily_event_counts returns a list of (date, int) tuples."""

    @pytest.mark.asyncio()
    async def test_returns_list_of_tuples(self, session: AsyncMock) -> None:
        row1 = MagicMock()
        row1.day = date(2025, 1, 1)
        row1.cnt = 10
        row2 = MagicMock()
        row2.day = date(2025, 1, 2)
        row2.cnt = 20

        result_mock = MagicMock()
        result_mock.all.return_value = [row1, row2]
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        counts = await repo.daily_event_counts(SINCE)

        assert counts == [(date(2025, 1, 1), 10), (date(2025, 1, 2), 20)]
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_data(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        counts = await repo.daily_event_counts(SINCE)

        assert counts == []


class TestEventsByDeveloper:
    """events_by_developer returns list of dicts with developer aggregates."""

    @pytest.mark.asyncio()
    async def test_returns_list_of_dicts(self, session: AsyncMock) -> None:
        agg_row = MagicMock()
        agg_row.email = "dev@example.com"
        agg_row.event_count = 15
        agg_row.avg_duration_ms = 120.5
        agg_row.last_active = datetime(2025, 6, 1, 12, 0, 0)

        agg_result = MagicMock()
        agg_result.all.return_value = [agg_row]

        top_model_result = MagicMock()
        top_model_result.scalar_one_or_none.return_value = "claude-3.5-sonnet"

        session.execute = AsyncMock(side_effect=[agg_result, top_model_result])

        repo = MetricsRepository(session=session)
        devs = await repo.events_by_developer(SINCE)

        assert len(devs) == 1
        assert devs[0]["email"] == "dev@example.com"
        assert devs[0]["event_count"] == 15
        assert devs[0]["top_model"] == "claude-3.5-sonnet"
        assert devs[0]["avg_duration_ms"] == 120.5
        assert devs[0]["last_active"] == datetime(2025, 6, 1, 12, 0, 0)

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_data(self, session: AsyncMock) -> None:
        agg_result = MagicMock()
        agg_result.all.return_value = []
        session.execute = AsyncMock(return_value=agg_result)

        repo = MetricsRepository(session=session)
        devs = await repo.events_by_developer(SINCE)

        assert devs == []

    @pytest.mark.asyncio()
    async def test_handles_null_duration(self, session: AsyncMock) -> None:
        agg_row = MagicMock()
        agg_row.email = "dev@example.com"
        agg_row.event_count = 3
        agg_row.avg_duration_ms = None
        agg_row.last_active = datetime(2025, 3, 1)

        agg_result = MagicMock()
        agg_result.all.return_value = [agg_row]

        top_model_result = MagicMock()
        top_model_result.scalar_one_or_none.return_value = "gpt-4"

        session.execute = AsyncMock(side_effect=[agg_result, top_model_result])

        repo = MetricsRepository(session=session)
        devs = await repo.events_by_developer(SINCE)

        assert devs[0]["avg_duration_ms"] is None


class TestTotalTokens:
    """total_tokens returns aggregated token counts as a dict."""

    @pytest.mark.asyncio()
    async def test_total_tokens_returns_aggregates(self, session: AsyncMock) -> None:
        row = MagicMock()
        row.input = 1000
        row.output = 2000
        row.cache_read = 500
        row.cache_write = 300

        result_mock = MagicMock()
        result_mock.one.return_value = row
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        totals = await repo.total_tokens(SINCE)

        assert totals == {
            "input_tokens": 1000,
            "output_tokens": 2000,
            "cache_read_tokens": 500,
            "cache_write_tokens": 300,
        }
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_total_tokens_returns_zeros_when_empty(self, session: AsyncMock) -> None:
        row = MagicMock()
        row.input = 0
        row.output = 0
        row.cache_read = 0
        row.cache_write = 0

        result_mock = MagicMock()
        result_mock.one.return_value = row
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        totals = await repo.total_tokens(SINCE)

        assert totals == {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "cache_write_tokens": 0,
        }


class TestEventsByModel:
    """events_by_model returns list of dicts with model aggregates."""

    @pytest.mark.asyncio()
    async def test_returns_list_of_dicts(self, session: AsyncMock) -> None:
        row = MagicMock()
        row.model = "gpt-4"
        row.event_count = 100
        row.developer_count = 5
        row.avg_duration_ms = 250.0
        row.total_input_tokens = 5000
        row.total_output_tokens = 8000
        row.total_cache_read_tokens = 1200

        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        models = await repo.events_by_model(SINCE)

        assert len(models) == 1
        assert models[0]["model"] == "gpt-4"
        assert models[0]["event_count"] == 100
        assert models[0]["developer_count"] == 5
        assert models[0]["avg_duration_ms"] == 250.0
        assert models[0]["total_input_tokens"] == 5000
        assert models[0]["total_output_tokens"] == 8000
        assert models[0]["total_cache_read_tokens"] == 1200
        session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_data(self, session: AsyncMock) -> None:
        result_mock = MagicMock()
        result_mock.all.return_value = []
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        models = await repo.events_by_model(SINCE)

        assert models == []

    @pytest.mark.asyncio()
    async def test_handles_null_avg_duration(self, session: AsyncMock) -> None:
        row = MagicMock()
        row.model = "claude-3"
        row.event_count = 10
        row.developer_count = 2
        row.avg_duration_ms = None
        row.total_input_tokens = 0
        row.total_output_tokens = 0
        row.total_cache_read_tokens = 0

        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        models = await repo.events_by_model(SINCE)

        assert models[0]["avg_duration_ms"] is None

    @pytest.mark.asyncio()
    async def test_events_by_model_includes_token_sums(self, session: AsyncMock) -> None:
        row = MagicMock()
        row.model = "claude-3.5-sonnet"
        row.event_count = 50
        row.developer_count = 3
        row.avg_duration_ms = 180.0
        row.total_input_tokens = 12000
        row.total_output_tokens = 9500
        row.total_cache_read_tokens = 4000

        result_mock = MagicMock()
        result_mock.all.return_value = [row]
        session.execute = AsyncMock(return_value=result_mock)

        repo = MetricsRepository(session=session)
        models = await repo.events_by_model(SINCE)

        assert "total_input_tokens" in models[0]
        assert "total_output_tokens" in models[0]
        assert "total_cache_read_tokens" in models[0]
        assert models[0]["total_input_tokens"] == 12000
        assert models[0]["total_output_tokens"] == 9500
        assert models[0]["total_cache_read_tokens"] == 4000
