# Task Breakdown

## Metadata

| Field | Value |
|-------|-------|
| ID | 005 |
| Name | Dashboard Redesign — Two-Tab Layout with Workflow Funnel |
| Status | APPROVED |
| Author | Developer / AI-assisted |
| Date | 2026-05-15 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-15 |
| Jira Ticket | |

---

## Overview

Restructure the dashboard from four pages into a single two-tab page (Overview + Workflow Funnel) per DESIGN.md. Implementation proceeds bottom-up: data model → repository → service → router → templates. Old templates are archived to `.OLD/`. See DESIGN.md for full architecture, data model, and service method signatures.

---

## Tasks

### Data Layer

- [ ] T1: Add `WorkflowProject` ORM model to `src/cursor_metrics/models/db.py` (DESIGN: Data Model)
  - Create: fields `id`, `spec_id` (unique), `name`, `stage`, `status`, `entered_stage_at`, `created_at`, `updated_at` per DESIGN.md column definitions
  - Create: indexes `ix_workflow_projects_stage`, `ix_workflow_projects_status`
  - Produces: `WorkflowProject` ORM class
  - Verify: `uv run python -c "from cursor_metrics.models.db import WorkflowProject; print(WorkflowProject.__tablename__)"` → Expected: `workflow_projects`

- [ ] T2: Create `src/cursor_metrics/repositories/workflow_repo.py` (DESIGN: Architecture — WorkflowRepository)
  - Create: `src/cursor_metrics/repositories/workflow_repo.py`
  - Modify: `src/cursor_metrics/repositories/__init__.py` — re-export `WorkflowRepository`
  - Methods: `count_by_stage()` → list of (stage, count) pairs; `projects_by_stage(stage)` → list of `WorkflowProject` rows; `count_blocked()` → int; `avg_time_in_stage(stage)` → float|None; `count_active_in_stage(stage)` → int; `total_projects()` → int
  - Produces: `WorkflowRepository.count_by_stage() -> list[tuple[str, int]]`, `WorkflowRepository.projects_by_stage(stage: str) -> list[WorkflowProject]`, `WorkflowRepository.count_blocked() -> int`, `WorkflowRepository.avg_time_in_stage(stage: str) -> float | None`, `WorkflowRepository.count_active_in_stage(stage: str) -> int`, `WorkflowRepository.total_projects() -> int`
  - Verify: `uv run python -c "from cursor_metrics.repositories.workflow_repo import WorkflowRepository; print('OK')"` → Expected: OK

- [ ] T3: Add `recent_events()` and `daily_token_counts()` to `src/cursor_metrics/repositories/metrics_repo.py` (DESIGN: Architecture — MetricsRepository)
  - Modify: `src/cursor_metrics/repositories/metrics_repo.py`
  - `recent_events(since, limit=20)` → list of dicts with `timestamp`, `model`, `total_tokens`, `cost_usd`, `duration_ms`; joins `model_pricing` for per-event cost
  - `daily_token_counts(since)` → list of (date, token_sum) ordered ascending
  - Produces: `MetricsRepository.recent_events(since: datetime, limit: int) -> list[dict]`, `MetricsRepository.daily_token_counts(since: datetime) -> list[tuple[date, int]]`
  - Verify: `uv run python -c "from cursor_metrics.repositories.metrics_repo import MetricsRepository; print('OK')"` → Expected: OK

### Service Layer

