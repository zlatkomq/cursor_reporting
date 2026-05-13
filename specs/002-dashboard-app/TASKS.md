# Task Breakdown

## Metadata

| Field | Value |
|-------|-------|
| ID | 002 |
| Name | Dashboard Application |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-12 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-12 |
| Jira Ticket | |

---

## Overview

Implement the full dashboard application per DESIGN-002: authentication layer first, then service/repository logic, then API endpoints, then templates/UI, and finally the CLI tool and integration tests. Tasks are ordered so each builds on the previous.

---

## Tasks

### Phase 1: Dependencies & Configuration

- [ ] T1: Add auth dependencies and config settings
  - Modify: `pyproject.toml`, `src/cursor_metrics/config.py`, `.env.example`
  - Produces: `python-jose[cryptography]` and `passlib[bcrypt]` in dependencies; `JWT_SECRET_KEY` and `JWT_EXPIRE_MINUTES` fields in Settings; updated `.env.example`
  - Verify: `uv sync` succeeds; `uv run pytest` passes (no regressions)

### Phase 2: Auth Layer

- [ ] T2: Create UserRepository
  - Create: `src/cursor_metrics/repositories/user_repo.py`
  - Modify: `src/cursor_metrics/repositories/__init__.py`
  - Create: `tests/test_user_repo.py`
  - Consumes: T1 (dependencies available)
  - Produces: `UserRepository` class with `get_by_email()` and `create()` methods
  - Verify: `uv run pytest tests/test_user_repo.py -v` → PASS

- [ ] T3: Create AuthService
  - Create: `src/cursor_metrics/services/auth_service.py`
  - Modify: `src/cursor_metrics/services/__init__.py`
  - Create: `tests/test_auth_service.py`
  - Consumes: T1 (JWT/passlib deps), T2 (UserRepository)
  - Produces: `AuthService` class with `authenticate()`, `create_token()`, `verify_token()`, `hash_password()`, `verify_password()`
  - Verify: `uv run pytest tests/test_auth_service.py -v` → PASS

- [ ] T4: Create auth dependency and middleware
  - Create: `src/cursor_metrics/dependencies.py`
  - Create: `tests/test_dependencies.py`
  - Consumes: T3 (AuthService)
  - Produces: `get_current_user()` dependency that reads JWT from cookie or Authorization header; redirects to login for HTML requests, returns 401 for API requests
  - Verify: `uv run pytest tests/test_dependencies.py -v` → PASS

### Phase 3: Repository & Service Implementation

- [ ] T5: Implement MetricsRepository queries
  - Modify: `src/cursor_metrics/repositories/metrics_repo.py`
  - Create: `tests/test_metrics_repo.py`
  - Consumes: existing `MetricsEvent` ORM model
  - Produces: `count_events()`, `count_active_developers()`, `top_model()`, `daily_event_counts()`, `events_by_developer()`, `events_by_model()` — all with `since: datetime` parameter
  - Verify: `uv run pytest tests/test_metrics_repo.py -v` → PASS

- [ ] T6: Implement PricingService
  - Modify: `src/cursor_metrics/services/pricing_service.py`
  - Create: `tests/test_pricing_service.py`
  - Consumes: existing `ModelPricing` ORM model
  - Produces: `get_pricing_map()` and `estimate_cost()` methods
  - Verify: `uv run pytest tests/test_pricing_service.py -v` → PASS

- [ ] T7: Implement MetricsService aggregation logic
  - Modify: `src/cursor_metrics/services/metrics_service.py`
  - Create: `tests/test_metrics_service.py`
  - Consumes: T5 (MetricsRepository), T6 (PricingService)
  - Produces: `get_overview(days)`, `get_by_developer(days)`, `get_by_model(days)` methods returning structured dicts
  - Verify: `uv run pytest tests/test_metrics_service.py -v` → PASS

### Phase 4: API Endpoints

- [ ] T8: Implement auth router (login/logout)
  - Modify: `src/cursor_metrics/routers/auth.py`
  - Modify: `src/cursor_metrics/main.py` (register router)
  - Create: `tests/test_auth_router.py`
  - Consumes: T3 (AuthService), T4 (dependencies)
  - Produces: `POST /api/v1/auth/login` (JSON), `GET /dashboard/login`, `POST /dashboard/login` (form), `GET /dashboard/logout`
  - Verify: `uv run pytest tests/test_auth_router.py -v` → PASS

- [ ] T9: Implement reports API router
  - Modify: `src/cursor_metrics/routers/reports.py`
  - Modify: `src/cursor_metrics/main.py` (register router)
  - Create: `tests/test_reports_router.py`
  - Consumes: T4 (auth dependency), T7 (MetricsService)
  - Produces: `GET /api/v1/metrics`, `GET /api/v1/metrics/by-developer`, `GET /api/v1/metrics/by-model` — all accept `?days=` query param, require auth
  - Verify: `uv run pytest tests/test_reports_router.py -v` → PASS

### Phase 5: Templates & Dashboard UI

- [ ] T10: Create base template with dark theme and sidebar
  - Modify: `src/cursor_metrics/templates/base.html`
  - Create: `src/cursor_metrics/templates/partials/sidebar.html`
  - Create: `src/cursor_metrics/templates/partials/date_filter.html`
  - Create: `tests/test_templates.py`
  - Produces: Dark theme CSS, sidebar nav (Overview, By Developer, By Model, Logout), HTMX + Chart.js CDN includes, date filter component
  - Verify: Templates render without error; `uv run pytest tests/test_templates.py -v` → PASS

