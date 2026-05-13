"""Shared pytest fixtures for the cursor-metrics test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Iterator


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Provide required env vars and clear the settings cache around every test."""
    from cursor_metrics.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key")
    yield
    get_settings.cache_clear()


def _mock_engine() -> MagicMock:
    """Return a mock async_engine so the app can be imported without a real DB."""
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=mock_conn)
    return engine


def mock_db_session() -> AsyncMock:
    """Return a mock AsyncSession for dependency override."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()
    return session


async def _mock_get_db() -> AsyncGenerator[AsyncMock]:
    yield mock_db_session()


@pytest.fixture()
async def async_client() -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the FastAPI app via ASGITransport."""
    from cursor_metrics.database import get_db
    from cursor_metrics.main import app

    app.dependency_overrides[get_db] = _mock_get_db
    try:
        with patch("cursor_metrics.main.async_engine", _mock_engine()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
    finally:
        app.dependency_overrides.pop(get_db, None)
