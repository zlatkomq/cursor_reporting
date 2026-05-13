"""Add subagent_type column to metrics_events.

Revision ID: 003
Revises: 002
Create Date: 2026-05-13

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import sqlalchemy as sa

from alembic import op

if TYPE_CHECKING:
    from collections.abc import Sequence

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("metrics_events", sa.Column("subagent_type", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("metrics_events", "subagent_type")
