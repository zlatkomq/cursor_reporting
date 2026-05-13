"""Tests for Jinja2 templates — verifies existence, key elements, and renderability."""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "src" / "cursor_metrics" / "templates"


@pytest.fixture()
def jinja_env() -> Environment:
    """Return a Jinja2 environment pointed at the project templates directory."""
    return Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=True,
    )


class TestBaseTemplate:
    """Verify base.html exists and contains expected elements."""

    def test_file_exists(self) -> None:
        assert (TEMPLATES_DIR / "base.html").is_file()

    def test_contains_htmx_cdn(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "htmx.org" in content

    def test_contains_chartjs_cdn(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "chart.js" in content

    def test_contains_sidebar_include(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "partials/sidebar.html" in content

    def test_contains_content_block(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "{% block content %}" in content

    def test_contains_title_block(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "{% block title %}" in content

    def test_contains_scripts_block(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "{% block scripts %}" in content

    def test_contains_design_tokens(self) -> None:
        content = (TEMPLATES_DIR / "base.html").read_text()
        assert "--bg-primary" in content
        assert "--accent-blue" in content
        assert "--sidebar-width" in content

    def test_loadable_by_jinja(self, jinja_env: Environment) -> None:
        template = jinja_env.get_template("base.html")
        assert template is not None


class TestSidebarPartial:
    """Verify sidebar partial exists and contains nav links."""

    def test_file_exists(self) -> None:
        assert (TEMPLATES_DIR / "partials" / "sidebar.html").is_file()

    def test_contains_overview_link(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "sidebar.html").read_text()
        assert "/dashboard" in content
        assert "Overview" in content

    def test_contains_by_developer_link(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "sidebar.html").read_text()
        assert "/dashboard/by-developer" in content
        assert "By Developer" in content

    def test_contains_by_model_link(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "sidebar.html").read_text()
        assert "/dashboard/by-model" in content
        assert "By Model" in content

    def test_contains_logout_link(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "sidebar.html").read_text()
        assert "/dashboard/logout" in content
        assert "Logout" in content

    def test_contains_active_state_logic(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "sidebar.html").read_text()
        assert "request.url.path" in content

    def test_contains_project_name(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "sidebar.html").read_text()
        assert "Cursor Metrics" in content

    def test_loadable_by_jinja(self, jinja_env: Environment) -> None:
        template = jinja_env.get_template("partials/sidebar.html")
        assert template is not None


class TestLoginTemplate:
    """Verify login.html exists and contains expected elements."""

    def test_file_exists(self) -> None:
        assert (TEMPLATES_DIR / "login.html").is_file()

    def test_contains_form_with_email_input(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "<form" in content
        assert 'name="email"' in content

    def test_contains_form_with_password_input(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert 'name="password"' in content

    def test_form_action_points_to_login(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert 'action="/dashboard/login"' in content

    def test_contains_error_variable(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "{{ error }}" in content

    def test_contains_dark_theme_bg(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "#0a0a0f" in content

    def test_contains_sign_in_button(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "Sign In" in content

    def test_contains_cursor_metrics_heading(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "Cursor Metrics" in content

    def test_does_not_extend_base(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "{% extends" not in content

    def test_does_not_include_sidebar(self) -> None:
        content = (TEMPLATES_DIR / "login.html").read_text()
        assert "sidebar" not in content

    def test_loadable_by_jinja(self, jinja_env: Environment) -> None:
        template = jinja_env.get_template("login.html")
        assert template is not None

    def test_renders_without_error(self, jinja_env: Environment) -> None:
        template = jinja_env.get_template("login.html")
        rendered = template.render(error="")
        assert "Cursor Metrics" in rendered
        assert '<p class="error-message">' not in rendered

    def test_renders_with_error(self, jinja_env: Environment) -> None:
        template = jinja_env.get_template("login.html")
        rendered = template.render(error="Invalid email or password")
        assert "Invalid email or password" in rendered
        assert "error-message" in rendered


class TestDateFilterPartial:
    """Verify date filter partial exists and contains HTMX attributes."""

    def test_file_exists(self) -> None:
        assert (TEMPLATES_DIR / "partials" / "date_filter.html").is_file()

    def test_contains_htmx_get(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "date_filter.html").read_text()
        assert "hx-get" in content

    def test_contains_htmx_target(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "date_filter.html").read_text()
        assert "hx-target" in content

    def test_contains_htmx_swap(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "date_filter.html").read_text()
        assert "hx-swap" in content

    def test_contains_day_options(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "date_filter.html").read_text()
        assert "days=7" in content
        assert "days=30" in content
        assert "days=90" in content

    def test_contains_active_state_logic(self) -> None:
        content = (TEMPLATES_DIR / "partials" / "date_filter.html").read_text()
        assert "current_days" in content

    def test_loadable_by_jinja(self, jinja_env: Environment) -> None:
        template = jinja_env.get_template("partials/date_filter.html")
        assert template is not None
