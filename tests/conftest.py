"""Shared pytest fixtures for the cursor-metrics test suite."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator


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


@pytest.fixture()
async def async_client() -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the FastAPI app via ASGITransport."""
    from cursor_metrics.main import app

    with patch("cursor_metrics.main.async_engine", _mock_engine()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
