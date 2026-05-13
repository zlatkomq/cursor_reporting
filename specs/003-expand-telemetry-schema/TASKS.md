# Tasks

## Metadata

| Field | Value |
|-------|-------|
| Spec ID | 003 |
| Name | Expand Telemetry Schema |
| Status | APPROVED |
| Date | 2026-05-13 |

---

## Task Breakdown

### Phase 1: Database & ORM

#### T1: Alembic migration — expand metrics_events and model_pricing

| Field | Value |
|-------|-------|
| Type | Migration |
| Estimated Size | S |
| Dependencies | None |
| Files | `alembic/versions/002_expand_telemetry.py` |

**Description:** Create Alembic migration `002_expand_telemetry` that:
- Adds 8 nullable columns to `metrics_events`: `input_tokens` (BIGINT), `output_tokens` (BIGINT), `cache_read_tokens` (BIGINT), `cache_write_tokens` (BIGINT), `session_id` (VARCHAR 255), `workspace` (VARCHAR 500), `command_name` (VARCHAR 100), `skill_name` (VARCHAR 100).
- Adds `cost_per_cache_read_token` (NUMERIC 12,8, NOT NULL, server_default "0.00000000") to `model_pricing`.
- Creates indexes: `ix_metrics_events_session_id`, `ix_metrics_events_workspace`.
- Downgrade drops all added columns and indexes.

**Tests:**
- Migration upgrade runs without error (offline mode).
- Migration downgrade runs without error (offline mode).

---

#### T2: Update MetricsEvent ORM model

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | S |
| Dependencies | T1 |
| Files | `src/cursor_metrics/models/db.py` |

**Description:** Add 8 mapped columns to `MetricsEvent`:
- `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens` (BigInteger, nullable)
- `session_id` (String 255, nullable), `workspace` (String 500, nullable)
- `command_name` (String 100, nullable), `skill_name` (String 100, nullable)

Add 2 indexes to `__table_args__`. Add `cost_per_cache_read_token` to `ModelPricing`.

**Tests:**
- `MetricsEvent` has all new attributes.
- `ModelPricing` has `cost_per_cache_read_token`.
- New indexes present in `__table_args__`.

---

### Phase 2: API Schema & Ingest

#### T3: Expand IngestPayload Pydantic model

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | S |
| Dependencies | None |
| Files | `src/cursor_metrics/models/metrics.py` |

**Description:** Add 8 optional fields to `IngestPayload`, all defaulting to `None`:
- `input_tokens: int | None`
- `output_tokens: int | None`
- `cache_read_tokens: int | None`
- `cache_write_tokens: int | None`
- `session_id: str | None`
- `workspace: str | None`
- `command_name: str | None`
- `skill_name: str | None`

**Tests:**
- Payload with all new fields validates.
- Payload without new fields validates (backward compat).
- Invalid types for token fields rejected (422).

---

#### T4: Update ingest router to persist new fields

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | S |
| Dependencies | T2, T3 |
| Files | `src/cursor_metrics/routers/ingest.py` |

**Description:** Extend the `MetricsEvent` constructor in `ingest()` to pass all 8 new fields from the payload.

**Tests:**
- POST with full payload (including tokens) returns 202.
- POST with old payload (no tokens) returns 202.
- Mock DB session's `add()` receives a `MetricsEvent` with the new fields set.

---

### Phase 3: Hook Script

#### T5: Rewrite hook script with correct field mapping and token capture

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | M |
| Dependencies | T3 |
| Files | `scripts/send-metrics.py`, `~/.cursor/hooks/send-metrics.py` |

