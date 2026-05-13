"""Tests for cursor_metrics.repositories.user_repo — UserRepository."""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from cursor_metrics.models.db import DashboardUser
from cursor_metrics.repositories.user_repo import UserRepository


class TestUserRepositoryImport:
    """Verify UserRepository is importable from multiple paths."""

    def test_import_from_module(self) -> None:
        from cursor_metrics.repositories.user_repo import UserRepository as Cls

        assert Cls is not None

    def test_import_from_package(self) -> None:
        from cursor_metrics.repositories import UserRepository as Cls

        assert Cls is not None

    def test_class_is_in_package_all(self) -> None:
        import cursor_metrics.repositories as pkg

        assert "UserRepository" in pkg.__all__


class TestUserRepositoryConstructor:
    """Verify UserRepository.__init__ accepts an AsyncSession."""

    def test_accepts_session_parameter(self) -> None:
        sig = inspect.signature(UserRepository.__init__)
        params = list(sig.parameters.keys())
        assert "session" in params

    def test_session_annotated_as_async_session(self) -> None:
        assert UserRepository.__init__.__annotations__["session"] == "AsyncSession"

    def test_instantiation_stores_session(self) -> None:
        mock_session = MagicMock(spec=AsyncSession)
        repo = UserRepository(session=mock_session)
        assert repo._session is mock_session

    def test_has_docstring(self) -> None:
        assert UserRepository.__doc__ is not None
        assert len(UserRepository.__doc__.strip()) > 0


class TestGetByEmail:
    """Tests for UserRepository.get_by_email."""

    @pytest.fixture()
    def _session(self) -> AsyncMock:
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.mark.asyncio()
    async def test_returns_none_when_user_not_found(self, _session: AsyncMock) -> None:
        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = None
        result_mock.scalars.return_value = scalars_mock
        _session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session=_session)
        user = await repo.get_by_email("nobody@example.com")

        assert user is None
        _session.execute.assert_awaited_once()

    @pytest.mark.asyncio()
    async def test_returns_user_when_found(self, _session: AsyncMock) -> None:
        expected_user = MagicMock(spec=DashboardUser)
        expected_user.email = "found@example.com"

        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = expected_user
        result_mock.scalars.return_value = scalars_mock
        _session.execute = AsyncMock(return_value=result_mock)

        repo = UserRepository(session=_session)
        user = await repo.get_by_email("found@example.com")

        assert user is expected_user
        assert user.email == "found@example.com"


class TestCreate:
    """Tests for UserRepository.create."""

    @pytest.fixture()
    def _session(self) -> AsyncMock:
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.mark.asyncio()
    async def test_create_adds_and_flushes(self, _session: AsyncMock) -> None:
        repo = UserRepository(session=_session)
        user = await repo.create("new@example.com", "hashed_pw")

        assert isinstance(user, DashboardUser)
        assert user.email == "new@example.com"
        assert user.password_hash == "hashed_pw"
        _session.add.assert_called_once_with(user)
        _session.flush.assert_awaited_once()
        _session.refresh.assert_awaited_once_with(user)

    @pytest.mark.asyncio()
    async def test_create_returns_dashboard_user_instance(self, _session: AsyncMock) -> None:
        repo = UserRepository(session=_session)
        user = await repo.create("user@example.com", "hash123")

        assert isinstance(user, DashboardUser)
        assert user.email == "user@example.com"
        assert user.password_hash == "hash123"


class TestGetByEmailAfterCreate:
    """Integration-style test: create then retrieve via mocked session."""

    @pytest.mark.asyncio()
    async def test_round_trip(self) -> None:
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()

        repo = UserRepository(session=session)
        created = await repo.create("rt@example.com", "pw_hash")

        result_mock = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.first.return_value = created
        result_mock.scalars.return_value = scalars_mock
        session.execute = AsyncMock(return_value=result_mock)

        fetched = await repo.get_by_email("rt@example.com")
        assert fetched is created
        assert fetched.email == "rt@example.com"


class TestCreateDuplicateEmail:
    """Verify that creating a duplicate email propagates the DB error."""

    @pytest.mark.asyncio()
    async def test_duplicate_email_raises(self) -> None:
        from sqlalchemy.exc import IntegrityError

        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()
        session.flush = AsyncMock(
            side_effect=IntegrityError("duplicate", params=None, orig=Exception()),
        )
        session.refresh = AsyncMock()

        repo = UserRepository(session=session)
        with pytest.raises(IntegrityError):
            await repo.create("dup@example.com", "hash")
