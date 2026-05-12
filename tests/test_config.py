"""Tests for cursor_metrics.config — Settings and get_settings()."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestSettings:
    """Verify Settings fields, types, and defaults."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Provide required env vars so Settings can instantiate."""
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")

    def test_import(self) -> None:
        from cursor_metrics.config import Settings, get_settings  # noqa: F401

    def test_database_url_from_env(self) -> None:
        from cursor_metrics.config import Settings

        settings = Settings()
        assert settings.DATABASE_URL == "mysql+aiomysql://u:p@localhost:3306/test"

    def test_secret_key_from_env(self) -> None:
        from cursor_metrics.config import Settings

        settings = Settings()
        assert settings.SECRET_KEY == "test-secret-key-abc123"

    def test_app_version_defaults_to_package_version(self) -> None:
        from cursor_metrics import __version__
        from cursor_metrics.config import Settings

        settings = Settings()
        assert __version__ == settings.APP_VERSION

    def test_log_level_default(self) -> None:
        from cursor_metrics.config import Settings

        settings = Settings()
        assert settings.LOG_LEVEL == "INFO"

    def test_debug_default_false(self) -> None:
        from cursor_metrics.config import Settings

        settings = Settings()
        assert settings.DEBUG is False

    def test_log_level_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cursor_metrics.config import Settings

        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.LOG_LEVEL == "DEBUG"

    def test_debug_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cursor_metrics.config import Settings

        monkeypatch.setenv("DEBUG", "true")
        settings = Settings()
        assert settings.DEBUG is True

    def test_database_url_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cursor_metrics.config import Settings

        monkeypatch.delenv("DATABASE_URL")
        with pytest.raises(ValidationError):
            Settings()

    def test_secret_key_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from cursor_metrics.config import Settings

        monkeypatch.delenv("SECRET_KEY")
        with pytest.raises(ValidationError):
            Settings()


class TestGetSettings:
    """Verify get_settings() returns a cached Settings instance."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")

    def test_returns_settings_instance(self) -> None:
        from cursor_metrics.config import Settings, get_settings

        result = get_settings()
        assert isinstance(result, Settings)

    def test_cached_singleton(self) -> None:
        from cursor_metrics.config import get_settings

        first = get_settings()
        second = get_settings()
        assert first is second