- [ ] T4: Create `src/cursor_metrics/services/workflow_service.py` (DESIGN: Architecture — WorkflowService)
  - Create: `src/cursor_metrics/services/workflow_service.py`
  - Modify: `src/cursor_metrics/services/__init__.py` — re-export `WorkflowService`
  - OOP class with `WorkflowRepository` constructor injection
  - `get_funnel_summary()` → dict with `stages` (6 stages: spec, design, uix, tasks, implement, review), `total_projects`, `conversion_rate_pct`, `active_in_stage`, `avg_time_in_stage_days`, `blocked_count` per DESIGN.md signature
  - `get_projects_by_stage(stage)` → list of dicts with `spec_id`, `name`, `status`, `time_in_stage_days`
  - Stage ordering: `["spec", "design", "uix", "tasks", "implement", "review"]`
  - Funnel logic: each stage count = projects that have reached or passed that stage; drop_off = previous count − current count; percentage = count / first stage count × 100
  - Consumes: T2.WorkflowRepository
  - Produces: `WorkflowService.get_funnel_summary() -> dict`, `WorkflowService.get_projects_by_stage(stage: str) -> list[dict]`
  - Verify: `uv run python -c "from cursor_metrics.services.workflow_service import WorkflowService; print('OK')"` → Expected: OK

- [ ] T5: Add `get_overview_with_trends()` to `src/cursor_metrics/services/metrics_service.py` (DESIGN: Architecture — MetricsService)
  - Modify: `src/cursor_metrics/services/metrics_service.py`
  - New method queries current period and prior period (same length), computes trend percentages for total_tokens, total_cost, avg_duration, total_events
  - Returns dict per DESIGN.md `get_overview_with_trends` signature including `daily_token_counts`, `model_distribution`, `recent_events`
  - Display "—" (None) for trends when prior period has < 1 event
  - Consumes: T3.MetricsRepository (recent_events, daily_token_counts)
  - Produces: `MetricsService.get_overview_with_trends(days: int) -> dict`
  - Verify: `uv run python -c "from cursor_metrics.services.metrics_service import MetricsService; print('OK')"` → Expected: OK

### Static Assets

- [ ] T6: Mount static files and copy SVG icons (DESIGN: Architecture — static/icons)
  - Create: `src/cursor_metrics/static/icons/` directory
  - Copy SVG icons from `specs/005-dashboard-redesign/assets/icons/overview/` and `specs/005-dashboard-redesign/assets/icons/funnel/` into `src/cursor_metrics/static/icons/`
  - Modify: `src/cursor_metrics/main.py` — mount `StaticFiles(directory=...)` at `/static`
  - Verify: `uv run python -c "from pathlib import Path; d = Path('src/cursor_metrics/static/icons'); print(len(list(d.glob('*.svg'))), 'icons')"` → Expected: 26 icons

### Template Layer

- [ ] T7: Archive old templates to `templates/.OLD/` (DESIGN: Architecture — templates/.OLD)
  - Create: `src/cursor_metrics/templates/.OLD/`
  - Move: `by_model.html`, `by_developer.html`, `by_command.html` → `.OLD/`
  - Move: `partials/by_model_content.html`, `partials/by_developer_content.html`, `partials/by_command_content.html`, `partials/stat_cards.html`, `partials/dashboard_content.html` → `.OLD/`
  - Verify: `ls src/cursor_metrics/templates/.OLD/*.html | wc -l` → Expected: 8

- [ ] T8: Update `src/cursor_metrics/templates/base.html` with Figma design tokens (DESIGN: Architecture — base.html)
  - Modify: `src/cursor_metrics/templates/base.html`
  - Replace CSS `:root` variables with Figma design tokens from `specs/005-dashboard-redesign/assets/design-tokens.css`
  - Add Google Fonts import for Arimo; Inter and Liberation Mono fallbacks
  - Update `font-family` to use Arimo as primary
  - Keep existing layout structure (sidebar + main), responsive media query
  - Verify: `rg 'color-bg-primary' src/cursor_metrics/templates/base.html` → Expected: match found

- [ ] T9: Update `src/cursor_metrics/templates/partials/sidebar.html` — simplify nav (DESIGN: Architecture — sidebar.html)
  - Modify: `src/cursor_metrics/templates/partials/sidebar.html`
  - Remove nav links for By Developer, By Model, By Command
  - Keep Overview link only
  - Verify: `rg 'by-developer' src/cursor_metrics/templates/partials/sidebar.html` → Expected: no match

