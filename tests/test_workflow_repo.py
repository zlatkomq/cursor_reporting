"""Tests for cursor_metrics.repositories.workflow_repo — WorkflowRepository query methods."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from cursor_metrics.models.db import Base, WorkflowProject
from cursor_metrics.repositories.workflow_repo import WorkflowRepository


@pytest.fixture()
async def session():
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as sess:
        yield sess

    await engine.dispose()


def _project(
    spec_id: str,
    name: str,
    stage: str,
    status: str = "active",
    entered_stage_at: datetime | None = None,
) -> WorkflowProject:
    return WorkflowProject(
        spec_id=spec_id,
        name=name,
        stage=stage,
        status=status,
        entered_stage_at=entered_stage_at or datetime.utcnow(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


class TestCountByStage:
    """count_by_stage returns (stage, count) pairs grouped by stage."""

    @pytest.mark.asyncio()
    async def test_returns_stage_counts(self, session: AsyncSession) -> None:
        session.add_all(
            [
                _project("001", "A", "planning"),
                _project("002", "B", "planning"),
                _project("003", "C", "implementation"),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        result = await repo.count_by_stage()

        stage_map = dict(result)
        assert stage_map["planning"] == 2
        assert stage_map["implementation"] == 1

    @pytest.mark.asyncio()
    async def test_returns_empty_list_when_no_data(self, session: AsyncSession) -> None:
        repo = WorkflowRepository(session)
        result = await repo.count_by_stage()
        assert result == []


class TestProjectsByStage:
    """projects_by_stage returns WorkflowProject list filtered by stage, ordered desc."""

    @pytest.mark.asyncio()
    async def test_filters_by_stage(self, session: AsyncSession) -> None:
        session.add_all(
            [
                _project("001", "A", "planning", entered_stage_at=datetime(2025, 1, 1)),
                _project("002", "B", "planning", entered_stage_at=datetime(2025, 6, 1)),
                _project("003", "C", "review"),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        result = await repo.projects_by_stage("planning")

        assert len(result) == 2
        assert all(isinstance(p, WorkflowProject) for p in result)
        assert result[0].entered_stage_at > result[1].entered_stage_at

    @pytest.mark.asyncio()
    async def test_returns_empty_for_unknown_stage(self, session: AsyncSession) -> None:
        session.add(_project("001", "A", "planning"))
        await session.commit()

        repo = WorkflowRepository(session)
        result = await repo.projects_by_stage("nonexistent")
        assert result == []


class TestCountBlocked:
    """count_blocked returns count of projects with status 'blocked'."""

    @pytest.mark.asyncio()
    async def test_counts_blocked_projects(self, session: AsyncSession) -> None:
        session.add_all(
            [
                _project("001", "A", "planning", status="blocked"),
                _project("002", "B", "review", status="blocked"),
                _project("003", "C", "planning", status="active"),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        assert await repo.count_blocked() == 2

    @pytest.mark.asyncio()
    async def test_returns_zero_when_none_blocked(self, session: AsyncSession) -> None:
        session.add(_project("001", "A", "planning", status="active"))
        await session.commit()

        repo = WorkflowRepository(session)
        assert await repo.count_blocked() == 0


class TestAvgTimeInStage:
    """avg_time_in_stage returns average days in the given stage."""

    @pytest.mark.asyncio()
    async def test_returns_average_days(self, session: AsyncSession) -> None:
        now = datetime.utcnow()
        session.add_all(
            [
                _project("001", "A", "planning", entered_stage_at=now - timedelta(days=10)),
                _project("002", "B", "planning", entered_stage_at=now - timedelta(days=20)),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        avg = await repo.avg_time_in_stage("planning")

        assert avg is not None
        assert 14.0 <= avg <= 16.0

    @pytest.mark.asyncio()
    async def test_returns_none_for_empty_stage(self, session: AsyncSession) -> None:
        repo = WorkflowRepository(session)
        result = await repo.avg_time_in_stage("nonexistent")
        assert result is None


class TestCountActiveInStage:
    """count_active_in_stage counts projects in stage excluding approved/blocked."""

    @pytest.mark.asyncio()
    async def test_counts_active_only(self, session: AsyncSession) -> None:
        session.add_all(
            [
                _project("001", "A", "planning", status="active"),
                _project("002", "B", "planning", status="in_progress"),
                _project("003", "C", "planning", status="approved"),
                _project("004", "D", "planning", status="blocked"),
                _project("005", "E", "review", status="active"),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        assert await repo.count_active_in_stage("planning") == 2

    @pytest.mark.asyncio()
    async def test_returns_zero_when_all_excluded(self, session: AsyncSession) -> None:
        session.add_all(
            [
                _project("001", "A", "planning", status="approved"),
                _project("002", "B", "planning", status="blocked"),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        assert await repo.count_active_in_stage("planning") == 0


class TestTotalProjects:
    """total_projects returns the total count of all rows."""

    @pytest.mark.asyncio()
    async def test_returns_total_count(self, session: AsyncSession) -> None:
        session.add_all(
            [
                _project("001", "A", "planning"),
                _project("002", "B", "review"),
                _project("003", "C", "implementation"),
            ]
        )
        await session.commit()

        repo = WorkflowRepository(session)
        assert await repo.total_projects() == 3

    @pytest.mark.asyncio()
    async def test_returns_zero_when_empty(self, session: AsyncSession) -> None:
        repo = WorkflowRepository(session)
        assert await repo.total_projects() == 0
