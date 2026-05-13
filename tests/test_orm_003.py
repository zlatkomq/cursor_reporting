"""Tests for SPEC-003 ORM model additions."""

from cursor_metrics.models.db import MetricsEvent, ModelPricing


class TestMetricsEventNewColumns:
    """MetricsEvent should have all 8 new attributes from SPEC-003."""

    def test_input_tokens(self):
        e = MetricsEvent()
        assert hasattr(e, "input_tokens")

    def test_output_tokens(self):
        e = MetricsEvent()
        assert hasattr(e, "output_tokens")

    def test_cache_read_tokens(self):
        e = MetricsEvent()
        assert hasattr(e, "cache_read_tokens")

    def test_cache_write_tokens(self):
        e = MetricsEvent()
        assert hasattr(e, "cache_write_tokens")

    def test_session_id(self):
        e = MetricsEvent()
        assert hasattr(e, "session_id")

    def test_workspace(self):
        e = MetricsEvent()
        assert hasattr(e, "workspace")

    def test_command_name(self):
        e = MetricsEvent()
        assert hasattr(e, "command_name")

    def test_skill_name(self):
        e = MetricsEvent()
        assert hasattr(e, "skill_name")


class TestModelPricingNewColumn:
    """ModelPricing should have cost_per_cache_read_token."""

    def test_cost_per_cache_read_token(self):
        p = ModelPricing()
        assert hasattr(p, "cost_per_cache_read_token")


class TestMetricsEventIndexes:
    """MetricsEvent should include the two new indexes."""

    def test_session_id_index(self):
        index_names = [idx.name for idx in MetricsEvent.__table_args__ if hasattr(idx, "name")]
        assert "ix_metrics_events_session_id" in index_names

    def test_workspace_index(self):
        index_names = [idx.name for idx in MetricsEvent.__table_args__ if hasattr(idx, "name")]
        assert "ix_metrics_events_workspace" in index_names