**Description:** Rewrite `send-metrics.py` to:
- Use Cursor's native snake_case field names directly (remove camelCase guessing).
- Use `user_email` from Cursor event directly, with `_git_email()` as fallback.
- Pass `input_tokens`, `output_tokens`, `cache_read_tokens`, `cache_write_tokens`, `session_id` directly.
- Extract `workspace` from `workspace_roots[0]`.
- Remove `duration_ms` from payload (not in Cursor's actual output).
- Keep debug logging to `~/.cursor/hooks-logs/stop-events.jsonl`.

**Tests:**
- Script accepts full Cursor payload JSON on stdin and produces `{}` on stdout.
- Payload built from Cursor event maps all fields correctly.
- `_extract_workspace()` returns first root or `None`.
- `user_email` uses event value when present, falls back to git config.

---

#### T6: Add transcript parsing for command and skill extraction

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | M |
| Dependencies | T5 |
| Files | `scripts/send-metrics.py`, `~/.cursor/hooks/send-metrics.py` |

**Description:** Add `_extract_command(transcript_path)` function to hook script:
- Reads up to 50 lines of the JSONL transcript.
- Finds the first user message (`role == "user"`).
- If the message starts with `/`, extracts the command name (e.g. `specify`).
- Maps command to skill using embedded `COMMAND_SKILL_MAP` dict.
- Returns `(command_name, skill_name)` tuple — both `None` if no command found.
- Handles missing file, unreadable file, and malformed JSON gracefully.

Embed the initial mapping:
```python
COMMAND_SKILL_MAP = {
    "specify": "spec-creation",
    "design": "design-creation",
    "implement": "implementation",
    "review": "code-review",
}
```

Integrate into the payload builder. Update `scripts/install-hook.sh` copy source if needed.

**Tests:**
- `/specify 003 foo` → `("specify", "spec-creation")`.
- `/design 003` → `("design", "design-creation")`.
- `/unknown-cmd` → `("unknown-cmd", None)`.
- Normal message (no `/`) → `(None, None)`.
- Missing transcript file → `(None, None)`.
- Empty/malformed transcript → `(None, None)`.
- Transcript with >50 lines, command in line 1 → still found.

---

### Phase 4: Repository & Service Layer

#### T7: Add token aggregation to MetricsRepository

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | M |
| Dependencies | T2 |
| Files | `src/cursor_metrics/repositories/metrics_repo.py` |

**Description:**
- Add `total_tokens(since)` method returning `{"input_tokens": int, "output_tokens": int, "cache_read_tokens": int, "cache_write_tokens": int}`.
- Update `events_by_model(since)` to include `total_input_tokens`, `total_output_tokens`, `total_cache_read_tokens` in returned dicts.

**Tests:**
- `total_tokens()` returns correct aggregates (mock session).
- `total_tokens()` returns zeros when no events exist.
- `events_by_model()` includes token sums in results.

---

#### T8: Update PricingService for real token-based cost calculation

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | M |
| Dependencies | T2, T7 |
| Files | `src/cursor_metrics/services/pricing_service.py` |

**Description:**
- Update `get_pricing_map()` to return `(cost_per_input, cost_per_output, cost_per_cache_read)` tuples.
- Update `estimate_cost()` signature to accept optional `input_tokens`, `output_tokens`, `cache_read_tokens`.
- When real token counts provided: `cost = input × rate_in + output × rate_out + cache_read × rate_cache`.
- When tokens are `None`: fall back to existing flat-rate placeholder.
- `cache_write_tokens` is NOT included in cost (tracked only).

**Tests:**
- Real tokens + known pricing → correct cost.
- `None` tokens → legacy flat-rate calculation (unchanged).
- Model not in pricing table → `Decimal(0)`.
- `get_pricing_map()` returns 3-tuples including cache read rate.

---

#### T9: Update MetricsService to pass token data

| Field | Value |
|-------|-------|
| Type | Code |
| Estimated Size | S |
| Dependencies | T7, T8 |
| Files | `src/cursor_metrics/services/metrics_service.py` |

**Description:**
- Update `get_overview()` to call `total_tokens()` and include token sums in response.
- Update `get_by_model()` to pass real token counts from `events_by_model()` to `PricingService.estimate_cost()`.

**Tests:**
- `get_overview()` response includes `total_input_tokens`, `total_output_tokens`, `total_cache_read_tokens`, `total_cache_write_tokens`.
- `get_by_model()` uses real token counts for cost estimation when available.

---

### Phase 5: Documentation & Cleanup

#### T10: Update CONSTITUTION.md and install script

| Field | Value |
|-------|-------|
| Type | Documentation |
| Estimated Size | S |
| Dependencies | T5, T6 |
| Files | `CONSTITUTION.md`, `scripts/install-hook.sh` |

**Description:**
- Update the "Ingest Payload Schema" section in `CONSTITUTION.md` with all new fields.
- Update the "Hook Events Used" table to mention token capture and command extraction.
- Ensure `scripts/install-hook.sh` copies the updated `scripts/send-metrics.py`.

**Tests:**
- Verify CONSTITUTION payload schema lists all 8 new fields.
- Verify install script source file path is correct.

---

#### T11: Full test suite pass and linting

| Field | Value |
|-------|-------|
| Type | Quality |
| Estimated Size | S |
| Dependencies | T1–T10 |
| Files | All modified files |

**Description:**
- Run `uv run pytest` — all tests pass.
- Run `uv run ruff check .` — no lint errors.
- Run `uv run ruff format --check .` — no format errors.
- Fix any regressions in existing tests caused by schema changes.
- Ensure backward compatibility: old payloads (without new fields) still accepted.

**Tests:**
- Full test suite green.
- Zero lint/format violations.

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1. Database & ORM | T1, T2 | Migration + ORM model updates |
| 2. API Schema & Ingest | T3, T4 | Pydantic model + router changes |
| 3. Hook Script | T5, T6 | Field mapping fix + transcript parsing |
| 4. Repository & Service | T7, T8, T9 | Token aggregation + real cost calc |
| 5. Docs & Cleanup | T10, T11 | Constitution update + full quality pass |

**Total: 11 tasks across 5 phases.**

### Dependency Graph

```
T1 ──→ T2 ──→ T4
               ↑
T3 ────────────┘──→ T5 ──→ T6 ──→ T10
                                    ↓
T2 ──→ T7 ──→ T8 ──→ T9 ──→ T11
```
