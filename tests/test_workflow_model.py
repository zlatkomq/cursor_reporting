"""Tests for the WorkflowProject ORM model."""

from __future__ import annotations

import pytest

from cursor_metrics.models import WorkflowProject
from cursor_metrics.models.db import Base


class TestWorkflowProjectSchema:
    """Verify WorkflowProject table structure, columns, and indexes."""

    def test_tablename(self) -> None:
        assert WorkflowProject.__tablename__ == "workflow_projects"

    def test_inherits_base(self) -> None:
        assert issubclass(WorkflowProject, Base)

    @pytest.mark.parametrize(
        ("col_name", "col_type", "nullable"),
        [
            ("id", "INTEGER", False),
            ("spec_id", "VARCHAR(20)", False),
            ("name", "VARCHAR(255)", False),
            ("stage", "VARCHAR(50)", False),
            ("status", "VARCHAR(50)", False),
            ("entered_stage_at", "DATETIME", False),
            ("created_at", "DATETIME", False),
            ("updated_at", "DATETIME", False),
        ],
    )
    def test_column_exists_and_type(self, col_name: str, col_type: str, nullable: bool) -> None:
        table = WorkflowProject.__table__
        col = table.c[col_name]
        assert str(col.type) == col_type
        assert col.nullable is nullable

    def test_id_is_primary_key_autoincrement(self) -> None:
        col = WorkflowProject.__table__.c["id"]
        assert col.primary_key
        assert col.autoincrement

    def test_spec_id_is_unique(self) -> None:
        col = WorkflowProject.__table__.c["spec_id"]
        assert col.unique

    def test_created_at_has_server_default(self) -> None:
        col = WorkflowProject.__table__.c["created_at"]
        assert col.server_default is not None

    def test_updated_at_has_server_default(self) -> None:
        col = WorkflowProject.__table__.c["updated_at"]
        assert col.server_default is not None

    def test_index_on_stage(self) -> None:
        indexes = {idx.name for idx in WorkflowProject.__table__.indexes}
        assert "ix_workflow_projects_stage" in indexes

    def test_index_on_status(self) -> None:
        indexes = {idx.name for idx in WorkflowProject.__table__.indexes}
        assert "ix_workflow_projects_status" in indexes

    def test_reexported_from_models_package(self) -> None:
        from cursor_metrics import models

        assert hasattr(models, "WorkflowProject")
        assert models.WorkflowProject is WorkflowProject
