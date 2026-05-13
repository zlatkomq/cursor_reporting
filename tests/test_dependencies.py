"""Tests for cursor_metrics.dependencies — get_current_user."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from cursor_metrics.dependencies import get_current_user
from cursor_metrics.services.auth_service import AuthService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


def _make_app() -> FastAPI:
    """Build a minimal FastAPI app with a single protected route."""
    test_app = FastAPI()

    @test_app.get("/protected")
    async def protected(user: str = Depends(get_current_user)) -> dict[str, str]:
        return {"email": user}

    return test_app


def _make_token(email: str = "test@example.com") -> str:
    """Create a valid JWT for testing."""
    svc = AuthService(user_repo=MagicMock())
    return svc.create_token(email)


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """Yield an httpx AsyncClient wired to the test app."""
    app = _make_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestGetCurrentUserFromCookie:
    """Valid session cookie → returns email."""

    @pytest.mark.asyncio()
    async def test_valid_cookie_returns_email(self, client: AsyncClient) -> None:
        token = _make_token("cookie@example.com")
        resp = await client.get("/protected", cookies={"session": token})
        assert resp.status_code == 200
        assert resp.json()["email"] == "cookie@example.com"


class TestGetCurrentUserFromBearer:
    """Valid Authorization header → returns email."""

    @pytest.mark.asyncio()
    async def test_valid_bearer_returns_email(self, client: AsyncClient) -> None:
        token = _make_token("bearer@example.com")
        resp = await client.get(
            "/protected",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "bearer@example.com"


class TestGetCurrentUserNoAuth:
    """No cookie or header, API request → 401."""

    @pytest.mark.asyncio()
    async def test_no_auth_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/protected")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Not authenticated"


class TestGetCurrentUserNoAuthHTML:
    """No cookie or header, HTML request → redirect to login."""

    @pytest.mark.asyncio()
    async def test_no_auth_html_redirects(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/protected",
            headers={"Accept": "text/html"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/dashboard/login"


class TestGetCurrentUserInvalidToken:
    """Bad token → 401."""

    @pytest.mark.asyncio()
    async def test_invalid_cookie_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get("/protected", cookies={"session": "garbage.token.here"})
        assert resp.status_code == 401

    @pytest.mark.asyncio()
    async def test_invalid_bearer_returns_401(self, client: AsyncClient) -> None:
        resp = await client.get(
            "/protected",
            headers={"Authorization": "Bearer garbage.token.here"},
        )
        assert resp.status_code == 401


class TestGetCurrentUserCookiePriority:
    """Both cookie and header present → cookie wins."""

    @pytest.mark.asyncio()
    async def test_cookie_takes_precedence(self, client: AsyncClient) -> None:
        cookie_token = _make_token("cookie@example.com")
        bearer_token = _make_token("bearer@example.com")
        resp = await client.get(
            "/protected",
            cookies={"session": cookie_token},
            headers={"Authorization": f"Bearer {bearer_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "cookie@example.com"
