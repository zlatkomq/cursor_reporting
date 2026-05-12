"""Tests for cursor_metrics.models.db — ORM table definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Generator

import pytest
from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import DeclarativeBase


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    from cursor_metrics.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@localhost:3306/test")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
    yield
    get_settings.cache_clear()


class TestModelsImportable:
    """All three model classes are importable from cursor_metrics.models.db."""

    def test_metrics_event_importable(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        assert MetricsEvent is not None

    def test_model_pricing_importable(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        assert ModelPricing is not None

    def test_dashboard_user_importable(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        assert DashboardUser is not None

    def test_models_re_exported_from_init(self) -> None:
        from cursor_metrics.models import DashboardUser, MetricsEvent, ModelPricing

        assert MetricsEvent is not None
        assert ModelPricing is not None
        assert DashboardUser is not None


class TestModelsInheritBase:
    """All models inherit from the project's DeclarativeBase."""

    def test_metrics_event_inherits_base(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        assert issubclass(MetricsEvent, DeclarativeBase)

    def test_model_pricing_inherits_base(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        assert issubclass(ModelPricing, DeclarativeBase)

    def test_dashboard_user_inherits_base(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        assert issubclass(DashboardUser, DeclarativeBase)


class TestMetricsEvent:
    """MetricsEvent has the correct table name, columns, types, and indexes."""

    def test_tablename(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        assert MetricsEvent.__tablename__ == "metrics_events"

    def test_id_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["id"]
        assert isinstance(col.type, Integer)
        assert col.primary_key is True
        assert col.autoincrement is True

    def test_event_type_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["event_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is False

    def test_conversation_id_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["conversation_id"]
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False

    def test_generation_id_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["generation_id"]
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False

    def test_model_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["model"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False

    def test_user_email_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["user_email"]
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False

    def test_status_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["status"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is False

    def test_duration_ms_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["duration_ms"]
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_loop_count_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["loop_count"]
        assert isinstance(col.type, Integer)
        assert col.nullable is True

    def test_cursor_version_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["cursor_version"]
        assert isinstance(col.type, String)
        assert col.type.length == 50
        assert col.nullable is True

    def test_timestamp_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["timestamp"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is False

    def test_created_at_column(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["created_at"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is False
        assert col.server_default is not None

    def test_id_is_bigint(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        col = MetricsEvent.__table__.columns["id"]
        from sqlalchemy import BigInteger

        assert isinstance(col.type, BigInteger)

    def test_index_user_email_timestamp(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        index_names = {idx.name for idx in MetricsEvent.__table__.indexes}
        assert "ix_metrics_events_user_email_timestamp" in index_names

    def test_index_model_timestamp(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        index_names = {idx.name for idx in MetricsEvent.__table__.indexes}
        assert "ix_metrics_events_model_timestamp" in index_names

    def test_index_conversation_id(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        index_names = {idx.name for idx in MetricsEvent.__table__.indexes}
        assert "ix_metrics_events_conversation_id" in index_names

    def test_index_user_email_timestamp_columns(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        idx = next(
            i for i in MetricsEvent.__table__.indexes if i.name == "ix_metrics_events_user_email_timestamp"
        )
        col_names = [c.name for c in idx.columns]
        assert col_names == ["user_email", "timestamp"]

    def test_index_model_timestamp_columns(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        idx = next(
            i for i in MetricsEvent.__table__.indexes if i.name == "ix_metrics_events_model_timestamp"
        )
        col_names = [c.name for c in idx.columns]
        assert col_names == ["model", "timestamp"]

    def test_index_conversation_id_columns(self) -> None:
        from cursor_metrics.models.db import MetricsEvent

        idx = next(
            i for i in MetricsEvent.__table__.indexes if i.name == "ix_metrics_events_conversation_id"
        )
        col_names = [c.name for c in idx.columns]
        assert col_names == ["conversation_id"]


class TestModelPricing:
    """ModelPricing has the correct table name, columns, types, and constraints."""

    def test_tablename(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        assert ModelPricing.__tablename__ == "model_pricing"

    def test_id_column(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        col = ModelPricing.__table__.columns["id"]
        assert isinstance(col.type, Integer)
        assert col.primary_key is True
        assert col.autoincrement is True

    def test_model_column(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        col = ModelPricing.__table__.columns["model"]
        assert isinstance(col.type, String)
        assert col.type.length == 100
        assert col.nullable is False
        assert col.unique is True

    def test_cost_per_input_token_column(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        col = ModelPricing.__table__.columns["cost_per_input_token"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 12
        assert col.type.scale == 8
        assert col.nullable is False

    def test_cost_per_output_token_column(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        col = ModelPricing.__table__.columns["cost_per_output_token"]
        assert isinstance(col.type, Numeric)
        assert col.type.precision == 12
        assert col.type.scale == 8
        assert col.nullable is False

    def test_updated_at_column(self) -> None:
        from cursor_metrics.models.db import ModelPricing

        col = ModelPricing.__table__.columns["updated_at"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is False
        assert col.server_default is not None


class TestDashboardUser:
    """DashboardUser has the correct table name, columns, types, and constraints."""

    def test_tablename(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        assert DashboardUser.__tablename__ == "dashboard_users"

    def test_id_column(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        col = DashboardUser.__table__.columns["id"]
        assert isinstance(col.type, Integer)
        assert col.primary_key is True
        assert col.autoincrement is True

    def test_email_column(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        col = DashboardUser.__table__.columns["email"]
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False
        assert col.unique is True

    def test_password_hash_column(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        col = DashboardUser.__table__.columns["password_hash"]
        assert isinstance(col.type, String)
        assert col.type.length == 255
        assert col.nullable is False

    def test_created_at_column(self) -> None:
        from cursor_metrics.models.db import DashboardUser

        col = DashboardUser.__table__.columns["created_at"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is False
        assert col.server_default is not None
