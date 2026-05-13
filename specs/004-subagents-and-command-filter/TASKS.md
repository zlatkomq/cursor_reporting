# Task Breakdown

## Metadata

| Field | Value |
|-------|-------|
| ID | 004 |
| Name | Subagent Tracking & Command Filtering |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-13 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-13 |
| Jira Ticket | |

---

## Overview

Two parallel tracks implemented in strict dependency order. Track A (T1–T3) adds `subagentStop` capture: a new Alembic migration, ORM/Pydantic expansion, and hook script update. Track B (T4–T10) adds command filtering: repository query parameters, service pass-through, route parameters, and the command filter UI across all dashboard pages plus a new by-command page. T11 closes with a full quality gate.

---

## Tasks

- [ ] T1: Create Alembic migration `003_add_subagent_type` (DESIGN: Database Changes)
  - Produces: `alembic/versions/003_add_subagent_type.py` — `upgrade()` adds `subagent_type VARCHAR(50) NULL`, `downgrade()` drops it; `down_revision` references `002`
  - Verify: `uv run python -c "import importlib.util, sys; spec=importlib.util.spec_from_file_location('m','alembic/versions/003_add_subagent_type.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); assert hasattr(m,'upgrade') and hasattr(m,'downgrade')"` → Expected: no error

- [ ] T2: Expand ORM model, IngestPayload, and ingest router (DESIGN: ORM Model Changes, Pydantic Schema Changes, Ingest Router Changes)
  - Consumes: T1.migration (down_revision chain)
  - Produces: `MetricsEvent.subagent_type: Mapped[str | None]`; `IngestPayload.event_type` Literal includes `"subagent_stop"`; `IngestPayload.subagent_type: str | None = None`; ingest router passes `subagent_type=payload.subagent_type` to constructor
  - Verify: `uv run pytest tests/test_ingest.py -k "subagent"` → Expected: all new subagent-related ingest tests pass

- [ ] T3: Update hook script and hooks.json for subagentStop (DESIGN: Hook Changes)
  - Consumes: T2.IngestPayload
  - Produces: `_build_payload()` maps `"subagentStop"` → `event_type="subagent_stop"`, adds `subagent_type` from event, skips `_extract_command()` when `hook_event_name != "stop"`; `~/.cursor/hooks.json` includes `subagentStop` entry; `scripts/install-hook.sh` writes both hook entries
  - Verify: `uv run pytest tests/test_send_metrics.py -k "subagent"` → Expected: mapping, subagent_type, and command-skip tests pass

- [ ] T4: Add `command_name` filter and `distinct_commands()` to MetricsRepository (DESIGN: Repository Changes)
  - Produces: all seven query methods accept `command_name: str | None = None`; `distinct_commands(since) -> list[str]` returns sorted non-null values
  - Verify: `uv run pytest tests/test_metrics_repo.py -k "command"` → Expected: filter and distinct-commands tests pass

- [ ] T5: Add command filter and `get_by_command()` to MetricsService (DESIGN: Service Changes)
  - Consumes: T4.MetricsRepository
  - Produces: `get_overview(days, command=None)`, `get_by_developer(days, command=None)`, `get_by_model(days, command=None)` forward `command_name` to repository; `get_available_commands(days) -> list[str]`; `get_by_command(days)` returns per-command aggregates
  - Verify: `uv run pytest tests/test_metrics_service.py -k "command"` → Expected: passthrough and get_by_command tests pass

- [ ] T6: Add `command` query param to dashboard and API routes; add by-command routes (DESIGN: Dashboard Router Changes)
  - Consumes: T5.MetricsService
  - Produces: `command: str | None = Query(default=None)` on all 3 dashboard routes and 3 reports API routes; `commands` + `current_command` in template context; `GET /dashboard/by-command`; `GET /api/v1/metrics/by-command`
  - Verify: `uv run pytest tests/test_dashboard.py -k "command"` → Expected: route acceptance, context, and new-route tests pass

- [ ] T7: Create `partials/command_filter.html` (DESIGN: Template Changes — New partial)
  - Consumes: T6.template_context (`commands`, `current_command`, `current_days`)
  - Produces: `src/cursor_metrics/templates/partials/command_filter.html` — "All" button + dynamic command buttons with HTMX attributes and active-state class
  - Verify: `uv run pytest tests/test_templates.py -k "command_filter"` → Expected: renders, All-active, and per-command-active tests pass

- [ ] T8: Update date filter to preserve `command` parameter (DESIGN: Template Changes — Updated date filter)
  - Consumes: T7.command_filter.html
  - Produces: `src/cursor_metrics/templates/partials/date_filter.html` — `hx-get` URLs include `&command={{ current_command }}` when set
  - Verify: `uv run pytest tests/test_templates.py -k "date_filter"` → Expected: command preserved / omitted correctly

