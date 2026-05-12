"""Tests for cursor_metrics.repositories — MetricsRepository stub."""

from __future__ import annotations

import inspect
from unittest.mock import MagicMock

from sqlalchemy.ext.asyncio import AsyncSession


class TestMetricsRepositoryImport:
    """Verify MetricsRepository is importable from multiple paths."""

    def test_import_from_module(self) -> None:
        from cursor_metrics.repositories.metrics_repo import MetricsRepository

        assert MetricsRepository is not None

    def test_import_from_package(self) -> None:
        from cursor_metrics.repositories import MetricsRepository

        assert MetricsRepository is not None

    def test_class_is_in_package_all(self) -> None:
        import cursor_metrics.repositories as pkg

        assert "MetricsRepository" in pkg.__all__


class TestMetricsRepositoryConstructor:
    """Verify MetricsRepository.__init__ accepts an AsyncSession."""

    def test_accepts_session_parameter(self) -> None:
        from cursor_metrics.repositories.metrics_repo import MetricsRepository

        sig = inspect.signature(MetricsRepository.__init__)
        params = list(sig.parameters.keys())
        assert "session" in params

    def test_session_annotated_as_async_session(self) -> None:
        from cursor_metrics.repositories.metrics_repo import MetricsRepository

        assert MetricsRepository.__init__.__annotations__["session"] == "AsyncSession"

    def test_instantiation_stores_session(self) -> None:
        from cursor_metrics.repositories.metrics_repo import MetricsRepository

        mock_session = MagicMock(spec=AsyncSession)
        repo = MetricsRepository(session=mock_session)
        assert repo._session is mock_session

    def test_has_docstring(self) -> None:
        from cursor_metrics.repositories.metrics_repo import MetricsRepository

        assert MetricsRepository.__doc__ is not None
        assert len(MetricsRepository.__doc__.strip()) > 0
