# Specification

## Metadata

| Field | Value |
|-------|-------|
| ID | 003 |
| Name | Expand Telemetry Schema |
| Type | Enhancement |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-13 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-13 |
| Jira Ticket | |

---

## Overview

Expand the telemetry ingestion pipeline to capture the full payload that Cursor IDE hooks actually provide — most critically **token counts** (`input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`), **workspace context**, and **session grouping**. Additionally, extract the **custom command name** (e.g. `/specify`, `/design`) and **skill name** from the agent transcript so that framework-level steps are tracked alongside raw Cursor telemetry. This replaces the current placeholder cost estimation (flat 1,000 tokens per event) with real token-based calculations.

---

## Context: Actual Cursor Hook Payload

The `stop` hook event provides the following JSON on stdin (discovered from live testing):

```json
{
  "conversation_id": "39c34bc5-b7f3-4313-aeac-8ff2551576b0",
  "generation_id": "433ae6fc-4169-4b6e-ba76-8196d7f94bec",
  "model": "claude-opus-4-6",
  "status": "completed",
  "loop_count": 0,
  "input_tokens": 2117969,
  "output_tokens": 19841,
  "cache_read_tokens": 2046472,
  "cache_write_tokens": 71458,
  "session_id": "39c34bc5-b7f3-4313-aeac-8ff2551576b0",
  "hook_event_name": "stop",
  "cursor_version": "3.3.30",
  "workspace_roots": ["/home/k/Desktop/AI/cursor-metrics"],
  "user_email": "dev@company.com",
  "transcript_path": "/home/k/.cursor/projects/.../agent-transcripts/.../uuid.jsonl"
}
```

Key fields **not currently captured**: `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `session_id`, `workspace_roots`, `transcript_path`.

Key fields **derived from transcript** (not in Cursor payload): `command_name`, `skill_name`.

---

## User Stories

- As a **team lead**, I want to see actual token usage (input, output, cache) per session, so that cost estimates are based on real data instead of guesses.
- As a **team lead**, I want to see which custom framework commands (`/specify`, `/design`, `/implement`) are being used, so that I can understand how the team applies our workflow.
- As a **developer**, I want my workspace (project) associated with each event, so I can see metrics broken down by project.
- As a **team lead**, I want accurate cost calculations based on real token counts and per-model pricing, so that I can report actual AI spend.

---

## Acceptance Criteria

- [ ] AC-1: Given a hook `stop` event, when the payload includes `input_tokens`, `output_tokens`, `cache_read_tokens`, and `cache_write_tokens`, then all four values are persisted to the `metrics_events` table.
- [ ] AC-2: Given a hook `stop` event, when the payload includes `session_id`, then it is persisted and available for grouping multi-generation conversations.
- [ ] AC-3: Given a hook `stop` event with `workspace_roots`, then the first workspace root path is persisted as the event's workspace.
- [ ] AC-4: Given a hook `stop` event with a `transcript_path`, when the transcript's first user message starts with `/` (a custom command like `/specify 003`), then the command name (e.g. `specify`) is extracted and persisted as `command_name`.
- [ ] AC-5: Given a `command_name` is extracted, when a mapping exists from command to skill (e.g. `specify` -> `spec-creation`), then the `skill_name` is also persisted.
- [ ] AC-6: Given the hook script, when it sends data to the API, then it uses the actual Cursor field names (`input_tokens`, `output_tokens`, `session_id`, etc.) directly — no camelCase-to-snake_case guessing.
- [ ] AC-7: Given events with token counts in the database, when the dashboard calculates cost, then it uses `(input_tokens * cost_per_input_token) + (output_tokens * cost_per_output_token)` from real data, not the flat-rate placeholder.
- [ ] AC-8: Given the schema change, when `alembic upgrade head` is run, then new columns are added to the existing `metrics_events` table without data loss.
- [ ] AC-9: Given the expanded `IngestPayload`, when old clients send payloads without the new fields, then the endpoint still accepts them (all new fields default to `None`).
- [ ] AC-10: Given the `model_pricing` table, when it contains cache token pricing, then `cache_read_tokens` are priced at their (typically discounted) rate.

---

## Scope

**In Scope:**

- Add columns to `metrics_events`: `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `session_id`, `workspace`, `command_name`, `skill_name`
- Add `cost_per_cache_read_token` column to `model_pricing`
- Alembic migration for new columns (ALTER TABLE, nullable, backward-compatible)
- Expand `IngestPayload` Pydantic model with new optional fields
- Update ingest router to persist new fields
- Update hook script (`~/.cursor/hooks/send-metrics.py` and `scripts/send-metrics.py`) to:
  - Pass all Cursor-provided fields directly (no field name guessing)
  - Read `transcript_path` and extract `command_name` from first user message
  - Map `command_name` to `skill_name` via a configurable mapping
- Update `PricingService.estimate_cost()` to use real token counts when available, fall back to placeholder when not
- Add `cost_per_cache_read_token` to `ModelPricing` ORM model
- Update `MetricsRepository` queries to aggregate token counts (SUM input/output/cache tokens)
- Update `MetricsService` to pass real token counts to pricing
- Update install script (`scripts/install-hook.sh`) to copy the new hook version
- Update CONSTITUTION.md ingest payload schema documentation

**Out of Scope:**

- Dashboard UI changes for token breakdown charts (separate spec)
- `model_pricing` seed data / admin CRUD (future spec)
- `sessionEnd` hook event handling (only `stop` for now)
- Transcript content analysis beyond first user message (e.g. summarization)
- Cache write token pricing (tracked for visibility only, not billed)

