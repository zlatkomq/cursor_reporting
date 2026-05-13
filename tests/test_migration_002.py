"""Tests for migration 002 - expand telemetry schema."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MIGRATION_PATH = ROOT / "alembic" / "versions" / "002_expand_telemetry.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_002", MIGRATION_PATH)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestMigration002Import:
    """Verify the migration module imports correctly."""

    def test_migration_file_exists(self) -> None:
        assert MIGRATION_PATH.is_file()

    def test_migration_is_importable(self) -> None:
        mod = _load_migration()
        assert mod is not None


class TestMigration002Functions:
    """Verify upgrade() and downgrade() functions exist."""

    def test_has_upgrade_function(self) -> None:
        mod = _load_migration()
        assert hasattr(mod, "upgrade")
        assert callable(mod.upgrade)

    def test_has_downgrade_function(self) -> None:
        mod = _load_migration()
        assert hasattr(mod, "downgrade")
        assert callable(mod.downgrade)


class TestMigration002RevisionChain:
    """Verify the revision chain links back to 001."""

    def test_revision_is_002(self) -> None:
        mod = _load_migration()
        assert mod.revision == "002"

    def test_down_revision_is_001(self) -> None:
        mod = _load_migration()
        assert mod.down_revision == "001"
