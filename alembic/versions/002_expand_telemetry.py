"""Expand telemetry schema with token counts, session/workspace tracking, and cache pricing.

Revision ID: 002
Revises: 001
Create Date: 2026-05-13

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("metrics_events", sa.Column("input_tokens", sa.BigInteger, nullable=True))
    op.add_column("metrics_events", sa.Column("output_tokens", sa.BigInteger, nullable=True))
    op.add_column("metrics_events", sa.Column("cache_read_tokens", sa.BigInteger, nullable=True))
    op.add_column("metrics_events", sa.Column("cache_write_tokens", sa.BigInteger, nullable=True))
    op.add_column("metrics_events", sa.Column("session_id", sa.String(255), nullable=True))
    op.add_column("metrics_events", sa.Column("workspace", sa.String(500), nullable=True))
    op.add_column("metrics_events", sa.Column("command_name", sa.String(100), nullable=True))
    op.add_column("metrics_events", sa.Column("skill_name", sa.String(100), nullable=True))

    op.add_column(
        "model_pricing",
        sa.Column(
            "cost_per_cache_read_token",
            sa.Numeric(12, 8),
            nullable=False,
            server_default="0.00000000",
        ),
    )

    op.create_index("ix_metrics_events_session_id", "metrics_events", ["session_id"])
    op.create_index("ix_metrics_events_workspace", "metrics_events", ["workspace"])


def downgrade() -> None:
    op.drop_index("ix_metrics_events_workspace", table_name="metrics_events")
    op.drop_index("ix_metrics_events_session_id", table_name="metrics_events")

    op.drop_column("model_pricing", "cost_per_cache_read_token")

    op.drop_column("metrics_events", "skill_name")
    op.drop_column("metrics_events", "command_name")
    op.drop_column("metrics_events", "workspace")
    op.drop_column("metrics_events", "session_id")
    op.drop_column("metrics_events", "cache_write_tokens")
    op.drop_column("metrics_events", "cache_read_tokens")
    op.drop_column("metrics_events", "output_tokens")
    op.drop_column("metrics_events", "input_tokens")