- [ ] T10: Rebuild `src/cursor_metrics/templates/dashboard.html` with tab bar (DESIGN: Architecture — dashboard.html)
  - Modify: `src/cursor_metrics/templates/dashboard.html`
  - New structure: page header with "AI Usage Dashboard" title (24px bold), subtitle, two tab buttons (Overview active by default, Workflow Funnel) with SVG icons from `/static/icons/`
  - Tab buttons use `hx-get="/dashboard?tab=overview"` / `hx-get="/dashboard?tab=funnel"`, `hx-target="#tab-content"`, `hx-swap="innerHTML"`, `hx-push-url="true"`
  - Active tab: bg `#fafafa`, text `#171717`; inactive: bg `#262626`, text `#a1a1a1`
  - `#tab-content` div includes the active tab's partial
  - Verify: `rg 'tab-content' src/cursor_metrics/templates/dashboard.html` → Expected: match found

- [ ] T11: Create `src/cursor_metrics/templates/partials/overview_content.html` (DESIGN: Architecture — overview_content.html)
  - Create: `src/cursor_metrics/templates/partials/overview_content.html`
  - 4 metric cards row: Total Tokens, Total Cost, Avg Response Time, API Requests — each with label (14px, `#a1a1a1`), value (30px bold), trend text (14px, `#05df72`), icon container (44×44px, `#fafafa` bg) with SVG icon
  - Two side-by-side chart cards (each ~604px): "Token Usage Over Time" (Chart.js line/area, purple `#8b5cf6`) and "Model Distribution" (Chart.js bar, purple `#8b5cf6`)
  - "Recent Activity" table: header row (Date, Model, Tokens, Cost, Duration), data rows with model badge (`#fafafa` bg, 8px radius)
  - All spacing per FIGMA-REFERENCE.md layout constants
  - Verify: `rg 'Token Usage Over Time' src/cursor_metrics/templates/partials/overview_content.html` → Expected: match found

- [ ] T12: Create `src/cursor_metrics/templates/partials/funnel_content.html` (DESIGN: Architecture — funnel_content.html)
  - Create: `src/cursor_metrics/templates/partials/funnel_content.html`
  - Left card (813px): "Workflow Funnel" heading, "Track projects through your framework stages" subtitle
  - 6 horizontal funnel bars: Spec (`#ad46ff`), Design (`#2b7fff`), UIX (`#8b5cf6`), Tasks (`#00b8db`), Implement (`#00c950`), Review (`#05df72`) — widths proportional to percentage, count label inside, `#262626` bg track, 48px height, 10px radius
  - Between bars: red (`#ff6467`) "−N drop-off" labels, arrow (→) connectors
  - Conversion Rate section: "Overall Conversion Rate" + percentage (20px bold, `#05df72`) + "N of M projects successfully implemented"
  - Right card (395px): "Select Stage" heading, 6 stage buttons — active `#fafafa` bg, inactive `#262626` bg; HTMX `hx-get="/dashboard/funnel-projects?stage=X"` targeting `#funnel-projects`
  - 3 stat cards below: Active Projects (with trend icon), Avg Time in Stage (with clock icon), Blocked (count in `#ff6467`, with alert icon)
  - Include `funnel_projects.html` partial in `#funnel-projects` div
  - Verify: `rg 'Workflow Funnel' src/cursor_metrics/templates/partials/funnel_content.html` → Expected: match found

- [ ] T13: Create `src/cursor_metrics/templates/partials/funnel_projects.html` (DESIGN: Architecture — funnel_projects.html)
  - Create: `src/cursor_metrics/templates/partials/funnel_projects.html`
  - Header: "Recent Projects in {stage_name}" (16px)
  - Table rows: Spec ID in Liberation Mono 12px `#a1a1a1`, Status badge (In Progress: `#2b7fff` bg / `#51a2ff` text; Review: `#f0b100` bg / `#fdc700` text; Blocked: `#ff6467`; Draft: `#262626`; Approved: `#00c950`), Project name (16px), Time in stage right-aligned (14px `#a1a1a1`)
  - Empty state: "No projects in this stage"
  - Verify: `rg 'funnel-projects' src/cursor_metrics/templates/partials/funnel_projects.html` → Expected: match found

