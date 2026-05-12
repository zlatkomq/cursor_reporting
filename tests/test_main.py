"""Tests for cursor_metrics.main — FastAPI app and health-check endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


class TestAppInstance:
    """Verify the module exposes a properly configured FastAPI app."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    def test_app_is_fastapi_instance(self) -> None:
        from cursor_metrics.main import app

        assert isinstance(app, FastAPI)

    def test_app_title(self) -> None:
        from cursor_metrics.main import app

        assert app.title == "Cursor Metrics"


class TestHealthCheckEndpoint:
    """Verify GET / returns a valid HealthCheckResponse."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    @staticmethod
    def _mock_engine_connected() -> MagicMock:
        """Return a mock async_engine whose connect() yields a working connection."""
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(return_value=mock_conn)
        return mock_engine

    async def test_health_returns_200(self) -> None:
        from cursor_metrics.main import app

        with patch("cursor_metrics.main.async_engine", self._mock_engine_connected()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        assert resp.status_code == 200

    async def test_health_returns_correct_json_shape(self) -> None:
        from cursor_metrics.main import app

        with patch("cursor_metrics.main.async_engine", self._mock_engine_connected()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        body = resp.json()
        assert "status" in body
        assert "version" in body
        assert "database" in body

    async def test_health_status_is_ok(self) -> None:
        from cursor_metrics.main import app

        with patch("cursor_metrics.main.async_engine", self._mock_engine_connected()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        assert resp.json()["status"] == "ok"

    async def test_health_version_matches_package(self) -> None:
        from cursor_metrics import __version__
        from cursor_metrics.main import app

        with patch("cursor_metrics.main.async_engine", self._mock_engine_connected()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        assert resp.json()["version"] == __version__

    async def test_health_database_connected_on_success(self) -> None:
        from cursor_metrics.main import app

        with patch("cursor_metrics.main.async_engine", self._mock_engine_connected()):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        assert resp.json()["database"] == "connected"

    async def test_health_database_disconnected_on_failure(self) -> None:
        from cursor_metrics.main import app

        mock_engine = MagicMock()
        mock_engine.connect = MagicMock(side_effect=Exception("connection refused"))

        with patch("cursor_metrics.main.async_engine", mock_engine):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        assert resp.status_code == 200
        assert resp.json()["database"] == "disconnected"


class TestOpenAPIDocs:
    """Verify /docs (OpenAPI UI) is accessible."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    async def test_docs_returns_200(self) -> None:
        from cursor_metrics.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/docs")

        assert resp.status_code == 200