- [ ] T11: Create login page template
  - Create: `src/cursor_metrics/templates/login.html`
  - Modify: `tests/test_auth_router.py` (add template rendering tests)
  - Consumes: T8 (auth router serves login), T10 (base template available)
  - Produces: Login form with email/password fields, error message display, dark theme styling
  - Verify: `GET /dashboard/login` returns rendered HTML; form submits correctly

- [ ] T12: Create dashboard overview page
  - Create: `src/cursor_metrics/templates/dashboard.html`
  - Create: `src/cursor_metrics/templates/partials/stat_cards.html`
  - Modify: `src/cursor_metrics/routers/dashboard.py`
  - Create: `tests/test_dashboard_router.py`
  - Consumes: T4 (auth dependency), T7 (MetricsService), T10 (base template + sidebar)
  - Produces: `GET /dashboard` page with 4 stat cards (Total Events, Active Developers, Top Model, Estimated Cost) and Chart.js daily events line chart
  - Verify: `uv run pytest tests/test_dashboard_router.py -v` → PASS

- [ ] T13: Create by-developer page
  - Create: `src/cursor_metrics/templates/by_developer.html`
  - Modify: `src/cursor_metrics/routers/dashboard.py`
  - Modify: `tests/test_dashboard_router.py`
  - Consumes: T7 (MetricsService.get_by_developer), T10 (base template)
  - Produces: `GET /dashboard/by-developer` page with ranked developer table
  - Verify: `uv run pytest tests/test_dashboard_router.py -v` → PASS

- [ ] T14: Create by-model page
  - Create: `src/cursor_metrics/templates/by_model.html`
  - Modify: `src/cursor_metrics/routers/dashboard.py`
  - Modify: `tests/test_dashboard_router.py`
  - Consumes: T7 (MetricsService.get_by_model), T10 (base template)
  - Produces: `GET /dashboard/by-model` page with model usage and cost table
  - Verify: `uv run pytest tests/test_dashboard_router.py -v` → PASS

### Phase 6: CLI & Finishing

- [ ] T15: Create CLI user management command
  - Create: `src/cursor_metrics/cli.py`, `src/cursor_metrics/__main__.py`
  - Create: `tests/test_cli.py`
  - Consumes: T2 (UserRepository), T3 (AuthService.hash_password)
  - Produces: `uv run python -m cursor_metrics.cli create-user --email X --password Y`
  - Verify: `uv run pytest tests/test_cli.py -v` → PASS

- [ ] T16: HTMX date filter integration
  - Modify: `src/cursor_metrics/routers/dashboard.py` (add partial endpoints)
  - Modify: dashboard templates (wire HTMX attributes)
  - Modify: `tests/test_dashboard_router.py`
  - Consumes: T10 (date_filter partial), T12-T14 (dashboard pages)
  - Produces: Clicking 7d/30d/90d triggers HTMX request, swaps stat cards and chart data without full page reload
  - Verify: `uv run pytest tests/test_dashboard_router.py -v` → PASS

- [ ] T17: Update Dockerfile and rebuild
  - Modify: `Dockerfile` (if new system deps needed for bcrypt)
  - Modify: `docker-compose.yml` (add JWT_SECRET_KEY to env)
  - Modify: `.env.example` (already done in T1, verify consistency)
  - Verify: `docker compose up --build -d` succeeds; `curl http://localhost:8000/dashboard/login` returns HTML

- [ ] T18: Verify linting, formatting, and full test suite
  - Verify: `uv run ruff check . && uv run ruff format --check .` → zero errors
  - Verify: `uv run pytest --tb=short -q` → all tests pass
  - Fix any lint/format issues found

---

## Testing

- [ ] T2: UserRepository unit tests (get_by_email, create)
- [ ] T3: AuthService unit tests (hash, verify, token create/decode, authenticate)
- [ ] T4: Auth dependency unit tests (valid cookie, invalid cookie, missing cookie, API bearer token)
- [ ] T5: MetricsRepository unit tests (all 6 query methods with mock data)
- [ ] T6: PricingService unit tests (pricing map, cost estimation)
- [ ] T7: MetricsService unit tests (overview, by-developer, by-model with mocked repo)
- [ ] T8: Auth router tests (login form rendering, successful login, failed login, logout, API login)
- [ ] T9: Reports router tests (all 3 endpoints with auth, without auth → 401)
- [ ] T12-T14: Dashboard router tests (page rendering with auth, redirect without auth)
- [ ] T15: CLI tests (create user, duplicate email error)

---

## Previous Spec Learnings

From SPEC-001:
- Use `Iterator[None]` (not `Generator[None]`) for yielding fixture type hints
- Module-level autouse `_required_env` fixtures with `get_settings.cache_clear()` before/after
- `httpx.AsyncClient` + `ASGITransport` for FastAPI testing
- Leading underscore for autouse fixtures
- `from __future__ import annotations` + `TYPE_CHECKING` pattern
- OOP test classes with `-> None` on all methods
- Hatchling needs `[tool.hatch.build.targets.wheel] packages = ["src/cursor_metrics"]`

---

## References

- DESIGN-002 — Architecture diagram, service interfaces, template structure, auth flow
- SPEC-002 — Acceptance criteria, scope, visual design direction
- CONSTITUTION.md — Coding standards, file structure, API standards, patterns
- SPEC-001 IMPLEMENTATION-SUMMARY.md — Established patterns and decisions

---

## Definition of Done

- [ ] All tasks completed (T1–T18)
- [ ] All tests passing (`uv run pytest`)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Formatting clean (`uv run ruff format --check .`)
- [ ] Docker Compose stack starts and dashboard is accessible
- [ ] Login flow works end-to-end (create user via CLI → login → see dashboard)
- [ ] All 12 acceptance criteria verified
- [ ] No open questions remaining
