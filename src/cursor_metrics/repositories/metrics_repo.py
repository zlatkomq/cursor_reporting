"""Repository for metrics_events database operations via SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class MetricsRepository:
    """Encapsulates all MariaDB queries against the metrics_events table.

    Follows the repository pattern so that routers and services never
    construct SQL directly.  All database I/O is async.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
