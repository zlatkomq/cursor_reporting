"""Tests for stub router placeholders — verifies importability and router instances."""

from __future__ import annotations

from fastapi import APIRouter


class TestReportsRouter:
    """Verify reports router module is importable and correctly configured."""

    def test_importable(self) -> None:
        from cursor_metrics.routers import reports

        assert reports is not None

    def test_router_is_api_router(self) -> None:
        from cursor_metrics.routers.reports import router

        assert isinstance(router, APIRouter)

    def test_router_prefix(self) -> None:
        from cursor_metrics.routers.reports import router

        assert router.prefix == "/api/v1"

    def test_router_has_reports_tag(self) -> None:
        from cursor_metrics.routers.reports import router

        assert "reports" in router.tags

    def test_router_has_no_routes(self) -> None:
        from cursor_metrics.routers.reports import router

        assert len(router.routes) == 0


class TestAuthRouter:
    """Verify auth router module is importable and correctly configured."""

    def test_importable(self) -> None:
        from cursor_metrics.routers import auth

        assert auth is not None

    def test_router_is_api_router(self) -> None:
        from cursor_metrics.routers.auth import router

        assert isinstance(router, APIRouter)

    def test_router_has_routes(self) -> None:
        from cursor_metrics.routers.auth import router

        assert len(router.routes) > 0


class TestDashboardRouter:
    """Verify dashboard router module is importable and correctly configured."""

    def test_importable(self) -> None:
        from cursor_metrics.routers import dashboard

        assert dashboard is not None

    def test_router_is_api_router(self) -> None:
        from cursor_metrics.routers.dashboard import router

        assert isinstance(router, APIRouter)

    def test_router_prefix(self) -> None:
        from cursor_metrics.routers.dashboard import router

        assert router.prefix == ""

    def test_router_has_dashboard_tag(self) -> None:
        from cursor_metrics.routers.dashboard import router

        assert "dashboard" in router.tags

    def test_router_has_no_routes(self) -> None:
        from cursor_metrics.routers.dashboard import router

        assert len(router.routes) == 0
