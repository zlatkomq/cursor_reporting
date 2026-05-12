"""Tests for cursor_metrics.services — MetricsService and PricingService stubs."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

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
