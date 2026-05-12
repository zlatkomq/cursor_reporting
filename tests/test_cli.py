"""Tests for the cursor-metrics CLI (cli.py / __main__.py)."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestCLIImport:
    """cli.py is importable and exposes the expected public API."""

    def test_module_importable(self) -> None:
        mod = importlib.import_module("cursor_metrics.cli")
        assert hasattr(mod, "main")
        assert callable(mod.main)

    def test_create_user_importable(self) -> None:
        from cursor_metrics.cli import create_user

        assert callable(create_user)


class TestCLIArgParsing:
    """Argument parser handles expected flags."""

    def test_create_user_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["cli", "create-user", "--email", "a@b.com", "--password", "s3cret"])
        with patch("cursor_metrics.cli.asyncio") as mock_asyncio:
            from cursor_metrics.cli import main

            main()
            mock_asyncio.run.assert_called_once()
            coro = mock_asyncio.run.call_args[0][0]
            coro.close()

    def test_missing_email_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["cli", "create-user", "--password", "s3cret"])
        with pytest.raises(SystemExit) as exc_info:
            from cursor_metrics.cli import main

            main()
        assert exc_info.value.code == 2

    def test_missing_password_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["cli", "create-user", "--email", "a@b.com"])
        with pytest.raises(SystemExit) as exc_info:
            from cursor_metrics.cli import main

            main()
        assert exc_info.value.code == 2


class TestCLINoCommand:
    """CLI exits with error code when no subcommand is given."""

    def test_no_command_exits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["cli"])
        with pytest.raises(SystemExit) as exc_info:
            from cursor_metrics.cli import main

            main()
        assert exc_info.value.code == 1


class TestCreateUserCommand:
    """create_user calls AuthService.hash_password and UserRepository.create."""

    @pytest.mark.anyio()
    async def test_creates_user_successfully(self) -> None:
        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_user = MagicMock()
        mock_repo_instance = AsyncMock()
        mock_repo_instance.create = AsyncMock(return_value=mock_user)

        with (
            patch("cursor_metrics.database.AsyncSessionLocal", return_value=mock_session_ctx),
            patch(
                "cursor_metrics.services.auth_service.AuthService.hash_password",
                return_value="hashed-pw",
            ) as mock_hash,
            patch(
                "cursor_metrics.repositories.user_repo.UserRepository",
                return_value=mock_repo_instance,
            ),
        ):
            from cursor_metrics.cli import create_user

            await create_user("test@example.com", "plain-pw")

            mock_hash.assert_called_once_with("plain-pw")
            mock_repo_instance.create.assert_called_once_with(email="test@example.com", password_hash="hashed-pw")
            mock_session.commit.assert_called_once()


class TestCLIDuplicateEmail:
    """IntegrityError on duplicate email is caught and reported gracefully."""

    @pytest.mark.anyio()
    async def test_duplicate_email_prints_error(self, capsys: pytest.CaptureFixture[str]) -> None:
        from sqlalchemy.exc import IntegrityError

        mock_session = AsyncMock()
        mock_session_ctx = AsyncMock()
        mock_session_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session_ctx.__aexit__ = AsyncMock(return_value=False)

        mock_repo_instance = AsyncMock()
        mock_repo_instance.create = AsyncMock(
            side_effect=IntegrityError("dup", params=None, orig=Exception("Duplicate entry"))
        )

        with (
            patch("cursor_metrics.database.AsyncSessionLocal", return_value=mock_session_ctx),
            patch(
                "cursor_metrics.services.auth_service.AuthService.hash_password",
                return_value="hashed-pw",
            ),
            patch(
                "cursor_metrics.repositories.user_repo.UserRepository",
                return_value=mock_repo_instance,
            ),
            pytest.raises(SystemExit) as exc_info,
        ):
            from cursor_metrics.cli import create_user

            await create_user("dup@example.com", "pw")

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "already exists" in captured.err
