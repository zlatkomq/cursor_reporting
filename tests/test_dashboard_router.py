"""Tests for dashboard router — HTML views."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

_MOCK_OVERVIEW = {
    "period_days": 30,
    "total_events": 12450,
    "active_developers": 18,
    "top_model": "claude-4-opus",
    "estimated_cost_usd": 342.50,
    "daily_counts": [
        {"date": "2026-05-01", "count": 420},
        {"date": "2026-05-02", "count": 380},
    ],
}


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


def _fake_auth_user(email: str = "admin@test.com"):
    """Return a dependency override that fakes authentication."""
    from cursor_metrics.dependencies import get_current_user

    async def _override():
        return email

    return get_current_user, _override


class TestDashboardOverview:
    """GET /dashboard with authenticated user → 200 HTML."""

    @pytest.mark.asyncio()
    async def test_returns_200_html(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get("/dashboard")

        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    @pytest.mark.asyncio()
    async def test_custom_days_param(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get("/dashboard?days=7")

        assert resp.status_code == 200
        mock_svc.get_overview.assert_called_once_with(7)


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


class TestDashboardOverviewContent:
    """GET /dashboard response contains stat card values and chart canvas."""

    @pytest.mark.asyncio()
    async def test_contains_stat_card_values(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get("/dashboard")

        html = resp.text
        assert "12450" in html
        assert "18" in html
        assert "claude-4-opus" in html
        assert "342.50" in html

    @pytest.mark.asyncio()
    async def test_contains_chart_canvas(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get("/dashboard")

        assert '<canvas id="dailyChart">' in resp.text

    @pytest.mark.asyncio()
    async def test_contains_chart_data(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get("/dashboard")

        html = resp.text
        assert "2026-05-01" in html
        assert "2026-05-02" in html

    @pytest.mark.asyncio()
    async def test_contains_stat_card_labels(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get("/dashboard")

        html = resp.text
        assert "Total Events" in html
        assert "Active Developers" in html
        assert "Top Model" in html
        assert "Estimated Cost" in html


class TestByDeveloper:
    """GET /dashboard/by-developer — authenticated HTML page."""

    @pytest.mark.asyncio()
    async def test_authenticated_returns_200_with_table(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {
            "period_days": 30,
            "developers": [
                {
                    "email": "dev@company.com",
                    "event_count": 890,
                    "top_model": "claude-4-opus",
                    "avg_duration_ms": 32000,
                    "last_active": "2026-05-12T10:30:00",
                },
                {
                    "email": "other@company.com",
                    "event_count": 450,
                    "top_model": "gpt-4o",
                    "avg_duration_ms": 28000,
                    "last_active": "2026-05-11T08:15:00",
                },
            ],
        }

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_developer = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            resp = await client.get(
                "/dashboard/by-developer",
                headers={"accept": "text/html"},
            )

        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Usage by Developer" in resp.text
        assert "dev@company.com" in resp.text
        assert "other@company.com" in resp.text
        assert "claude-4-opus" in resp.text
        assert "32.0s" in resp.text
        assert "<table" in resp.text

    @pytest.mark.asyncio()
    async def test_empty_developers_shows_no_data_message(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {"period_days": 30, "developers": []}

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_developer = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            resp = await client.get(
                "/dashboard/by-developer",
                headers={"accept": "text/html"},
            )

        assert resp.status_code == 200
        assert "No data for this period" in resp.text


class TestByDeveloperUnauthenticated:
    """GET /dashboard/by-developer — unauthenticated access."""

    @pytest.mark.asyncio()
    async def test_unauthenticated_redirects_to_login(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = await client.get(
            "/dashboard/by-developer",
            headers={"accept": "text/html"},
            follow_redirects=False,
        )

        assert resp.status_code == 303
        assert resp.headers["location"] == "/dashboard/login"


class TestByModel:
    """GET /dashboard/by-model — authenticated HTML page."""

    @pytest.mark.asyncio()
    async def test_authenticated_returns_200_with_table(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {
            "period_days": 30,
            "models": [
                {
                    "model": "claude-4-opus",
                    "event_count": 5200,
                    "developer_count": 15,
                    "estimated_cost_usd": 180.25,
                    "avg_duration_ms": 28000,
                },
            ],
        }

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_model = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            resp = await client.get(
                "/dashboard/by-model",
                headers={"accept": "text/html"},
            )

        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "Usage by Model" in resp.text
        assert "claude-4-opus" in resp.text
        assert "$180.25" in resp.text
        assert "5,200" in resp.text
        assert "28.0s" in resp.text
        assert "<table" in resp.text


class TestByModelUnauthenticated:
    """GET /dashboard/by-model — unauthenticated access."""

    @pytest.mark.asyncio()
    async def test_unauthenticated_redirects_to_login(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides.pop(get_current_user, None)

        resp = await client.get(
            "/dashboard/by-model",
            headers={"accept": "text/html"},
            follow_redirects=False,
        )

        assert resp.status_code == 303
        assert resp.headers["location"] == "/dashboard/login"


class TestHTMXDateFilter:
    """HTMX requests return partial content without the full HTML wrapper."""

    @pytest.mark.asyncio()
    async def test_htmx_overview_returns_partial(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            resp = await client.get(
                "/dashboard?days=7",
                headers={"HX-Request": "true"},
            )

        assert resp.status_code == 200
        html = resp.text
        assert "<!DOCTYPE html>" not in html
        assert "<html" not in html
        assert "stat-card" in html
        assert "dailyChart" in html

    @pytest.mark.asyncio()
    async def test_htmx_by_developer_returns_partial(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {
            "period_days": 7,
            "developers": [
                {
                    "email": "dev@company.com",
                    "event_count": 200,
                    "top_model": "claude-4-opus",
                    "avg_duration_ms": 25000,
                    "last_active": "2026-05-10T14:00:00",
                },
            ],
        }

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_developer = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            resp = await client.get(
                "/dashboard/by-developer?days=7",
                headers={"HX-Request": "true"},
            )

        assert resp.status_code == 200
        html = resp.text
        assert "<!DOCTYPE html>" not in html
        assert "dev@company.com" in html
        assert "<table" in html

    @pytest.mark.asyncio()
    async def test_htmx_by_model_returns_partial(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {
            "period_days": 7,
            "models": [
                {
                    "model": "gpt-4o",
                    "event_count": 3100,
                    "developer_count": 10,
                    "estimated_cost_usd": 95.50,
                    "avg_duration_ms": 22000,
                },
            ],
        }

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_model = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            resp = await client.get(
                "/dashboard/by-model?days=7",
                headers={"HX-Request": "true"},
            )

        assert resp.status_code == 200
        html = resp.text
        assert "<!DOCTYPE html>" not in html
        assert "gpt-4o" in html
        assert "$95.50" in html


class TestHTMXDateFilterDays:
    """HTMX requests with different days values pass correct param to service."""

    @pytest.mark.asyncio()
    async def test_htmx_overview_days_7(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            await client.get(
                "/dashboard?days=7",
                headers={"HX-Request": "true"},
            )

        mock_svc.get_overview.assert_called_once_with(7)

    @pytest.mark.asyncio()
    async def test_htmx_overview_days_90(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "user@example.com"

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_overview = AsyncMock(return_value=_MOCK_OVERVIEW)
            mock_build.return_value = mock_svc

            await client.get(
                "/dashboard?days=90",
                headers={"HX-Request": "true"},
            )

        mock_svc.get_overview.assert_called_once_with(90)

    @pytest.mark.asyncio()
    async def test_htmx_by_developer_days_90(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {
            "period_days": 90,
            "developers": [],
        }

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_developer = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            await client.get(
                "/dashboard/by-developer?days=90",
                headers={"HX-Request": "true"},
            )

        mock_svc.get_by_developer.assert_called_once_with(days=90)

    @pytest.mark.asyncio()
    async def test_htmx_by_model_days_7(self, client: AsyncClient) -> None:
        from cursor_metrics.dependencies import get_current_user
        from cursor_metrics.main import app

        app.dependency_overrides[get_current_user] = lambda: "admin@test.com"

        mock_data = {
            "period_days": 7,
            "models": [],
        }

        with patch("cursor_metrics.routers.dashboard._build_metrics_service") as mock_build:
            mock_svc = AsyncMock()
            mock_svc.get_by_model = AsyncMock(return_value=mock_data)
            mock_build.return_value = mock_svc

            await client.get(
                "/dashboard/by-model?days=7",
                headers={"HX-Request": "true"},
            )

        mock_svc.get_by_model.assert_called_once_with(7)
