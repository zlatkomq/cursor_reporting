"""Unit tests for the GET / health-check endpoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import cursor_metrics

if TYPE_CHECKING:
    from httpx import AsyncClient


class TestHealthEndpoint:
    """Verify health-check response status, schema, and database reporting."""

    async def test_health_returns_200(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert resp.status_code == 200

    async def test_health_response_schema(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert set(resp.json().keys()) == {"status", "version", "database"}

    async def test_health_status_ok(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert resp.json()["status"] == "ok"

    async def test_health_version_matches_package(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert resp.json()["version"] == cursor_metrics.__version__

    async def test_health_database_connected(self, async_client: AsyncClient) -> None:
        resp = await async_client.get("/")
        assert resp.json()["database"] == "connected"

    async def test_health_database_disconnected(self) -> None:
        from httpx import ASGITransport, AsyncClient

        from cursor_metrics.main import app

        mock_conn = AsyncMock()
        mock_conn.__aenter__ = AsyncMock(side_effect=Exception("db down"))
        mock_conn.__aexit__ = AsyncMock(return_value=False)
        engine = MagicMock()
        engine.connect = MagicMock(return_value=mock_conn)

        with patch("cursor_metrics.main.async_engine", engine):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/")

        assert resp.status_code == 200
        assert resp.json()["database"] == "disconnected"
