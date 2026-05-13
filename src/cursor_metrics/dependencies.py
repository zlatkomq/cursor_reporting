"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Cookie, HTTPException, Request
from jose import JWTError, jwt

from cursor_metrics.config import get_settings
from cursor_metrics.services.auth_service import _ALGORITHM


def _verify_jwt(token: str) -> str | None:
    """Decode a JWT and return the subject (email) or ``None``."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def get_current_user(
    request: Request,
    session: str | None = Cookie(default=None),
) -> str:
    """Extract and verify JWT from cookie or Authorization header.

    Resolution order:
    1. ``session`` cookie  (browser / dashboard requests)
    2. ``Authorization: Bearer <token>`` header  (API requests)

    On failure the response depends on the ``Accept`` header:
    * ``text/html`` → 303 redirect to ``/dashboard/login``
    * otherwise     → 401 JSON error
    """
    token: str | None = None

    if session:
        token = session

    if not token:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if token:
        email = _verify_jwt(token)
        if email:
            return email

    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        raise HTTPException(status_code=303, headers={"Location": "/dashboard/login"})
    raise HTTPException(status_code=401, detail="Not authenticated")
