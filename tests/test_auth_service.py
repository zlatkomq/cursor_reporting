"""Tests for cursor_metrics.services.auth_service — AuthService."""

from __future__ import annotations

from datetime import timedelta, timezone
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from jose import jwt

from cursor_metrics.models.db import DashboardUser
from cursor_metrics.services.auth_service import AuthService, _ALGORITHM

if TYPE_CHECKING:
    pass


class TestAuthServiceImport:
    """Verify AuthService is importable from multiple paths."""

    def test_import_from_module(self) -> None:
        from cursor_metrics.services.auth_service import AuthService as Cls

        assert Cls is not None

    def test_import_from_package(self) -> None:
        from cursor_metrics.services import AuthService as Cls

        assert Cls is not None

    def test_class_is_in_package_all(self) -> None:
        import cursor_metrics.services as pkg

        assert "AuthService" in pkg.__all__


class TestHashPassword:
    """Tests for AuthService.hash_password."""

    def test_produces_bcrypt_string(self) -> None:
        hashed = AuthService.hash_password("mysecret")
        assert hashed.startswith("$2b$")

    def test_different_hashes_for_same_input(self) -> None:
        h1 = AuthService.hash_password("same")
        h2 = AuthService.hash_password("same")
        assert h1 != h2


class TestVerifyPassword:
    """Tests for AuthService.verify_password."""

    def test_correct_password_returns_true(self) -> None:
        hashed = AuthService.hash_password("correct")
        assert AuthService.verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self) -> None:
        hashed = AuthService.hash_password("correct")
        assert AuthService.verify_password("wrong", hashed) is False


class TestCreateToken:
    """Tests for AuthService.create_token."""

    def test_returns_string(self) -> None:
        repo = MagicMock()
        svc = AuthService(user_repo=repo)
        token = svc.create_token("user@example.com")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_contains_expected_claims(self) -> None:
        from cursor_metrics.config import get_settings

        repo = MagicMock()
        svc = AuthService(user_repo=repo)
        token = svc.create_token("user@example.com")

        settings = get_settings()
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
        assert payload["sub"] == "user@example.com"
        assert "exp" in payload

    def test_token_exp_matches_configured_minutes(self) -> None:
        from datetime import datetime

        from cursor_metrics.config import get_settings

        repo = MagicMock()
        svc = AuthService(user_repo=repo)

        before = datetime.now(timezone.utc)
        token = svc.create_token("user@example.com")
        after = datetime.now(timezone.utc)

        settings = get_settings()
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[_ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)

        expected_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        low = before + expected_delta - timedelta(seconds=2)
        high = after + expected_delta + timedelta(seconds=2)
        assert low <= exp <= high


class TestVerifyToken:
    """Tests for AuthService.verify_token."""

    def test_valid_token_returns_email(self) -> None:
        repo = MagicMock()
        svc = AuthService(user_repo=repo)
        token = svc.create_token("valid@example.com")
        result = svc.verify_token(token)
        assert result == "valid@example.com"

    def test_expired_token_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("JWT_EXPIRE_MINUTES", "0")
        get_settings.cache_clear()

        repo = MagicMock()
        svc = AuthService(user_repo=repo)

        settings = get_settings()
        expired_payload = {
            "sub": "expired@example.com",
            "exp": 0,
        }
        token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=_ALGORITHM)

        result = svc.verify_token(token)
        assert result is None

    def test_garbage_token_returns_none(self) -> None:
        repo = MagicMock()
        svc = AuthService(user_repo=repo)
        result = svc.verify_token("not.a.valid.jwt.token")
        assert result is None

    def test_wrong_secret_returns_none(self) -> None:
        from cursor_metrics.config import get_settings

        settings = get_settings()
        payload = {"sub": "user@example.com", "exp": 9999999999}
        token = jwt.encode(payload, "wrong-secret-key", algorithm=_ALGORITHM)

        repo = MagicMock()
        svc = AuthService(user_repo=repo)
        result = svc.verify_token(token)
        assert result is None


class TestAuthenticate:
    """Tests for AuthService.authenticate."""

    @pytest.fixture()
    def _user(self) -> MagicMock:
        user = MagicMock(spec=DashboardUser)
        user.email = "auth@example.com"
        user.password_hash = AuthService.hash_password("secret123")
        return user

    @pytest.fixture()
    def _mock_repo(self) -> AsyncMock:
        return AsyncMock()

    @pytest.mark.asyncio()
    async def test_valid_credentials_returns_token(
        self, _mock_repo: AsyncMock, _user: MagicMock
    ) -> None:
        _mock_repo.get_by_email = AsyncMock(return_value=_user)

        svc = AuthService(user_repo=_mock_repo)
        token = await svc.authenticate("auth@example.com", "secret123")

        assert token is not None
        assert isinstance(token, str)

        email = svc.verify_token(token)
        assert email == "auth@example.com"

    @pytest.mark.asyncio()
    async def test_wrong_password_returns_none(
        self, _mock_repo: AsyncMock, _user: MagicMock
    ) -> None:
        _mock_repo.get_by_email = AsyncMock(return_value=_user)

        svc = AuthService(user_repo=_mock_repo)
        result = await svc.authenticate("auth@example.com", "wrongpassword")

        assert result is None

    @pytest.mark.asyncio()
    async def test_unknown_email_returns_none(self, _mock_repo: AsyncMock) -> None:
        _mock_repo.get_by_email = AsyncMock(return_value=None)

        svc = AuthService(user_repo=_mock_repo)
        result = await svc.authenticate("nobody@example.com", "anything")

        assert result is None
        _mock_repo.get_by_email.assert_awaited_once_with("nobody@example.com")
