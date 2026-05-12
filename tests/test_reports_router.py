"""Tests for reports API router — GET /api/v1/metrics endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

OVERVIEW_RESPONSE = {
    "period_days": 30,
    "total_events": 150,
    "active_developers": 5,
    "top_model": "claude-4-opus",
    "estimated_cost_usd": 12.5,
    "daily_counts": [{"date": "2026-05-10", "count": 50}],
}
BY_DEVELOPER_RESPONSE = {
    "period_days": 30,
    "developers": [
        {
            "email": "dev@company.com",
            "event_count": 100,
            "top_model": "claude-4-opus",
            "avg_duration_ms": 3000.0,
            "last_active": "2026-05-12T10:00:00",
        },
    ],
}
BY_MODEL_RESPONSE = {
    "period_days": 30,
    "models": [
        {
            "model": "claude-4-opus",
            "event_count": 100,
            "developer_count": 3,
            "estimated_cost_usd": 10.0,
            "avg_duration_ms": 2500.0,
        },
    ],
}


def _mock_engine() -> MagicMock:
    mock_conn = AsyncMock()
    mock_conn.execute = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=False)
    engine = MagicMock()
    engine.connect = MagicMock(return_value=mock_conn)
    return engine


@pytest.fixture()
def _mock_services() -> None:
    """Patch MetricsService methods to return canned responses."""
    with (
        patch(
            "cursor_metrics.routers.reports.MetricsService.get_overview",
            new_callable=AsyncMock,
            return_value=OVERVIEW_RESPONSE,
        ),
        patch(
            "cursor_metrics.routers.reports.MetricsService.get_by_developer",
            new_callable=AsyncMock,
            return_value=BY_DEVELOPER_RESPONSE,
        ),
        patch(
            "cursor_metrics.routers.reports.MetricsService.get_by_model",
            new_callable=AsyncMock,
            return_value=BY_MODEL_RESPONSE,
        ),
    ):
        yield


async def _authenticated_user() -> str:
    return "test@example.com"


async def _mock_db() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
async def auth_client(_mock_services: None) -> AsyncIterator[AsyncClient]:
    from cursor_metrics.database import get_db
    from cursor_metrics.dependencies import get_current_user
    from cursor_metrics.main import app

    app.dependency_overrides[get_current_user] = _authenticated_user
    app.dependency_overrides[get_db] = _mock_db

    with patch("cursor_metrics.main.async_engine", _mock_engine()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()


@pytest.fixture()
async def unauth_client(_mock_services: None) -> AsyncIterator[AsyncClient]:
    from cursor_metrics.database import get_db
    from cursor_metrics.dependencies import get_current_user
    from cursor_metrics.main import app

    app.dependency_overrides[get_db] = _mock_db
    app.dependency_overrides.pop(get_current_user, None)

    with patch("cursor_metrics.main.async_engine", _mock_engine()):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

    app.dependency_overrides.clear()


class TestMetricsOverview:
    """GET /api/v1/metrics — overview endpoint."""

    async def test_authenticated_returns_200(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics")
        assert resp.status_code == 200

    async def test_authenticated_returns_correct_json(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics")
        body = resp.json()
        assert body["period_days"] == 30
        assert body["total_events"] == 150
        assert body["active_developers"] == 5
        assert body["top_model"] == "claude-4-opus"
        assert body["estimated_cost_usd"] == 12.5
        assert len(body["daily_counts"]) == 1

    async def test_unauthenticated_returns_401(self, unauth_client: AsyncClient) -> None:
        resp = await unauth_client.get("/api/v1/metrics")
        assert resp.status_code == 401


class TestMetricsByDeveloper:
    """GET /api/v1/metrics/by-developer — developer rankings."""

    async def test_authenticated_returns_200(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics/by-developer")
        assert resp.status_code == 200

    async def test_authenticated_returns_developer_data(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics/by-developer")
        body = resp.json()
        assert body["period_days"] == 30
        assert len(body["developers"]) == 1
        assert body["developers"][0]["email"] == "dev@company.com"

    async def test_unauthenticated_returns_401(self, unauth_client: AsyncClient) -> None:
        resp = await unauth_client.get("/api/v1/metrics/by-developer")
        assert resp.status_code == 401


class TestMetricsByModel:
    """GET /api/v1/metrics/by-model — model breakdown."""

    async def test_authenticated_returns_200(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics/by-model")
        assert resp.status_code == 200

    async def test_authenticated_returns_model_data(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics/by-model")
        body = resp.json()
        assert body["period_days"] == 30
        assert len(body["models"]) == 1
        assert body["models"][0]["model"] == "claude-4-opus"

    async def test_unauthenticated_returns_401(self, unauth_client: AsyncClient) -> None:
        resp = await unauth_client.get("/api/v1/metrics/by-model")
        assert resp.status_code == 401


class TestDaysParameter:
    """Query param ?days= validation across all endpoints."""

    async def test_default_days_is_30(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics")
        assert resp.status_code == 200
        assert resp.json()["period_days"] == 30

    async def test_explicit_days_7(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics", params={"days": 7})
        assert resp.status_code == 200

    async def test_explicit_days_90(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics", params={"days": 90})
        assert resp.status_code == 200

    async def test_invalid_days_returns_422(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics", params={"days": 15})
        assert resp.status_code == 422

    async def test_invalid_days_by_developer_returns_422(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics/by-developer", params={"days": 15})
        assert resp.status_code == 422

    async def test_invalid_days_by_model_returns_422(self, auth_client: AsyncClient) -> None:
        resp = await auth_client.get("/api/v1/metrics/by-model", params={"days": 15})
        assert resp.status_code == 422