- [ ] T9: Include command filter on all dashboard pages and content partials (DESIGN: Template Changes — Include command filter)
  - Consumes: T7.command_filter.html, T8.date_filter.html
  - Produces: `{% include "partials/command_filter.html" %}` added to `dashboard.html`, `by_developer.html`, `by_model.html` and their HTMX content partials
  - Verify: `uv run pytest tests/test_templates.py -k "includes_command_filter"` → Expected: all six templates include the partial

- [ ] T10: Create by-command page templates and add sidebar link (DESIGN: Template Changes — New templates, Sidebar update)
  - Consumes: T6.by_command_route
  - Produces: `by_command.html`, `partials/by_command_content.html` (table: command, event count, total tokens, estimated cost); "By Command" link in `partials/sidebar.html`
  - Verify: `uv run pytest tests/test_templates.py -k "by_command"` → Expected: templates render and sidebar link present

- [ ] T11: Full test suite pass and linting (DESIGN: Testing Strategy)
  - Consumes: T1–T10
  - Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check .` → Expected: zero failures, zero violations

---

## Testing

- [ ] T2: Unit tests — `IngestPayload` accepts `event_type="subagent_stop"` and `subagent_type` field; POST `/api/v1/ingest` with subagent payload returns 202 and persists `subagent_type`
- [ ] T3: Unit tests — `_build_payload()` subagentStop mapping; `subagent_type` in payload; `command_name`/`skill_name` are None for subagentStop; no regression for stop events
- [ ] T4: Unit tests — each repository method accepts `command_name` param; WHERE clause applied (mock inspection); `distinct_commands()` returns sorted list
- [ ] T5: Unit tests — `get_overview(command="specify")` forwards `command_name="specify"` to repo; `get_available_commands()` returns repo list; `get_by_command()` returns aggregates
- [ ] T6: Unit tests — dashboard and API routes accept `?command=specify`; context includes `commands` and `current_command`; `/dashboard/by-command` returns 200; `/api/v1/metrics/by-command` returns JSON
- [ ] T7–T10: Unit tests — template rendering with sample contexts; active-state logic; date-filter URL preservation; sidebar link
- [ ] T1: Integration test — migration `003_add_subagent_type` upgrade/downgrade runs without error against test schema
- [ ] T11: Integration test — full ingest → query → dashboard render flow with `subagent_stop` event and command filter active

---

## Previous Spec Learnings

From SPEC-003 (Expand Telemetry Schema):

- Use Cursor's native snake_case field names directly in the hook script — no camelCase guessing.
- `_extract_command(transcript_path)` reads up to 50 lines; handles missing file, unreadable file, and malformed JSON gracefully — apply same defensive pattern to subagentStop handling.
- `COMMAND_SKILL_MAP` is embedded in the hook script and returns `(None, None)` for unrecognised commands.
- Repository tests use mock session with `.execute()` return value inspection to verify WHERE clauses.
- `estimate_cost()` falls back to legacy flat-rate when token counts are `None` — ensure subagent events with real token counts follow the same cost path as parent events.
- Backward compatibility: old payloads (missing new fields) must still return 202 — continue this pattern for `subagent_type`.

---

## References

- [Source: DESIGN.md#Database Changes] — migration filename, column spec, down_revision
- [Source: DESIGN.md#ORM Model Changes] — `MetricsEvent.subagent_type` mapped column
- [Source: DESIGN.md#Pydantic Schema Changes] — `IngestPayload` Literal expansion and new field
- [Source: DESIGN.md#Ingest Router Changes] — constructor kwarg addition
- [Source: DESIGN.md#Hook Changes] — `hooks.json` structure, `_build_payload()` logic, command-skip condition
- [Source: DESIGN.md#Repository Changes] — seven methods + `distinct_commands()` signature and WHERE pattern
- [Source: DESIGN.md#Service Changes] — `get_overview/get_by_developer/get_by_model` signatures, `get_available_commands()`, `get_by_command()`
- [Source: DESIGN.md#Dashboard Router Changes] — route signatures, context keys, new routes
- [Source: DESIGN.md#Template Changes] — `command_filter.html` markup, date-filter URL pattern, include locations, by-command table columns, sidebar placement
- [Source: CONSTITUTION.md#Testing Standards] — 80% coverage threshold, pytest fixtures, integration test requirement

---

## Definition of Done

- [ ] All tasks completed (T1–T11)
- [ ] All tests passing
- [ ] Test coverage meets CONSTITUTION.md threshold (≥ 80%)
- [ ] Code reviewed and approved
- [ ] No open questions remaining
