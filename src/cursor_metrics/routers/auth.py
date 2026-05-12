"""Auth router — dashboard login and session management."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Form, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from cursor_metrics.config import get_settings
from cursor_metrics.database import get_db
from cursor_metrics.repositories.user_repo import UserRepository
from cursor_metrics.services.auth_service import AuthService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def _build_auth_service(session: AsyncSession) -> AuthService:
    return AuthService(UserRepository(session))


_LOGIN_PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Login — Cursor Metrics</title></head>
<body>
<h1>Login</h1>
{error}
<form method="post" action="/dashboard/login">
  <label>Email <input type="email" name="email" required></label><br>
  <label>Password <input type="password" name="password" required></label><br>
  <button type="submit">Login</button>
</form>
</body>
</html>
"""


class _LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/api/v1/auth/login")
async def api_login(
    body: _LoginRequest,
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> JSONResponse:
    """JSON API login — returns access token or 401."""
    auth_service = _build_auth_service(session)
    token = await auth_service.authenticate(body.email, body.password)
    if token is None:
        return JSONResponse(
            status_code=401,
            content={
                "error": "INVALID_CREDENTIALS",
                "detail": "Invalid email or password",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
    return JSONResponse(
        status_code=200,
        content={"access_token": token, "token_type": "bearer"},
    )


@router.get("/dashboard/login", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    """Render the login form."""
    return HTMLResponse(_LOGIN_PAGE_HTML.format(error=""))


@router.post("/dashboard/login")
async def form_login(
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_db),  # noqa: B008
) -> Response:
    """Form-based login — sets cookie and redirects on success."""
    auth_service = _build_auth_service(session)
    token = await auth_service.authenticate(email, password)
    if token is None:
        error_html = '<p style="color:red">Invalid email or password</p>'
        return HTMLResponse(
            _LOGIN_PAGE_HTML.format(error=error_html),
            status_code=200,
        )
    settings = get_settings()
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/dashboard/logout")
async def logout() -> Response:
    """Clear the session cookie and redirect to login."""
    response = RedirectResponse(url="/dashboard/login", status_code=303)
    response.delete_cookie(key="session", path="/")
    return response
