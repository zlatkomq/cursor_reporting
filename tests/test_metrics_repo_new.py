"""Tests for MetricsRepository.recent_events() and daily_token_counts()."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from cursor_metrics.database import Base
from cursor_metrics.models.db import MetricsEvent
from cursor_metrics.repositories.metrics_repo import MetricsRepository


@pytest.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s
    await engine.dispose()


_next_id = 0


def _make_event(ts: datetime, total_tokens: int = 100, **kwargs) -> MetricsEvent:
    global _next_id
    _next_id += 1
    defaults = {
        "id": _next_id,
        "event_type": "completion",
        "conversation_id": "conv-1",
        "generation_id": "gen-1",
        "model": "gpt-4",
        "user_email": "dev@example.com",
        "status": "success",
        "timestamp": ts,
        "created_at": ts,
        "input_tokens": total_tokens // 2,
        "output_tokens": total_tokens // 2,
    }
    defaults.update(kwargs)
    return MetricsEvent(**defaults)


class TestRecentEvents:
    """recent_events returns the most recent MetricsEvent rows descending."""

    @pytest.mark.asyncio()
    async def test_returns_limited_rows_ordered_desc(self, session: AsyncSession) -> None:
        now = datetime(2025, 6, 1, 12, 0, 0)
        events = [_make_event(now - timedelta(hours=i), generation_id=f"gen-{i}") for i in range(5)]
        session.add_all(events)
        await session.commit()

        repo = MetricsRepository(session=session)
        result = await repo.recent_events(limit=3)

        assert len(result) == 3
        assert result[0].timestamp >= result[1].timestamp >= result[2].timestamp
        assert result[0].timestamp == now

    @pytest.mark.asyncio()
    async def test_default_limit_is_10(self, session: AsyncSession) -> None:
        now = datetime(2025, 6, 1, 12, 0, 0)
        events = [_make_event(now - timedelta(minutes=i), generation_id=f"gen-{i}") for i in range(15)]
        session.add_all(events)
        await session.commit()

        repo = MetricsRepository(session=session)
        result = await repo.recent_events()

        assert len(result) == 10

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_data(self, session: AsyncSession) -> None:
        repo = MetricsRepository(session=session)
        result = await repo.recent_events()

        assert result == []

    @pytest.mark.asyncio()
    async def test_returns_metrics_event_instances(self, session: AsyncSession) -> None:
        session.add(_make_event(datetime(2025, 6, 1, 10, 0, 0)))
        await session.commit()

        repo = MetricsRepository(session=session)
        result = await repo.recent_events()

        assert isinstance(result[0], MetricsEvent)


class TestDailyTokenCounts:
    """daily_token_counts returns (date_string, total_tokens) grouped by day."""

    @pytest.mark.asyncio()
    async def test_returns_grouped_daily_totals(self, session: AsyncSession) -> None:
        now = datetime.utcnow().replace(hour=10, minute=0, second=0, microsecond=0)
        yesterday = now - timedelta(days=1)
        session.add_all(
            [
                _make_event(now, total_tokens=100, generation_id="g1"),
                _make_event(now + timedelta(hours=2), total_tokens=200, generation_id="g2"),
                _make_event(yesterday, total_tokens=50, generation_id="g3"),
            ]
        )
        await session.commit()

        repo = MetricsRepository(session=session)
        result = await repo.daily_token_counts(days=30)

        assert len(result) == 2
        date_str_0, total_0 = result[0]
        date_str_1, total_1 = result[1]
        assert date_str_0 == yesterday.strftime("%Y-%m-%d")
        assert total_0 == 50
        assert date_str_1 == now.strftime("%Y-%m-%d")
        assert total_1 == 300

    @pytest.mark.asyncio()
    async def test_excludes_events_older_than_days(self, session: AsyncSession) -> None:
        now = datetime.utcnow()
        session.add_all(
            [
                _make_event(now - timedelta(days=5), total_tokens=100, generation_id="g1"),
                _make_event(now - timedelta(days=40), total_tokens=999, generation_id="g2"),
            ]
        )
        await session.commit()

        repo = MetricsRepository(session=session)
        result = await repo.daily_token_counts(days=30)

        assert len(result) == 1
        assert result[0][1] == 100

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_data(self, session: AsyncSession) -> None:
        repo = MetricsRepository(session=session)
        result = await repo.daily_token_counts()

        assert result == []

    @pytest.mark.asyncio()
    async def test_ordered_by_date_ascending(self, session: AsyncSession) -> None:
        now = datetime.utcnow()
        session.add_all(
            [
                _make_event(now - timedelta(days=3), total_tokens=10, generation_id="g1"),
                _make_event(now - timedelta(days=1), total_tokens=20, generation_id="g2"),
                _make_event(now - timedelta(days=5), total_tokens=30, generation_id="g3"),
            ]
        )
        await session.commit()

        repo = MetricsRepository(session=session)
        result = await repo.daily_token_counts(days=30)

        dates = [r[0] for r in result]
        assert dates == sorted(dates)
