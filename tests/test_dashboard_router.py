"""Tests for dashboard router — HTML views (updated for two-tab redesign)."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@pytest.fixture()
def mock_db_session() -> AsyncMock:
    """Return a mock AsyncSession."""
    return AsyncMock()


@pytest.fixture()
async def client(mock_db_session: AsyncMock) -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient with mocked DB dependency."""
    from cursor_metrics.database import get_db
    from cursor_metrics.main import app

    async def _override_get_db():
        yield mock_db_session

    app.dependency_overrides[get_db] = _override_get_db

    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=mock_conn)

    with patch("cursor_metrics.main.async_engine", engine):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c

    app.dependency_overrides.clear()


class TestDashboardOverview:
    """GET /dashboard with authenticated user → 200 HTML."""

    @pytest.mark.asyncio()
    async def test_returns_200_html(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._get_overview_data") as mock_get:
            mock_get.return_value = {
                "total_tokens": 2400000,
                "total_cost": 4832.50,
                "total_requests": 12450,
                "active_models": 4,
                "daily_tokens": [],
                "recent_events": [],
                "model_distribution": {},
                "avg_response_ms": 0.0,
            }

            resp = await client.get("/dashboard")

        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


class TestDashboardOverviewUnauthenticated:
    """GET /dashboard without auth → redirect to login."""

    @pytest.mark.asyncio()
    async def test_redirects_to_login(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = await client.get(
            "/dashboard",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )

        assert resp.status_code == 303
        assert resp.headers["location"] == "/dashboard/login"


class TestLegacyRedirects:
    """Old dashboard routes redirect to /dashboard."""

    @pytest.mark.asyncio()
    async def test_by_model_redirects(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/by-model", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/dashboard"

    @pytest.mark.asyncio()
    async def test_by_developer_redirects(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/by-developer", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/dashboard"

    @pytest.mark.asyncio()
    async def test_by_command_redirects(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/by-command", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/dashboard"