---

## Dependencies

- **SPEC-001** (Docker & FastAPI Setup) — provides the database, ORM, and migration infrastructure.
- **SPEC-002** (Dashboard Application) — provides the dashboard, services, and repositories this spec modifies.

---

## Schema Changes

### `metrics_events` — New Columns

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `input_tokens` | BIGINT | YES | NULL | From Cursor hook `input_tokens` |
| `output_tokens` | BIGINT | YES | NULL | From Cursor hook `output_tokens` |
| `cache_read_tokens` | BIGINT | YES | NULL | From Cursor hook `cache_read_tokens` |
| `cache_write_tokens` | BIGINT | YES | NULL | From Cursor hook `cache_write_tokens` |
| `session_id` | VARCHAR(255) | YES | NULL | Groups multi-gen conversations |
| `workspace` | VARCHAR(500) | YES | NULL | First item from `workspace_roots` |
| `command_name` | VARCHAR(100) | YES | NULL | Extracted from transcript, e.g. `specify` |
| `skill_name` | VARCHAR(100) | YES | NULL | Mapped from command, e.g. `spec-creation` |

### `model_pricing` — New Column

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `cost_per_cache_read_token` | NUMERIC(12,8) | NO | 0.00000000 | Typically discounted vs. input rate |

### New Indexes

| Index | Columns | Purpose |
|-------|---------|---------|
| `ix_metrics_events_session_id` | `session_id` | Session grouping queries |
| `ix_metrics_events_workspace` | `workspace` | Per-project filtering |

---

## Hook Script Changes

### Field Mapping (Cursor → API)

Current hook guesses at camelCase field names. The actual Cursor payload uses **snake_case** natively:

| Cursor Field | API Field | Current Hook | Fix |
|---|---|---|---|
| `conversation_id` | `conversation_id` | `event.get("conversationId", ...)` | Use directly |
| `generation_id` | `generation_id` | `event.get("generationId", ...)` | Use directly |
| `model` | `model` | Correct | — |
| `status` | `status` | Correct | — |
| `loop_count` | `loop_count` | `event.get("loopCount")` | Use directly |
| `input_tokens` | `input_tokens` | Not captured | Add |
| `output_tokens` | `output_tokens` | Not captured | Add |
| `cache_read_tokens` | `cache_read_tokens` | Not captured | Add |
| `cache_write_tokens` | `cache_write_tokens` | Not captured | Add |
| `session_id` | `session_id` | Not captured | Add |
| `cursor_version` | `cursor_version` | `event.get("cursorVersion")` | Use directly |
| `user_email` | `user_email` | git config fallback | Use directly |
| `workspace_roots[0]` | `workspace` | Not captured | Extract first |
| (transcript) | `command_name` | Not captured | Parse transcript |
| (derived) | `skill_name` | Not captured | Map from command |

### Transcript Parsing

The hook reads `transcript_path` from the event, opens the JSONL file, finds the first user message, and checks if it starts with `/`:

```
User message: "/specify 003 expand telemetry schema"
→ command_name: "specify"
→ skill_name: "spec-creation" (from mapping)
```

### Command → Skill Mapping

Configurable in the hook script. Initial mapping:

| Command | Skill |
|---------|-------|
| `specify` | `spec-creation` |
| `design` | `design-creation` |
| `implement` | `implementation` |
| `review` | `code-review` |

Unknown commands set `command_name` but leave `skill_name` as `None`.

---

## Updated Ingest Payload Schema

```json
{
  "event_type": "stop | session_end",
  "conversation_id": "string (default: 'unknown')",
  "generation_id": "string (default: 'unknown')",
  "model": "string (default: 'unknown')",
  "user_email": "string (default: 'unknown')",
  "status": "completed | aborted | error (default: 'completed')",
  "duration_ms": "int | null",
  "loop_count": "int | null",
  "cursor_version": "string | null",
  "timestamp": "ISO 8601 | null",
  "input_tokens": "int | null",
  "output_tokens": "int | null",
  "cache_read_tokens": "int | null",
  "cache_write_tokens": "int | null",
  "session_id": "string | null",
  "workspace": "string | null",
  "command_name": "string | null",
  "skill_name": "string | null"
}
```

All new fields are optional with `None` defaults — fully backward-compatible with older hook versions.

---

## Cost Calculation Change

### Current (placeholder)

```
cost = event_count × (cost_per_input + cost_per_output) × 1000
```

### New (real tokens)

```
cost = SUM(input_tokens × cost_per_input_token)
      + SUM(output_tokens × cost_per_output_token)
      + SUM(cache_read_tokens × cost_per_cache_read_token)
```

`cache_write_tokens` are stored for visibility but **not priced**.

When token counts are `NULL` (legacy events), fall back to the existing flat-rate placeholder per event.

---

## Open Questions

None — all questions resolved.

---

## Decisions Made

| Question | Decision |
|----------|----------|
| Backward compatibility | All new columns and payload fields are nullable/optional — zero breaking changes |
| Hook field naming | Use Cursor's native snake_case directly; remove camelCase guessing |
| Cache write pricing | Track `cache_write_tokens` but do NOT price them — store for visibility only |
| Command→Skill mapping | Embed directly in the hook script as a Python dict — no external config file |
| Transcript read limit | Read only the first 50 lines of the transcript JSONL when parsing for the command |

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