### Router Layer

- [ ] T14: Rewrite `src/cursor_metrics/routers/dashboard.py` with tab routing (DESIGN: API / Interfaces)
  - Modify: `src/cursor_metrics/routers/dashboard.py`
  - Replace `dashboard_overview`, `dashboard_by_model`, `by_developer_page`, `dashboard_by_command` with single `dashboard_page` handler
  - `GET /dashboard` accepts `?tab=overview|funnel` (default: overview); builds both `MetricsService` and `WorkflowService`; for HTMX returns partial only, for full load returns `dashboard.html`
  - Add `GET /dashboard/funnel-projects` accepting `?stage=spec|design|uix|tasks|implement|review` (default: spec); returns `funnel_projects.html` partial via `WorkflowService.get_projects_by_stage(stage)`
  - Add 302 redirect handlers for `/dashboard/by-model`, `/dashboard/by-developer`, `/dashboard/by-command` → `/dashboard`
  - Consumes: T4.WorkflowService, T5.MetricsService
  - Produces: `GET /dashboard` endpoint, `GET /dashboard/funnel-projects` endpoint
  - Verify: `rg 'funnel-projects' src/cursor_metrics/routers/dashboard.py` → Expected: match found

### Seed Data

- [ ] T15: Create seed script for `workflow_projects` table (DESIGN: Risks & Tradeoffs — seed data)
  - Create: `scripts/seed_workflow_projects.py`
  - Insert rows for existing specs: 001-docker-fastapi-setup, 002-dashboard-app, 003-expand-telemetry-schema, 004-subagents-and-command-filter, 005-dashboard-redesign — with appropriate stage and status values based on which files exist in each spec dir
  - Uses async SQLAlchemy session from `cursor_metrics.database`
  - Idempotent: skip if `spec_id` already exists
  - Verify: `uv run python scripts/seed_workflow_projects.py --dry-run` → Expected: prints 5 project rows without writing

### Testing

- [ ] T16: Unit tests for `WorkflowRepository` (DESIGN: Architecture — WorkflowRepository)
  - Create: `tests/test_workflow_repo.py`
  - Test: `count_by_stage()` returns correct counts per stage; `projects_by_stage()` filters correctly; `count_blocked()` counts only blocked status; `avg_time_in_stage()` computes correct average; `total_projects()` counts all; empty table returns zeros/empty
  - Follow established pattern: OOP test class, `AsyncSession` fixture, `from __future__ import annotations`
  - Verify: `uv run pytest tests/test_workflow_repo.py -v` → Expected: PASS (≥6 tests)

- [ ] T17: Unit tests for `WorkflowService` (DESIGN: Architecture — WorkflowService)
  - Create: `tests/test_workflow_service.py`
  - Test: `get_funnel_summary()` returns 6 stages in correct order with correct percentages and drop-off values; conversion rate calculation; `get_projects_by_stage()` returns correct fields; edge case: no projects returns zeros
  - Mock `WorkflowRepository` methods
  - Verify: `uv run pytest tests/test_workflow_service.py -v` → Expected: PASS (≥5 tests)

- [ ] T18: Unit tests for `MetricsService.get_overview_with_trends()` (DESIGN: Architecture — MetricsService)
  - Create or modify: `tests/test_metrics_service.py`
  - Test: trend percentage calculation (positive, negative, zero); "—" (None) when prior period has no data; `daily_token_counts` and `model_distribution` pass-through; `recent_events` integration
  - Mock `MetricsRepository` and `PricingService`
  - Verify: `uv run pytest tests/test_metrics_service.py -v -k "trend"` → Expected: PASS (≥4 tests)

- [ ] T19: Unit tests for `MetricsRepository.recent_events()` and `daily_token_counts()` (DESIGN: Architecture — MetricsRepository)
  - Modify: `tests/test_metrics_repo.py`
  - Test: `recent_events()` returns correct columns with limit; `daily_token_counts()` aggregates tokens by day; empty period returns empty list
  - Verify: `uv run pytest tests/test_metrics_repo.py -v -k "recent or daily_token"` → Expected: PASS (≥4 tests)

