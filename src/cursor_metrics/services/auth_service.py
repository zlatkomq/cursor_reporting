"""JWT authentication and bcrypt password hashing service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import bcrypt
from jose import JWTError, jwt

from cursor_metrics.config import get_settings

if TYPE_CHECKING:
    from cursor_metrics.repositories.user_repo import UserRepository

_ALGORITHM = "HS256"


class AuthService:
    """Handles credential verification, JWT creation/validation, and password hashing.

    Collaborates with :class:`UserRepository` to look up users by email
    and verify their stored bcrypt password hashes.
    """

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def authenticate(self, email: str, password: str) -> str | None:
        """Verify credentials, return a signed JWT token or ``None``."""
        user = await self._user_repo.get_by_email(email)
        if user is None:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return self.create_token(email)

    def create_token(self, email: str) -> str:
        """Create a signed JWT with ``sub=email`` and ``exp`` claims."""
        settings = get_settings()
        expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        payload = {"sub": email, "exp": expire}
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)

    def verify_token(self, token: str) -> str | None:
        """Decode a JWT and return the ``sub`` (email) or ``None`` if invalid/expired."""
        settings = get_settings()
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
            return payload.get("sub")
        except JWTError:
            return None

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a plaintext password with bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Check a plaintext password against a bcrypt hash."""
        return bcrypt.checkpw(plain.encode(), hashed.encode())
