"""Tests for cursor_metrics.services — MetricsService and PricingService stubs."""

from __future__ import annotations

import inspect
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


class TestMetricsServiceImport:
    """Verify MetricsService is importable from multiple paths."""

    def test_import_from_module(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        assert MetricsService is not None

    def test_import_from_package(self) -> None:
        from cursor_metrics.services import MetricsService

        assert MetricsService is not None

    def test_class_is_in_package_all(self) -> None:
        import cursor_metrics.services as pkg

        assert "MetricsService" in pkg.__all__


class TestMetricsServiceConstructor:
    """Verify MetricsService.__init__ accepts a MetricsRepository."""

    def test_accepts_repository_parameter(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        sig = inspect.signature(MetricsService.__init__)
        params = list(sig.parameters.keys())
        assert "repository" in params

    def test_repository_annotated_as_metrics_repository(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        assert MetricsService.__init__.__annotations__["repository"] == "MetricsRepository"

    def test_instantiation_stores_repository(self) -> None:
        from cursor_metrics.repositories.metrics_repo import MetricsRepository
        from cursor_metrics.services.metrics_service import MetricsService
        from cursor_metrics.services.pricing_service import PricingService

        mock_repo = MagicMock(spec=MetricsRepository)
        mock_pricing = MagicMock(spec=PricingService)
        svc = MetricsService(repository=mock_repo, pricing_service=mock_pricing)
        assert svc._repository is mock_repo

    def test_has_docstring(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        assert MetricsService.__doc__ is not None
        assert len(MetricsService.__doc__.strip()) > 0


class TestPricingServiceImport:
    """Verify PricingService is importable from multiple paths."""

    def test_import_from_module(self) -> None:
        from cursor_metrics.services.pricing_service import PricingService

        assert PricingService is not None

    def test_import_from_package(self) -> None:
        from cursor_metrics.services import PricingService

        assert PricingService is not None

    def test_class_is_in_package_all(self) -> None:
        import cursor_metrics.services as pkg

        assert "PricingService" in pkg.__all__


class TestPricingServiceConstructor:
    """Verify PricingService.__init__ accepts an AsyncSession."""

    def test_accepts_session_parameter(self) -> None:
        from cursor_metrics.services.pricing_service import PricingService

        sig = inspect.signature(PricingService.__init__)
        params = list(sig.parameters.keys())
        assert "session" in params

    def test_session_annotated_as_async_session(self) -> None:
        from cursor_metrics.services.pricing_service import PricingService

        assert PricingService.__init__.__annotations__["session"] == "AsyncSession"

    def test_instantiation_stores_session(self) -> None:
        from cursor_metrics.services.pricing_service import PricingService

        mock_session = MagicMock(spec=AsyncSession)
        svc = PricingService(session=mock_session)
        assert svc._session is mock_session

    def test_has_docstring(self) -> None:
        from cursor_metrics.services.pricing_service import PricingService

        assert PricingService.__doc__ is not None
        assert len(PricingService.__doc__.strip()) > 0


# ---------------------------------------------------------------------------
# Fixtures and helpers for MetricsService async tests
# ---------------------------------------------------------------------------


def _make_mock_repo() -> MagicMock:
    """Create a mocked MetricsRepository with all async methods."""
    from cursor_metrics.repositories.metrics_repo import MetricsRepository

    repo = MagicMock(spec=MetricsRepository)
    repo.count_events = AsyncMock(return_value=100)
    repo.count_active_developers = AsyncMock(return_value=5)
    repo.top_model = AsyncMock(return_value="claude-sonnet-4-20250514")
    repo.daily_event_counts = AsyncMock(return_value=[])
    repo.events_by_model = AsyncMock(
        return_value=[
            {
                "model": "claude-sonnet-4-20250514",
                "event_count": 80,
                "developer_count": 4,
                "avg_duration_ms": 1200.0,
                "total_input_tokens": 5000,
                "total_output_tokens": 3000,
                "total_cache_read_tokens": 1000,
            },
            {
                "model": "gpt-4o",
                "event_count": 20,
                "developer_count": 2,
                "avg_duration_ms": 900.0,
                "total_input_tokens": 2000,
                "total_output_tokens": 1500,
                "total_cache_read_tokens": 500,
            },
        ]
    )
    repo.total_tokens = AsyncMock(
        return_value={
            "input_tokens": 7000,
            "output_tokens": 4500,
            "cache_read_tokens": 1500,
            "cache_write_tokens": 800,
        }
    )
    return repo


def _make_mock_pricing() -> MagicMock:
    """Create a mocked PricingService."""
    from cursor_metrics.services.pricing_service import PricingService

    pricing = MagicMock(spec=PricingService)
    pricing.estimate_cost = AsyncMock(return_value=Decimal("0.05"))
    return pricing


class TestGetOverviewIncludesTokenTotals:
    """Verify overview response contains aggregate token fields."""

    @pytest.mark.asyncio
    async def test_get_overview_includes_token_totals(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        repo = _make_mock_repo()
        pricing = _make_mock_pricing()
        svc = MetricsService(repository=repo, pricing_service=pricing)

        result = await svc.get_overview(days=30)

        assert result["total_input_tokens"] == 7000
        assert result["total_output_tokens"] == 4500
        assert result["total_cache_read_tokens"] == 1500
        assert result["total_cache_write_tokens"] == 800
        repo.total_tokens.assert_called_once()


class TestGetByModelPassesTokensToPricing:
    """Verify estimate_cost receives token parameters from model data."""

    @pytest.mark.asyncio
    async def test_get_by_model_passes_tokens_to_pricing(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        repo = _make_mock_repo()
        pricing = _make_mock_pricing()
        svc = MetricsService(repository=repo, pricing_service=pricing)

        await svc.get_by_model(days=30)

        calls = pricing.estimate_cost.call_args_list
        assert len(calls) == 2

        _, kwargs0 = calls[0]
        assert kwargs0["input_tokens"] == 5000
        assert kwargs0["output_tokens"] == 3000
        assert kwargs0["cache_read_tokens"] == 1000

        _, kwargs1 = calls[1]
        assert kwargs1["input_tokens"] == 2000
        assert kwargs1["output_tokens"] == 1500
        assert kwargs1["cache_read_tokens"] == 500


class TestGetByModelIncludesTokensInResponse:
    """Verify token counts appear in the enriched model dicts."""

    @pytest.mark.asyncio
    async def test_get_by_model_includes_tokens_in_response(self) -> None:
        from cursor_metrics.services.metrics_service import MetricsService

        repo = _make_mock_repo()
        pricing = _make_mock_pricing()
        svc = MetricsService(repository=repo, pricing_service=pricing)

        result = await svc.get_by_model(days=30)
        models = result["models"]

        assert models[0]["total_input_tokens"] == 5000
        assert models[0]["total_output_tokens"] == 3000
        assert models[0]["total_cache_read_tokens"] == 1000

        assert models[1]["total_input_tokens"] == 2000
        assert models[1]["total_output_tokens"] == 1500
        assert models[1]["total_cache_read_tokens"] == 500
