"""Repository for dashboard_users database operations via SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from cursor_metrics.models.db import DashboardUser

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserRepository:
    """Encapsulates all MariaDB queries against the dashboard_users table.

    Follows the repository pattern so that routers and services never
    construct SQL directly.  All database I/O is async.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> DashboardUser | None:
        """Return the user matching *email*, or ``None`` if not found."""
        result = await self._session.execute(
            select(DashboardUser).where(DashboardUser.email == email),
        )
        return result.scalars().first()

    async def create(self, email: str, password_hash: str) -> DashboardUser:
        """Insert a new dashboard user and return the persisted instance."""
        user = DashboardUser(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user
