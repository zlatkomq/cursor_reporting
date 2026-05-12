"""Create metrics_events, model_pricing, and dashboard_users tables.

Revision ID: 001
Revises: None
Create Date: 2026-05-12

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "metrics_events",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("conversation_id", sa.String(255), nullable=False),
        sa.Column("generation_id", sa.String(255), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("user_email", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("loop_count", sa.Integer, nullable=True),
        sa.Column("cursor_version", sa.String(50), nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_metrics_events_user_email_timestamp", "metrics_events", ["user_email", "timestamp"])
    op.create_index("ix_metrics_events_model_timestamp", "metrics_events", ["model", "timestamp"])
    op.create_index("ix_metrics_events_conversation_id", "metrics_events", ["conversation_id"])

    op.create_table(
        "model_pricing",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("model", sa.String(100), nullable=False, unique=True),
        sa.Column("cost_per_input_token", sa.Numeric(12, 8), nullable=False),
        sa.Column("cost_per_output_token", sa.Numeric(12, 8), nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "dashboard_users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("dashboard_users")
    op.drop_table("model_pricing")
    op.drop_table("metrics_events")
