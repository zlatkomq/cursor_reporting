# Implementation Summary — SPEC-002: Dashboard Application

## Established Patterns (from SPEC-001)

- `Iterator[None]` for yielding fixture type hints
- Module-level autouse `_required_env` with `get_settings.cache_clear()`
- `httpx.AsyncClient` + `ASGITransport` for testing
- OOP test classes with `-> None`
- `from __future__ import annotations` + `TYPE_CHECKING`
- Leading underscore for autouse fixtures

---

## Task Log

### T1: Add auth dependencies and config settings
**Files:** modified: [pyproject.toml, src/cursor_metrics/config.py, .env.example, .env, tests/conftest.py, tests/test_config.py, uv.lock]
**Patterns:** extra="ignore" in SettingsConfigDict for Docker Compose vars; _env_file=None in required-field tests
**Decisions:** JWT_SECRET_KEY required (no default); JWT_EXPIRE_MINUTES default 1440 (24h)
**Deviations:** Fixed pre-existing extra fields rejection bug
**Implementer:** 0c6c7a8d-ff49-4469-a084-0509dd8e70df [2026-05-12 14:28]
**Review:** PASS (config-only task, regression guard 224/224)

### T2: Create UserRepository
**Files:** created: [src/cursor_metrics/repositories/user_repo.py, tests/test_user_repo.py], modified: [src/cursor_metrics/repositories/__init__.py]
**Patterns:** OOP repository with AsyncSession constructor; select().where() for queries; flush+refresh for create; re-export from __init__
**Decisions:** None
**Deviations:** None
**Implementer:** 6c5c6af8-513b-4fee-8f89-5a2f5e03e725 [2026-05-12 14:31]
**Review:** PASS (13 tests, follows established repository pattern)

### T3: Create AuthService
**Files:** created: [src/cursor_metrics/services/auth_service.py, tests/test_auth_service.py], modified: [src/cursor_metrics/services/__init__.py]
**Patterns:** OOP service with UserRepository constructor; bcrypt direct for hashing; jose.jwt HS256 for tokens; get_settings() for JWT config
**Decisions:** Used bcrypt directly instead of passlib — passlib 1.7.x incompatible with bcrypt 5.0.0 on Python 3.14
**Deviations:** passlib replaced by direct bcrypt (same API surface)
**Implementer:** 80e1ccc5-631c-4e42-b7c6-3184e04a660c [2026-05-12 14:34]
**Review:** PASS (17 tests covering hash, verify, token create/decode, authenticate)

### T4: Create auth dependency and middleware
**Files:** created: [src/cursor_metrics/dependencies.py, tests/test_dependencies.py]
**Patterns:** FastAPI Depends; cookie-first then Bearer fallback; _verify_jwt standalone helper reusing AuthService constants; 303 redirect for HTML, 401 for API
**Decisions:** Cookie takes priority over Bearer header; HTML detection via Accept header
**Deviations:** None
**Implementer:** 8df82263-09ad-4fc6-849e-e2956db98df6 [2026-05-12 14:36]
**Review:** PASS (7 tests covering all auth scenarios)

### T5: Implement MetricsRepository queries
**Files:** modified: [src/cursor_metrics/repositories/metrics_repo.py], created: [tests/test_metrics_repo.py]
**Patterns:** SQLAlchemy 2.x select() with func.count/distinct/avg/date/max; all methods take since: datetime; null-safe duration handling
**Implementer:** 9f3ca8e1-3a04-498d-98cd-64a3db43b21e [2026-05-12 14:38]
**Review:** PASS (14 tests)

### T6: Implement PricingService
**Files:** modified: [src/cursor_metrics/services/pricing_service.py], created: [tests/test_pricing_service.py]
**Patterns:** Pricing map dict from DB; placeholder cost formula event_count * (in+out) * 1000; Decimal(0) for unknown models
**Implementer:** 444ffbcd-78de-48c5-9f49-ee516ddacedf [2026-05-12 14:38]
**Review:** PASS (7 tests)

### T7: Implement MetricsService aggregation logic
**Files:** modified: [src/cursor_metrics/services/metrics_service.py], created: [tests/test_metrics_service.py]
**Patterns:** Orchestrates MetricsRepository + PricingService; date formatting for daily_counts; cost summed across models for overview
**Implementer:** 86493373-474d-4f8b-9d83-ccfdbe6a8b3d [2026-05-12 14:41]
**Review:** PASS (9 tests)

### T8: Implement auth router (login/logout)
**Files:** modified: [src/cursor_metrics/routers/auth.py, pyproject.toml, tests/test_stub_routers.py], created: [tests/test_auth_router.py]
**Patterns:** Form login sets HttpOnly session cookie; API login returns JSON token; Pydantic LoginRequest model; python-multipart added for form data
**Implementer:** 3681420d-4122-4c85-b5e9-379bb5f047e2 [2026-05-12 14:47]
**Review:** PASS (7 tests)

