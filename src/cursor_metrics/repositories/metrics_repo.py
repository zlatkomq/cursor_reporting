"""Repository for metrics_events database operations via SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import case, func, select

from cursor_metrics.models.db import MetricsEvent

if TYPE_CHECKING:
    from datetime import date, datetime

    from sqlalchemy.ext.asyncio import AsyncSession


class MetricsRepository:
    """Encapsulates all MariaDB queries against the metrics_events table.

    Follows the repository pattern so that routers and services never
    construct SQL directly.  All database I/O is async.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_events(self, since: datetime) -> int:
        """Return total number of events since the given timestamp."""
        stmt = (
            select(func.count())
            .select_from(MetricsEvent)
            .where(
                MetricsEvent.timestamp >= since,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_active_developers(self, since: datetime) -> int:
        """Return number of distinct developers since the given timestamp."""
        stmt = (
            select(func.count(func.distinct(MetricsEvent.user_email)))
            .select_from(MetricsEvent)
            .where(MetricsEvent.timestamp >= since)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def top_model(self, since: datetime) -> str | None:
        """Return the most-used model name, or None when no data exists."""
        stmt = (
            select(MetricsEvent.model)
            .where(MetricsEvent.timestamp >= since)
            .group_by(MetricsEvent.model)
            .order_by(func.count().desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def daily_event_counts(self, since: datetime) -> list[tuple[date, int]]:
        """Return (date, count) pairs ordered by date ascending."""
        day = func.date(MetricsEvent.timestamp).label("day")
        cnt = func.count().label("cnt")
        stmt = select(day, cnt).where(MetricsEvent.timestamp >= since).group_by(day).order_by(day)
        result = await self._session.execute(stmt)
        return [(row.day, row.cnt) for row in result.all()]

    async def events_by_developer(self, since: datetime) -> list[dict]:
        """Return per-developer aggregates ordered by event count descending."""
        event_count = func.count().label("event_count")
        stmt = (
            select(
                MetricsEvent.user_email.label("email"),
                event_count,
                func.avg(
                    case(
                        (MetricsEvent.duration_ms.isnot(None), MetricsEvent.duration_ms),
                    )
                ).label("avg_duration_ms"),
                func.max(MetricsEvent.timestamp).label("last_active"),
            )
            .where(MetricsEvent.timestamp >= since)
            .group_by(MetricsEvent.user_email)
            .order_by(event_count.desc())
        )
        result = await self._session.execute(stmt)
        rows = result.all()

        dev_list: list[dict] = []
        for row in rows:
            top_model_stmt = (
                select(MetricsEvent.model)
                .where(
                    MetricsEvent.user_email == row.email,
                    MetricsEvent.timestamp >= since,
                )
                .group_by(MetricsEvent.model)
                .order_by(func.count().desc())
                .limit(1)
            )
            top_model_result = await self._session.execute(top_model_stmt)
            model_name = top_model_result.scalar_one_or_none()
            dev_list.append(
                {
                    "email": row.email,
                    "event_count": row.event_count,
                    "top_model": model_name,
                    "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms is not None else None,
                    "last_active": row.last_active,
                }
            )
        return dev_list

    async def events_by_model(self, since: datetime) -> list[dict]:
        """Return per-model aggregates ordered by event count descending."""
        event_count = func.count().label("event_count")
        stmt = (
            select(
                MetricsEvent.model.label("model"),
                event_count,
                func.count(func.distinct(MetricsEvent.user_email)).label("developer_count"),
                func.avg(MetricsEvent.duration_ms).label("avg_duration_ms"),
            )
            .where(MetricsEvent.timestamp >= since)
            .group_by(MetricsEvent.model)
            .order_by(event_count.desc())
        )
        result = await self._session.execute(stmt)
        return [
            {
                "model": row.model,
                "event_count": row.event_count,
                "developer_count": row.developer_count,
                "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms is not None else None,
            }
            for row in result.all()
        ]
