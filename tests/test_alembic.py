"""Tests for Alembic configuration and initial migration."""

from __future__ import annotations

import ast
import configparser
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

ROOT = Path(__file__).resolve().parent.parent


class TestAlembicIni:
    """Verify alembic.ini exists and is parseable."""

    def test_alembic_ini_exists(self) -> None:
        assert (ROOT / "alembic.ini").is_file()

    def test_alembic_ini_parseable(self) -> None:
        cfg = configparser.ConfigParser()
        cfg.read(ROOT / "alembic.ini")
        assert "alembic" in cfg.sections()

    def test_alembic_ini_script_location(self) -> None:
        cfg = configparser.ConfigParser()
        cfg.read(ROOT / "alembic.ini")
        assert cfg.get("alembic", "script_location") == "alembic"

    def test_alembic_ini_sqlalchemy_url_empty(self) -> None:
        cfg = configparser.ConfigParser()
        cfg.read(ROOT / "alembic.ini")
        assert cfg.get("alembic", "sqlalchemy.url") == ""


class TestEnvPy:
    """Verify alembic/env.py references the correct metadata and has async support."""

    def test_env_py_exists(self) -> None:
        assert (ROOT / "alembic" / "env.py").is_file()

    def test_env_py_imports_base_metadata(self) -> None:
        source = (ROOT / "alembic" / "env.py").read_text()
        assert "Base.metadata" in source or "Base" in source

    def test_env_py_sets_target_metadata(self) -> None:
        source = (ROOT / "alembic" / "env.py").read_text()
        assert "target_metadata" in source

    def test_env_py_has_async_runner(self) -> None:
        source = (ROOT / "alembic" / "env.py").read_text()
        assert "run_async_migrations" in source

    def test_env_py_imports_models(self) -> None:
        source = (ROOT / "alembic" / "env.py").read_text()
        assert "cursor_metrics.models.db" in source


class TestScriptMako:
    """Verify the Alembic migration template exists."""

    def test_script_mako_exists(self) -> None:
        assert (ROOT / "alembic" / "script.py.mako").is_file()

    def test_script_mako_has_revision_variable(self) -> None:
        source = (ROOT / "alembic" / "script.py.mako").read_text()
        assert "revision" in source

    def test_script_mako_has_upgrade_downgrade(self) -> None:
        source = (ROOT / "alembic" / "script.py.mako").read_text()
        assert "def upgrade()" in source
        assert "def downgrade()" in source


class TestInitialMigration:
    """Verify the initial migration script creates all 3 tables."""

    @pytest.fixture(autouse=True)
    def _required_env(self, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
        from cursor_metrics.config import get_settings

        get_settings.cache_clear()
        monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
        monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
        yield
        get_settings.cache_clear()

    def test_migration_file_exists(self) -> None:
        assert (ROOT / "alembic" / "versions" / "001_initial_schema.py").is_file()

    def test_migration_has_upgrade_function(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        tree = ast.parse(source)
        func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "upgrade" in func_names

    def test_migration_has_downgrade_function(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        tree = ast.parse(source)
        func_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        assert "downgrade" in func_names

    def test_migration_creates_metrics_events(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        assert "metrics_events" in source

    def test_migration_creates_model_pricing(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        assert "model_pricing" in source

    def test_migration_creates_dashboard_users(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        assert "dashboard_users" in source

    def test_migration_downgrade_drops_all_tables(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        assert source.count("drop_table") >= 3

    def test_migration_has_revision_id(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        assert "revision" in source
        assert "down_revision" in source

    def test_migration_is_importable(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "migration_001",
            ROOT / "alembic" / "versions" / "001_initial_schema.py",
        )
        assert spec is not None
        assert spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)

    def test_migration_creates_indexes(self) -> None:
        source = (ROOT / "alembic" / "versions" / "001_initial_schema.py").read_text()
        assert "ix_metrics_events_user_email_timestamp" in source
        assert "ix_metrics_events_model_timestamp" in source
        assert "ix_metrics_events_conversation_id" in source