### T9: Implement reports API router
**Files:** modified: [src/cursor_metrics/routers/reports.py, src/cursor_metrics/main.py], created: [tests/test_reports_router.py]
**Patterns:** Literal[7,30,90] for days validation; get_current_user dependency on all endpoints; MetricsService constructed from session
**Implementer:** 2291d980-bc58-47a0-be6b-ea8100024e30 [2026-05-12 14:44]
**Review:** PASS (15 tests)

### T10: Create base template with dark theme and sidebar
**Files:** modified: [src/cursor_metrics/templates/base.html], created: [src/cursor_metrics/templates/partials/sidebar.html, src/cursor_metrics/templates/partials/date_filter.html, tests/test_templates.py]
**Patterns:** CSS custom properties for design tokens; SVG icons in sidebar; active-state via request.url.path; HTMX 2.0.4 + Chart.js 4.4.7 CDN; Jinja2 blocks (title, content, scripts)
**Implementer:** f3620856-c89b-421d-bdc8-1765ccd7dbc9 [2026-05-12 14:50]
**Review:** PASS (24 tests)

### T11: Create login page template
**Files:** created: [src/cursor_metrics/templates/login.html], modified: [src/cursor_metrics/routers/auth.py, tests/test_templates.py]
**Patterns:** Standalone page (no base.html extend, no sidebar); Jinja2Templates in router; centered login card
**Implementer:** 7d4bed2d-7e09-445f-b2cb-03452f491de2 [2026-05-12 14:53]
**Review:** PASS (13 template tests + 7 router tests)

### T12: Create dashboard overview page
**Files:** created: [src/cursor_metrics/templates/dashboard.html, src/cursor_metrics/templates/partials/stat_cards.html], modified: [src/cursor_metrics/routers/dashboard.py, tests/test_dashboard_router.py]
**Patterns:** Extends base.html; 4 stat cards; Chart.js line chart with tojson filter; fixed Starlette 1.0 TemplateResponse API
**Implementer:** ee1ca2c7-c37a-4c69-b304-cd56b3e59c7f [2026-05-12 14:56]
**Review:** PASS (7 new tests, 12 total dashboard tests)

### T13: Create by-developer page
**Files:** created: [src/cursor_metrics/templates/by_developer.html]
**Patterns:** Extends base.html; ranked table with duration formatting; empty state message
**Implementer:** a320fddd-ea01-41aa-a0c0-b937a763b330 [2026-05-12 14:57]
**Review:** PASS (3 tests)

### T14: Create by-model page
**Files:** created: [src/cursor_metrics/templates/by_model.html], modified: [src/cursor_metrics/routers/dashboard.py, src/cursor_metrics/main.py, tests/test_dashboard_router.py]
**Patterns:** Extends base.html; cost formatted with $ and 2 decimals; developer count column
**Implementer:** 46be9026-5da2-419c-8740-e9c0fac22af2 [2026-05-12 14:55]
**Review:** PASS (2 tests)

### T15: Create CLI user management command
**Files:** created: [src/cursor_metrics/cli.py, src/cursor_metrics/__main__.py, tests/test_cli.py]
**Patterns:** argparse subcommands; async create_user with IntegrityError handling; dual invocation via __main__.py
**Implementer:** 90792dd1-f4be-4d7f-81eb-e948f10f29c6 [2026-05-12 15:01]
**Review:** PASS (8 tests)

### T16: HTMX date filter integration
**Files:** created: [partials/dashboard_content.html, partials/by_developer_content.html, partials/by_model_content.html], modified: [routers/dashboard.py, templates/*.html, partials/date_filter.html, tests/test_dashboard_router.py]
**Patterns:** _is_htmx() helper; HX-Request header detection; partial vs full template; hx-push-url for URL state
**Implementer:** 44720f93-7f7a-4808-b379-516b668aa00f [2026-05-12 15:00]
**Review:** PASS (19 tests, 7 new HTMX-specific)

### T17: Update Dockerfile and rebuild
**Files:** modified: [Dockerfile, docker-compose.yml]
**Patterns:** gcc + libffi-dev for bcrypt build; db port remapped 3307:3306
**Implementer:** 5ae0904b-908c-4ddf-9d64-340b18e93c32 [2026-05-12 15:03]
**Review:** PASS (docker build + curl verified)

### T18: Verify linting, formatting, and full test suite
**Files:** modified: 18 files (lint fixes, format fixes, stale test updates)
**Patterns:** Fixed 20 lint errors, 8 format issues, 4 test failures; datetime.UTC migration
**Implementer:** a351a0d5-c692-4d9d-be4c-3fd672dcef64 [2026-05-12 15:07]
**Review:** PASS (375 tests, 0 lint errors, 0 format issues)
