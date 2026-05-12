"""Tests for auth router — login/logout endpoints."""

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


class TestAPILogin:
    """POST /api/v1/auth/login — JSON API."""

    @pytest.mark.asyncio()
    async def test_valid_credentials_returns_token(self, client: AsyncClient, mock_db_session: AsyncMock) -> None:
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = "$2b$12$hashvalue"

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "cursor_metrics.services.auth_service.AuthService.verify_password",
            return_value=True,
        ):
            resp = await client.post(
                "/api/v1/auth/login",
                json={"email": "user@example.com", "password": "correct"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio()
    async def test_invalid_credentials_returns_401(self, client: AsyncClient, mock_db_session: AsyncMock) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "bad@example.com", "password": "wrong"},
        )

        assert resp.status_code == 401
        body = resp.json()
        assert body["error"] == "INVALID_CREDENTIALS"
        assert body["detail"] == "Invalid email or password"
        assert "timestamp" in body


class TestFormLogin:
    """POST /dashboard/login — form submission."""

    @pytest.mark.asyncio()
    async def test_valid_credentials_redirects_with_cookie(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        mock_user = MagicMock()
        mock_user.email = "user@example.com"
        mock_user.password_hash = "$2b$12$hashvalue"

        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = mock_user
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        with patch(
            "cursor_metrics.services.auth_service.AuthService.verify_password",
            return_value=True,
        ):
            resp = await client.post(
                "/dashboard/login",
                data={"email": "user@example.com", "password": "correct"},
                follow_redirects=False,
            )

        assert resp.status_code == 303
        assert resp.headers["location"] == "/dashboard"
        assert "session" in resp.cookies

    @pytest.mark.asyncio()
    async def test_invalid_credentials_rerenders_with_error(
        self, client: AsyncClient, mock_db_session: AsyncMock
    ) -> None:
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        resp = await client.post(
            "/dashboard/login",
            data={"email": "bad@example.com", "password": "wrong"},
            follow_redirects=False,
        )

        assert resp.status_code == 200
        assert "Invalid email or password" in resp.text


class TestLogout:
    """GET /dashboard/logout — clears cookie and redirects."""

    @pytest.mark.asyncio()
    async def test_logout_redirects_to_login(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/logout", follow_redirects=False)

        assert resp.status_code == 303
        assert resp.headers["location"] == "/dashboard/login"

    @pytest.mark.asyncio()
    async def test_logout_clears_session_cookie(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/logout", follow_redirects=False)

        set_cookie = resp.headers.get("set-cookie", "")
        assert "session" in set_cookie
        assert "Max-Age=0" in set_cookie or "expires" in set_cookie.lower()


class TestLoginPage:
    """GET /dashboard/login — login page HTML."""

    @pytest.mark.asyncio()
    async def test_returns_html_form(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/login")

        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "<form" in resp.text
        assert 'name="email"' in resp.text
        assert 'name="password"' in resp.text
