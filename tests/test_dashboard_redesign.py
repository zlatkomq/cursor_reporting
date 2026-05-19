"""Integration and visual smoke tests for the redesigned dashboard (spec 005)."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from jinja2 import pass_context
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from cursor_metrics.database import Base
from cursor_metrics.models.db import WorkflowProject

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator


@pytest.fixture(autouse=True)
def _required_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from cursor_metrics.config import get_settings

    get_settings.cache_clear()
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-abc123")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-jwt-secret-key")
    yield
    get_settings.cache_clear()


_test_engine = create_async_engine("sqlite+aiosqlite:///:memory:")
_TestSession = async_sessionmaker(bind=_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def _setup_db() -> AsyncIterator[None]:
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _TestSession() as session:
        now = datetime.utcnow()
        projects = [
            WorkflowProject(
                spec_id="SPEC-001",
                name="Auth module",
                stage="spec",
                status="in-progress",
                entered_stage_at=now - timedelta(days=3),
            ),
            WorkflowProject(
                spec_id="SPEC-002",
                name="Dashboard redesign",
                stage="design",
                status="draft",
                entered_stage_at=now - timedelta(days=5),
            ),
            WorkflowProject(
                spec_id="SPEC-003",
                name="API v2",
                stage="implement",
                status="in-progress",
                entered_stage_at=now - timedelta(days=1),
            ),
        ]
        session.add_all(projects)
        await session.commit()
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def _override_get_db() -> AsyncIterator[AsyncSession]:
    async with _TestSession() as session:
        yield session


async def _override_get_current_user() -> str:
    return "test@example.com"


def _patch_jinja_env() -> None:
    """Fix Jinja2 environment for test rendering.

    1. ``url_for('static', filename=…)`` → rewrite ``filename`` to ``path``
       (Starlette StaticFiles expects ``path``; templates use Django-style ``filename``).
    2. Override the ``format`` filter so new-style format strings (``{:,}``) work
       alongside old-style (``%.1f``).
    """
    from cursor_metrics.routers.dashboard import templates as dash_templates

    @pass_context
    def _url_for(context: dict, name: str, /, **path_params: str) -> str:  # type: ignore[type-arg]
        if name == "static" and "filename" in path_params:
            path_params["path"] = path_params.pop("filename")
        request = context["request"]
        return str(request.url_for(name, **path_params))

    def _format_filter(value: str, *args: object, **kwargs: object) -> str:
        if "{" in value:
            return value.format(*args, **kwargs)
        if args:
            return value % args  # type: ignore[arg-type]
        if kwargs:
            return value % kwargs
        return value

    dash_templates.env.globals["url_for"] = _url_for
    dash_templates.env.filters["format"] = _format_filter


@pytest.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    from cursor_metrics.database import get_db
    from cursor_metrics.dependencies import get_current_user
    from cursor_metrics.main import app

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    _patch_jinja_env()
    try:
        with patch("cursor_metrics.main.async_engine", _test_engine):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------------
# T20: Integration tests for dashboard tab routing
# ---------------------------------------------------------------------------


class TestDashboardRouting:
    """Integration tests for the new dashboard routes."""

    async def test_dashboard_default_returns_overview(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard")
        assert resp.status_code == 200
        body = resp.text
        assert "Overview" in body
        assert "Total Tokens" in body

    async def test_dashboard_funnel_tab(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard?tab=funnel")
        assert resp.status_code == 200
        assert "Workflow Funnel" in resp.text

    async def test_dashboard_htmx_overview(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/overview", headers={"HX-Request": "true"})
        assert resp.status_code == 200
        body = resp.text
        assert "Total Tokens" in body or "overview-metric" in body
        assert "<html" not in body

    async def test_dashboard_htmx_funnel(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/funnel", headers={"HX-Request": "true"})
        assert resp.status_code == 200
        assert "Workflow Funnel" in resp.text or "funnel" in resp.text

    async def test_dashboard_funnel_projects(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/funnel-projects?stage=spec")
        assert resp.status_code == 200
        assert "Recent Projects" in resp.text

    async def test_redirect_by_model(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/by-model", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["location"] == "/dashboard"

    async def test_redirect_by_developer(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/by-developer", follow_redirects=False)
        assert resp.status_code == 302

    async def test_redirect_by_command(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/by-command", follow_redirects=False)
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# T21: Visual smoke tests
# ---------------------------------------------------------------------------


class TestVisualSmoke:
    """Visual smoke tests verifying expected content in rendered pages."""

    async def test_overview_contains_metric_cards(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard")
        body = resp.text
        for label in ("Total Tokens", "Total Cost", "Avg Response Time", "API Requests"):
            assert label in body, f"Missing metric card: {label}"

    async def test_funnel_contains_all_stages(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard?tab=funnel")
        body = resp.text
        for stage in ("Spec", "Design", "Uix", "Tasks", "Implement", "Review"):
            assert stage in body, f"Missing funnel stage: {stage}"

    async def test_funnel_projects_contains_header(self, client: AsyncClient) -> None:
        resp = await client.get("/dashboard/funnel-projects?stage=spec")
        assert "Recent Projects in" in resp.text

    async def test_base_template_has_design_tokens(self) -> None:
        base_path = Path(__file__).resolve().parent.parent / "src" / "cursor_metrics" / "templates" / "base.html"
        content = base_path.read_text()
        assert "--color-bg-primary" in content
        assert "--color-border" in content