- [ ] T20: Integration test for dashboard tab routing and HTMX partials (DESIGN: API / Interfaces)
  - Create: `tests/test_dashboard_redesign.py`
  - Test full chain without mocks: `GET /dashboard` returns full page with tab bar; `GET /dashboard?tab=funnel` with `HX-Request: true` returns funnel partial only; `GET /dashboard/funnel-projects?stage=spec` returns filtered table; redirects for `/dashboard/by-model` etc. return 302
  - Uses `httpx.AsyncClient` + `ASGITransport` per established pattern
  - Consumes: T14 (dashboard routes), T4.WorkflowService, T5.MetricsService
  - Verify: `uv run pytest tests/test_dashboard_redesign.py -v` → Expected: PASS (≥6 tests)

- [ ] T21: Visual smoke test — verify templates render without errors (DESIGN: Acceptance Criteria Traceability — Visual)
  - Modify: `tests/test_dashboard_redesign.py` (or `tests/test_templates.py`)
  - Test: overview partial contains "Total Tokens", "Total Cost", "Avg Response Time", "API Requests"; funnel partial contains "Workflow Funnel", all 6 stage names; funnel projects partial contains "Recent Projects in"
  - Test: `base.html` contains Figma design token variables (`--color-bg-primary`, `--color-border`, etc.)
  - Verify: `uv run pytest tests/test_dashboard_redesign.py -v -k "smoke or visual"` → Expected: PASS (≥4 tests)

---

## Previous Spec Learnings

From SPEC-002 IMPLEMENTATION-SUMMARY.md (most recent completed spec with implementation details):

- **HTMX pattern**: Use `_is_htmx()` helper checking `HX-Request: true` header; return partial template for HTMX requests, full template otherwise; use `hx-push-url` for URL state sync (T16 in SPEC-002)
- **Repository pattern**: OOP class with `AsyncSession` constructor; `select().where()` for queries; re-export from `__init__.py` (T2, T5 in SPEC-002)
- **Service pattern**: OOP class with repository constructor injection; orchestrates repo calls and transforms data (T7 in SPEC-002)
- **Template pattern**: `Jinja2Templates` resolved from package path; `TemplateResponse(request, template, context=context)` — note Starlette 1.0 API requires `request` as first positional arg (T12 in SPEC-002)
- **Test pattern**: OOP test classes, `from __future__ import annotations`, `Iterator[None]` fixture types, `httpx.AsyncClient` + `ASGITransport` for router tests (all tasks in SPEC-002)
- **Static files**: `main.py` does NOT currently mount `StaticFiles` — this will be the first time (T6 in this spec)
- **Lint gate**: Run `uv run ruff check .` and `uv run ruff format --check .` before marking tasks complete; SPEC-002 T18 fixed 20 lint errors post-implementation

---

## References

- DESIGN.md#Data Model — `WorkflowProject` table schema, columns, indexes, stage/status enums
- DESIGN.md#Architecture — component table, mermaid interaction diagram
- DESIGN.md#API / Interfaces — route changes, service method signatures
- DESIGN.md#Risks & Tradeoffs — seed data strategy, redirect strategy, trend edge cases
- DESIGN.md#Acceptance Criteria Traceability — AC-to-component mapping
- FIGMA-REFERENCE.md — design tokens, typography, layout constants, SVG asset manifest
- CONSTITUTION.md — repository pattern, service layer, async/await, Pydantic models, test conventions

---

## Definition of Done

- [ ] All tasks completed (T1–T21)
- [ ] All tests passing (`uv run pytest`)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Formatting clean (`uv run ruff format --check .`)
- [ ] Test coverage meets CONSTITUTION.md threshold (≥80%)
- [ ] Old templates archived in `.OLD/` (not deleted)
- [ ] SVG icons served via `/static/icons/`
- [ ] Dashboard loads with both tabs functional
- [ ] Redirects for old URLs return 302
