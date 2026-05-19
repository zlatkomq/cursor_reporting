"""Repository for workflow_projects database operations via SQLAlchemy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import func, select, text

from cursor_metrics.models.db import WorkflowProject

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class WorkflowRepository:
    """Encapsulates all database queries against the workflow_projects table.

    Follows the repository pattern so that routers and services never
    construct SQL directly.  All database I/O is async.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def count_by_stage(self) -> list[tuple[str, int]]:
        """Return (stage, count) pairs grouped by stage."""
        stmt = select(WorkflowProject.stage, func.count().label("cnt")).group_by(WorkflowProject.stage)
        result = await self._session.execute(stmt)
        return [(row.stage, row.cnt) for row in result.all()]

    async def projects_by_stage(self, stage: str) -> list[WorkflowProject]:
        """Return projects filtered by stage, ordered by entered_stage_at descending."""
        stmt = (
            select(WorkflowProject)
            .where(WorkflowProject.stage == stage)
            .order_by(WorkflowProject.entered_stage_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_blocked(self) -> int:
        """Return count of projects with status 'blocked'."""
        stmt = select(func.count()).select_from(WorkflowProject).where(WorkflowProject.status == "blocked")
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def avg_time_in_stage(self, stage: str) -> float | None:
        """Return average days between entered_stage_at and now for the given stage.

        Uses TIMESTAMPDIFF for MariaDB/MySQL and julianday for SQLite tests.
        The result is in fractional days.
        """
        dialect_name = getattr(getattr(self._session, "bind", None), "dialect", None)
        dialect_name = getattr(dialect_name, "name", "")
        if dialect_name == "sqlite":
            avg_expr = func.avg(
                func.julianday(func.current_timestamp()) - func.julianday(WorkflowProject.entered_stage_at)
            )
        else:
            avg_expr = func.avg(
                func.timestampdiff(
                    text("SECOND"),
                    WorkflowProject.entered_stage_at,
                    func.now(),
                )
            ) / 86400.0
        stmt = (
            select(avg_expr)
            .select_from(WorkflowProject)
            .where(WorkflowProject.stage == stage)
        )
        result = await self._session.execute(stmt)
        value = result.scalar_one_or_none()
        return round(float(value), 1) if value is not None else None

    async def count_active_in_stage(self, stage: str) -> int:
        """Return count of projects in stage excluding approved and blocked."""
        stmt = (
            select(func.count())
            .select_from(WorkflowProject)
            .where(
                WorkflowProject.stage == stage,
                WorkflowProject.status.notin_(("approved", "blocked")),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def total_projects(self) -> int:
        """Return total count of all workflow projects."""
        stmt = select(func.count()).select_from(WorkflowProject)
        result = await self._session.execute(stmt)
        return result.scalar_one()
