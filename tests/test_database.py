"""Tests for cursor_metrics.database — async engine, session, and Base."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


class TestBase:
    """Verify Base is a proper DeclarativeBase subclass."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    def test_base_is_declarative_base_subclass(self) -> None:
        from cursor_metrics.database import Base

        assert issubclass(Base, DeclarativeBase)


class TestAsyncEngine:
    """Verify async_engine is created from Settings.DATABASE_URL."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    def test_async_engine_is_async_engine_instance(self) -> None:
        from cursor_metrics.database import async_engine

        assert isinstance(async_engine, AsyncEngine)

    def test_async_engine_uses_settings_database_url(self) -> None:
        from cursor_metrics.database import async_engine

        assert async_engine.url.render_as_string(hide_password=False) == "mysql+aiomysql://u:p@localhost:3306/test"

    def test_async_engine_echo_disabled(self) -> None:
        from cursor_metrics.database import async_engine

        assert async_engine.echo is False

    def test_async_engine_pool_pre_ping_enabled(self) -> None:
        from cursor_metrics.database import async_engine

        assert async_engine.pool._pre_ping is True


class TestAsyncSessionLocal:
    """Verify AsyncSessionLocal is an async_sessionmaker bound to the engine."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    def test_async_session_local_is_async_sessionmaker(self) -> None:
        from cursor_metrics.database import AsyncSessionLocal

        assert isinstance(AsyncSessionLocal, async_sessionmaker)

    def test_async_session_local_does_not_expire_on_commit(self) -> None:
        from cursor_metrics.database import AsyncSessionLocal

        assert AsyncSessionLocal.kw.get("expire_on_commit") is False

    def test_async_session_local_produces_async_session(self) -> None:
        from cursor_metrics.database import AsyncSessionLocal

        assert AsyncSessionLocal.class_ is AsyncSession


class TestGetDb:
    """Verify get_db() is an async generator yielding AsyncSession."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    def test_get_db_is_async_generator_function(self) -> None:
        from cursor_metrics.database import get_db

        assert inspect.isasyncgenfunction(get_db)

    async def test_get_db_yields_async_session(self) -> None:
        from cursor_metrics.database import get_db

        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock(return_value=mock_session)
        with patch("cursor_metrics.database.AsyncSessionLocal", mock_factory):
            session = await anext(get_db())
            assert session is mock_session

    async def test_get_db_closes_session_after_use(self) -> None:
        from cursor_metrics.database import get_db

        mock_session = AsyncMock(spec=AsyncSession)
        mock_factory = MagicMock(return_value=mock_session)
        with patch("cursor_metrics.database.AsyncSessionLocal", mock_factory):
            gen = get_db()
            await anext(gen)
            await gen.aclose()
            mock_session.close.assert_awaited_once()
