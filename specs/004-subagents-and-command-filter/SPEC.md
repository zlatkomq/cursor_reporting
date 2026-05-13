# Specification

## Metadata

| Field | Value |
|-------|-------|
| ID | 004 |
| Name | Subagent Tracking & Command Filtering |
| Type | Enhancement |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-13 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-13 |
| Jira Ticket | |

---

## Overview

Extend the metrics pipeline in two directions:

1. **Subagent tracking** — Capture individual subagent completions via the `subagentStop` Cursor hook event. Each parent agent session spawns multiple subagents (e.g. T1–T11 implementer/reviewer subagents), each with its own model, token counts, and status. Currently only the parent `stop` event is captured, losing per-subagent granularity. By adding a `subagentStop` hook, every subagent completion is recorded as its own `metrics_events` row, linked to the parent via `session_id`.

2. **Command filtering on the dashboard** — Add a command filter (dropdown or button group) to all dashboard pages, allowing users to filter metrics by `command_name` (e.g. `/specify`, `/design`, `/implement`). This leverages the `command_name` field added in SPEC-003.

---

## Context: Subagent Data

A single parent agent session (e.g. this conversation) spawns many subagents. Example from the current session: **79 subagent transcripts** in the `subagents/` directory. Each subagent has:

- Its own `conversation_id` (subagent UUID)
- The parent `session_id`
- Its own model (e.g. `claude-opus-4-6`, `claude-4.6-sonnet-medium-thinking`)
- Its own token counts (`input_tokens`, `output_tokens`, etc.)
- A `subagent_type` (e.g. `generalPurpose`, `explore`, `shell`)

The `subagentStop` hook event fires when each subagent completes and provides this data on stdin.

---

## User Stories

- As a **team lead**, I want to see how many subagents each session spawns and how many tokens they consume individually, so I can understand the true cost breakdown of complex tasks.
- As a **team lead**, I want to filter the dashboard by command type (`/specify`, `/design`, etc.), so I can see how much each workflow step costs.
- As a **developer**, I want to see which subagent types (generalPurpose, explore, shell) are used most, so I can optimize my workflow.
- As a **dashboard user**, I want to filter any dashboard page by command, so I can compare cost/usage across different framework steps.

---

## Acceptance Criteria

### Subagent Tracking

- [ ] AC-1: Given a `subagentStop` hook event, when a subagent completes, then a new row is inserted into `metrics_events` with `event_type = "subagent_stop"`.
- [ ] AC-2: Given a subagent event, when it includes a parent `session_id`, then the subagent row references the same `session_id` for grouping.
- [ ] AC-3: Given a subagent event with token counts, then `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens` are persisted.
- [ ] AC-4: Given a subagent event with `subagent_type`, then it is persisted in a new `subagent_type` column.
- [ ] AC-5: Given the dashboard overview, when subagent events exist, then they are counted in total event counts, token sums, and cost calculations (no separate stat card).

### Command Filtering

- [ ] AC-6: Given the dashboard overview page, when the user selects a command filter (e.g. "specify"), then all stats, charts, and tables update to show only events from that command.
- [ ] AC-7: Given the by-developer page, when a command filter is active, then the developer table shows only events matching that command.
- [ ] AC-8: Given the by-model page, when a command filter is active, then the model table shows only events matching that command.
- [ ] AC-9: Given the command filter, when "All" is selected, then no filtering is applied (full data shown).
- [ ] AC-10: Given the command filter, the available commands are populated dynamically from distinct `command_name` values in the database for the current period.
- [ ] AC-11: Given the command filter combined with the date filter, both filters apply simultaneously.

---

## Scope

**In Scope:**

- Add `subagentStop` hook entry to `~/.cursor/hooks.json`
- Create/update hook script to handle `subagentStop` events
- Add `subagent_type` column to `metrics_events` (nullable VARCHAR 50)
- Add `event_type` value `"subagent_stop"` to `IngestPayload` Literal
- Alembic migration for new column
- Update all dashboard pages with a command filter bar (HTMX-powered, like the date filter)
- Add `command` query parameter to dashboard routes and reports API
- Update `MetricsRepository` queries to accept optional `command_name` filter
- Update `MetricsService` to pass command filter through
- Populate command filter dropdown from distinct `command_name` values
- Update sidebar to include a "By Command" page showing command-level breakdown
- Update `scripts/install-hook.sh` to register the `subagentStop` hook

