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

    async def count_events(self, since: datetime, command_name: str | None = None) -> int:
        """Return total number of events since the given timestamp."""
        stmt = select(func.count()).select_from(MetricsEvent).where(MetricsEvent.timestamp >= since)
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_active_developers(self, since: datetime, command_name: str | None = None) -> int:
        """Return number of distinct developers since the given timestamp."""
        stmt = (
            select(func.count(func.distinct(MetricsEvent.user_email)))
            .select_from(MetricsEvent)
            .where(MetricsEvent.timestamp >= since)
        )
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def top_model(self, since: datetime, command_name: str | None = None) -> str | None:
        """Return the most-used model name, or None when no data exists."""
        stmt = (
            select(MetricsEvent.model)
            .where(MetricsEvent.timestamp >= since)
            .group_by(MetricsEvent.model)
            .order_by(func.count().desc())
            .limit(1)
        )
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def daily_event_counts(self, since: datetime, command_name: str | None = None) -> list[tuple[date, int]]:
        """Return (date, count) pairs ordered by date ascending."""
        day = func.date(MetricsEvent.timestamp).label("day")
        cnt = func.count().label("cnt")
        stmt = select(day, cnt).where(MetricsEvent.timestamp >= since).group_by(day).order_by(day)
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
        result = await self._session.execute(stmt)
        return [(row.day, row.cnt) for row in result.all()]

    async def events_by_developer(self, since: datetime, command_name: str | None = None) -> list[dict]:
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
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
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
            if command_name:
                top_model_stmt = top_model_stmt.where(MetricsEvent.command_name == command_name)
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

    async def total_tokens(self, since: datetime, command_name: str | None = None) -> dict[str, int]:
        """Return aggregated token counts for the period."""
        stmt = select(
            func.coalesce(func.sum(MetricsEvent.input_tokens), 0).label("input"),
            func.coalesce(func.sum(MetricsEvent.output_tokens), 0).label("output"),
            func.coalesce(func.sum(MetricsEvent.cache_read_tokens), 0).label("cache_read"),
            func.coalesce(func.sum(MetricsEvent.cache_write_tokens), 0).label("cache_write"),
        ).where(MetricsEvent.timestamp >= since)
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
        row = (await self._session.execute(stmt)).one()
        return {
            "input_tokens": row.input,
            "output_tokens": row.output,
            "cache_read_tokens": row.cache_read,
            "cache_write_tokens": row.cache_write,
        }

    async def events_by_model(self, since: datetime, command_name: str | None = None) -> list[dict]:
        """Return per-model aggregates ordered by event count descending."""
        event_count = func.count().label("event_count")
        stmt = (
            select(
                MetricsEvent.model.label("model"),
                event_count,
                func.count(func.distinct(MetricsEvent.user_email)).label("developer_count"),
                func.avg(MetricsEvent.duration_ms).label("avg_duration_ms"),
                func.coalesce(func.sum(MetricsEvent.input_tokens), 0).label("total_input_tokens"),
                func.coalesce(func.sum(MetricsEvent.output_tokens), 0).label("total_output_tokens"),
                func.coalesce(func.sum(MetricsEvent.cache_read_tokens), 0).label("total_cache_read_tokens"),
                func.coalesce(func.sum(MetricsEvent.cache_write_tokens), 0).label("total_cache_write_tokens"),
            )
            .where(MetricsEvent.timestamp >= since)
            .group_by(MetricsEvent.model)
            .order_by(event_count.desc())
        )
        if command_name:
            stmt = stmt.where(MetricsEvent.command_name == command_name)
        result = await self._session.execute(stmt)
        return [
            {
                "model": row.model,
                "event_count": row.event_count,
                "developer_count": row.developer_count,
                "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms is not None else None,
                "total_input_tokens": row.total_input_tokens,
                "total_output_tokens": row.total_output_tokens,
                "total_cache_read_tokens": row.total_cache_read_tokens,
                "total_cache_write_tokens": row.total_cache_write_tokens,
            }
            for row in result.all()
        ]

    async def distinct_commands(self, since: datetime) -> list[str]:
        """Return distinct non-null command_name values for the period, sorted."""
        stmt = (
            select(MetricsEvent.command_name)
            .where(MetricsEvent.timestamp >= since, MetricsEvent.command_name.isnot(None))
            .distinct()
            .order_by(MetricsEvent.command_name)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def recent_events(self, limit: int = 10) -> list[MetricsEvent]:
        """Return the most recent MetricsEvent rows ordered by timestamp descending."""
        stmt = select(MetricsEvent).order_by(MetricsEvent.timestamp.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def daily_token_counts(self, days: int = 30) -> list[tuple[str, int]]:
        """Return (date_string, total_tokens) tuples for the last N days."""
        from datetime import datetime, timedelta

        since = datetime.utcnow() - timedelta(days=days)
        day = func.date(MetricsEvent.timestamp).label("day")
        total = func.coalesce(func.sum(MetricsEvent.input_tokens), 0) + func.coalesce(
            func.sum(MetricsEvent.output_tokens), 0
        )
        total = total.label("total")
        stmt = select(day, total).where(MetricsEvent.timestamp >= since).group_by(day).order_by(day)
        result = await self._session.execute(stmt)
        return [(str(row.day), int(row.total)) for row in result.all()]

    async def events_by_command(self, since: datetime) -> list[dict]:
        """Return per-command aggregates ordered by event count descending."""
        event_count = func.count().label("event_count")
        stmt = (
            select(
                MetricsEvent.command_name.label("command_name"),
                event_count,
                func.coalesce(func.sum(MetricsEvent.input_tokens), 0).label("total_input_tokens"),
                func.coalesce(func.sum(MetricsEvent.output_tokens), 0).label("total_output_tokens"),
                func.coalesce(func.sum(MetricsEvent.cache_read_tokens), 0).label("total_cache_read_tokens"),
            )
            .where(
                MetricsEvent.timestamp >= since,
                MetricsEvent.command_name.isnot(None),
            )
            .group_by(MetricsEvent.command_name)
            .order_by(event_count.desc())
        )
        result = await self._session.execute(stmt)
        return [
            {
                "command_name": row.command_name,
                "event_count": row.event_count,
                "total_input_tokens": row.total_input_tokens,
                "total_output_tokens": row.total_output_tokens,
                "total_cache_read_tokens": row.total_cache_read_tokens,
            }
            for row in result.all()
        ]
