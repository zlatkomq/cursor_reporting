"""ORM table definitions for metrics_events, model_pricing, and dashboard_users."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from decimal import Decimal  # noqa: TC003

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from cursor_metrics.database import Base


class MetricsEvent(Base):
    """Stores individual telemetry events from the Cursor IDE."""

    __tablename__ = "metrics_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    generation_id: Mapped[str] = mapped_column(String(255), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    user_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loop_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cursor_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cache_read_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cache_write_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workspace: Mapped[str | None] = mapped_column(String(500), nullable=True)
    command_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    skill_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subagent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_metrics_events_user_email_timestamp", "user_email", "timestamp"),
        Index("ix_metrics_events_model_timestamp", "model", "timestamp"),
        Index("ix_metrics_events_conversation_id", "conversation_id"),
        Index("ix_metrics_events_session_id", "session_id"),
        Index("ix_metrics_events_workspace", "workspace"),
    )


class ModelPricing(Base):
    """Per-model token pricing used for cost estimation."""

    __tablename__ = "model_pricing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    cost_per_input_token: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    cost_per_output_token: Mapped[Decimal] = mapped_column(Numeric(12, 8), nullable=False)
    cost_per_cache_read_token: Mapped[Decimal] = mapped_column(
        Numeric(12, 8), nullable=False, server_default=text("0.00000000")
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())


class DashboardUser(Base):
    """Authenticated users of the metrics dashboard."""

    __tablename__ = "dashboard_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