**Out of Scope:**

- Parsing subagent transcript files (the hook captures data directly from the event)
- Subagent-level drill-down UI (clicking a session to see its subagents — future spec)
- Real-time subagent progress tracking
- Custom date range picker (still using 7d/30d/90d presets)

---

## Dependencies

- **SPEC-003** (Expand Telemetry Schema) — provides token columns, `session_id`, `command_name`, `workspace` fields.

---

## Schema Changes

### `metrics_events` — New Column

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `subagent_type` | VARCHAR(50) | YES | NULL | e.g. `generalPurpose`, `explore`, `shell` |

### `IngestPayload` — Changes

- `event_type` Literal expands: `"stop" | "session_end" | "subagent_stop"`
- Add `subagent_type: str | None = None`

---

## Hook Changes

### `hooks.json` — Add subagentStop

```json
{
  "version": 1,
  "hooks": {
    "stop": [
      { "command": "hooks/send-metrics.py", "timeout": 10 }
    ],
    "subagentStop": [
      { "command": "hooks/send-metrics.py", "timeout": 10 }
    ]
  }
}
```

The same `send-metrics.py` script handles both events — it reads `hook_event_name` from stdin to determine the event type. For `subagentStop`, the `transcript_path` may not be available, so `command_name`/`skill_name` extraction is skipped.

### Hook Script — subagentStop payload

Best-guess payload (based on `stop` event shape, to be refined after first live event):
- `hook_event_name`: `"subagentStop"`
- `conversation_id`: subagent's own ID
- `session_id`: parent session ID (for linking)
- `model`, `status`, `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`
- `subagent_type`: e.g. `"generalPurpose"`, `"explore"`, `"shell"`
- `cursor_version`, `user_email`, `workspace_roots`

The hook maps `hook_event_name` `"subagentStop"` to `event_type` `"subagent_stop"`.

The script always logs raw stdin to `~/.cursor/hooks-logs/stop-events.jsonl` regardless of event type, so the first real `subagentStop` event will be captured for inspection and refinement.

**Note:** For `subagentStop` events, `transcript_path` may not be present, so `command_name`/`skill_name` extraction is skipped. The subagent inherits the parent's command context via `session_id`.

---

## Dashboard Changes

### Command Filter Bar

A new row of buttons (matching the date filter style) appears on all dashboard pages, positioned below the date filter. It contains:

- **"All" button** (default active, no filter)
- **Dynamic command buttons** populated from distinct `command_name` values in the DB for the current period (e.g. "specify", "design", "implement", "review")
- Approximately 7-8 commands expected — fits well as a button row

Both filters (date + command) work together via HTMX. The URL updates to include both: `/dashboard?days=30&command=specify`.

### New Sidebar Link: "By Command"

A new page `/dashboard/by-command` showing a table with:
- Command name
- Event count (parent + subagent)
- Total tokens (input + output)
- Estimated cost
- Average subagents per session

### Updated Routes

All dashboard routes and reports API endpoints accept an optional `command` query parameter:
- `/dashboard?days=30&command=specify`
- `/dashboard/by-developer?days=30&command=design`
- `/api/v1/metrics?days=30&command=specify`

---

## Open Questions

None — all questions resolved.

---

## Decisions Made

| Question | Decision |
|----------|----------|
| Same hook script for both events | Yes — `send-metrics.py` handles both `stop` and `subagentStop` based on `hook_event_name` |
| Subagent linking | Via `session_id` — parent and subagents share the same session |
| subagentStop approach | Log-first: capture raw events to debug log, build against best guess from `stop` shape, refine after first real event |
| Command filter UI | Row of buttons (like date filter) — there are ~7-8 commands, fits well as buttons |
| Subagent events in totals | Included in total event count — no separate stat card, just counted alongside parent events |

---

## Bug History

| Bug ID | Severity | Date Fixed | Description |
|--------|----------|------------|-------------|
| - | - | No bugs reported | - |

---

## Amendment History

| CR ID | Date | Description | Approved By |
|-------|------|-------------|-------------|
| - | - | No amendments | - |
