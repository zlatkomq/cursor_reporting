# Design

## Metadata

| Field | Value |
|-------|-------|
| Spec ID | 003 |
| Name | Expand Telemetry Schema |
| Status | APPROVED |
| Date | 2026-05-13 |

---

## Architecture Overview

This is a vertical enhancement that touches every layer of the existing stack — from the Cursor hook script at the edge, through the API payload and ingest route, down to the database schema, and back up through the repository/service/pricing layers. No new services or modules are introduced; existing ones are extended.

```
┌─────────────────────────────────────────────────────────────────┐
│ Cursor IDE (developer machine)                                  │
│                                                                 │
│  stop event ─→ ~/.cursor/hooks/send-metrics.py                  │
│                  │ 1. Read transcript_path (first 50 lines)     │
│                  │ 2. Extract /command → command_name, skill     │
│                  │ 3. Build payload with all native fields       │
│                  │ 4. POST /api/v1/ingest                       │
│                  ▼                                              │
├─────────────────────────────────────────────────────────────────┤
│ FastAPI API Server                                              │
│                                                                 │
│  IngestPayload (expanded Pydantic model)                        │
│       │                                                         │
│       ▼                                                         │
│  ingest router → MetricsEvent ORM (expanded)                    │
│       │                                                         │
│       ▼                                                         │
│  MariaDB  metrics_events (8 new columns)                        │
│           model_pricing  (1 new column)                         │
│                                                                 │
│  MetricsRepository (token aggregation queries)                  │
│       │                                                         │
│       ▼                                                         │
│  PricingService (real token-based cost calc)                    │
│       │                                                         │
│       ▼                                                         │
│  MetricsService (passes real tokens to pricing)                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Changes

### Migration: `002_expand_telemetry.py`

Single Alembic migration that adds columns to two tables. All new columns are nullable (or have server defaults) so existing data is preserved.

#### `metrics_events` — ADD COLUMN

```python
op.add_column("metrics_events", sa.Column("input_tokens", sa.BigInteger, nullable=True))
op.add_column("metrics_events", sa.Column("output_tokens", sa.BigInteger, nullable=True))
op.add_column("metrics_events", sa.Column("cache_read_tokens", sa.BigInteger, nullable=True))
op.add_column("metrics_events", sa.Column("cache_write_tokens", sa.BigInteger, nullable=True))
op.add_column("metrics_events", sa.Column("session_id", sa.String(255), nullable=True))
op.add_column("metrics_events", sa.Column("workspace", sa.String(500), nullable=True))
op.add_column("metrics_events", sa.Column("command_name", sa.String(100), nullable=True))
op.add_column("metrics_events", sa.Column("skill_name", sa.String(100), nullable=True))

op.create_index("ix_metrics_events_session_id", "metrics_events", ["session_id"])
op.create_index("ix_metrics_events_workspace", "metrics_events", ["workspace"])
```

#### `model_pricing` — ADD COLUMN

```python
op.add_column("model_pricing", sa.Column(
    "cost_per_cache_read_token", sa.Numeric(12, 8), nullable=False, server_default="0.00000000"
))
```

#### Downgrade

Drop the columns and indexes in reverse order.

---

## ORM Model Changes

### `MetricsEvent` (models/db.py)

Add 8 mapped columns:

```python
input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
output_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
cache_read_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
cache_write_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
session_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
workspace: Mapped[str | None] = mapped_column(String(500), nullable=True)
command_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
skill_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
```

Add indexes to `__table_args__`:

```python
Index("ix_metrics_events_session_id", "session_id"),
Index("ix_metrics_events_workspace", "workspace"),
```

### `ModelPricing` (models/db.py)

Add 1 column:

```python
cost_per_cache_read_token: Mapped[Decimal] = mapped_column(
    Numeric(12, 8), nullable=False, server_default=text("0.00000000")
)
```

---

## Pydantic Schema Changes

### `IngestPayload` (models/metrics.py)

Add optional fields:

```python
input_tokens: int | None = None
output_tokens: int | None = None
cache_read_tokens: int | None = None
cache_write_tokens: int | None = None
session_id: str | None = None
workspace: str | None = None
command_name: str | None = None
skill_name: str | None = None
```

All default to `None` — fully backward-compatible.

---

## Ingest Router Changes

### `routers/ingest.py`

The `ingest()` endpoint already creates a `MetricsEvent` from the payload. Simply add the new fields to the constructor:

```python
event = MetricsEvent(
    # ... existing fields ...
    input_tokens=payload.input_tokens,
    output_tokens=payload.output_tokens,
    cache_read_tokens=payload.cache_read_tokens,
    cache_write_tokens=payload.cache_write_tokens,
    session_id=payload.session_id,
    workspace=payload.workspace,
    command_name=payload.command_name,
    skill_name=payload.skill_name,
)
```

---

## Hook Script Changes

### `send-metrics.py` (both `~/.cursor/hooks/` and `scripts/`)

#### 1. Fix field mapping

Remove all camelCase guessing. Cursor provides snake_case natively:

```python
payload = {
    "event_type": event.get("hook_event_name", "stop"),
    "conversation_id": event.get("conversation_id", "unknown"),
    "generation_id": event.get("generation_id", "unknown"),
    "model": event.get("model", "unknown"),
    "user_email": event.get("user_email") or _git_email(),
    "status": event.get("status", "completed"),
    "loop_count": event.get("loop_count"),
    "cursor_version": event.get("cursor_version"),
    "input_tokens": event.get("input_tokens"),
    "output_tokens": event.get("output_tokens"),
    "cache_read_tokens": event.get("cache_read_tokens"),
    "cache_write_tokens": event.get("cache_write_tokens"),
    "session_id": event.get("session_id"),
    "workspace": _extract_workspace(event),
    "timestamp": datetime.now(timezone.utc).isoformat(),
}
```

#### 2. Extract workspace

```python
def _extract_workspace(event: dict) -> str | None:
    roots = event.get("workspace_roots")
    if roots and isinstance(roots, list) and len(roots) > 0:
        return roots[0]
    return None
```

#### 3. Extract command from transcript

```python
COMMAND_SKILL_MAP = {
    "specify": "spec-creation",
    "design": "design-creation",
    "implement": "implementation",
    "review": "code-review",
}
MAX_TRANSCRIPT_LINES = 50

def _extract_command(transcript_path: str | None) -> tuple[str | None, str | None]:
    if not transcript_path or not os.path.isfile(transcript_path):
        return None, None
    try:
        with open(transcript_path) as f:
            for i, line in enumerate(f):
                if i >= MAX_TRANSCRIPT_LINES:
                    break
                event = json.loads(line)
                if event.get("role") == "user":
                    text = (event.get("content") or "").strip()
                    if text.startswith("/"):
                        cmd = text.split()[0].lstrip("/")
                        return cmd, COMMAND_SKILL_MAP.get(cmd)
                    break
    except (OSError, json.JSONDecodeError):
        pass
    return None, None
```

#### 4. Integrate into payload

```python
command_name, skill_name = _extract_command(event.get("transcript_path"))
payload["command_name"] = command_name
payload["skill_name"] = skill_name
```

---

## Repository Changes

### `MetricsRepository` (repositories/metrics_repo.py)

#### New method: `total_tokens(since)`

Aggregate token counts for the period:

```python
async def total_tokens(self, since: datetime) -> dict[str, int]:
    stmt = select(
        func.coalesce(func.sum(MetricsEvent.input_tokens), 0).label("input"),
        func.coalesce(func.sum(MetricsEvent.output_tokens), 0).label("output"),
        func.coalesce(func.sum(MetricsEvent.cache_read_tokens), 0).label("cache_read"),
        func.coalesce(func.sum(MetricsEvent.cache_write_tokens), 0).label("cache_write"),
    ).where(MetricsEvent.timestamp >= since)
    row = (await self._session.execute(stmt)).one()
    return {
        "input_tokens": row.input,
        "output_tokens": row.output,
        "cache_read_tokens": row.cache_read,
        "cache_write_tokens": row.cache_write,
    }
```

#### Update `events_by_model(since)`

Add token sum columns to the per-model query:

```python
func.coalesce(func.sum(MetricsEvent.input_tokens), 0).label("total_input_tokens"),
func.coalesce(func.sum(MetricsEvent.output_tokens), 0).label("total_output_tokens"),
func.coalesce(func.sum(MetricsEvent.cache_read_tokens), 0).label("total_cache_read_tokens"),
```

Return these in the result dicts so `PricingService` can use real numbers.

---

## Service Changes

### `PricingService` (services/pricing_service.py)

#### Update `get_pricing_map()`

Return cache read pricing too:

```python
return {
    row.model: (row.cost_per_input_token, row.cost_per_output_token, row.cost_per_cache_read_token)
    for row in rows
}
```

#### Update `estimate_cost()`

New signature accepts optional token counts:

```python
async def estimate_cost(
    self,
    model: str,
    event_count: int,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cache_read_tokens: int | None = None,
) -> Decimal:
```

Logic:
- If `input_tokens` is not None → use real token-based calculation
- Else → fall back to existing flat-rate placeholder

```python
if input_tokens is not None:
    cost_in, cost_out, cost_cache = pricing_map[model]
    return (
        Decimal(input_tokens) * cost_in
        + Decimal(output_tokens or 0) * cost_out
        + Decimal(cache_read_tokens or 0) * cost_cache
    )
# Legacy fallback
return event_count * (cost_in + cost_out) * _TOKENS_PER_EVENT
```

### `MetricsService` (services/metrics_service.py)

#### Update `get_overview()`

Add total token counts to the overview response:

```python
tokens = await self._repository.total_tokens(since)
# ... add to response dict
```

#### Update `get_by_model()`

Pass real token counts from the enriched model query to `PricingService.estimate_cost()`.

---

## Install Script Changes

### `scripts/install-hook.sh`

No structural changes — it already copies `scripts/send-metrics.py` to `~/.cursor/hooks/`. The updated script will be picked up automatically on next install.

---

## Testing Strategy

| Area | Test Type | Key Assertions |
|------|-----------|----------------|
| Alembic migration | Unit (offline) | upgrade/downgrade without errors |
| `IngestPayload` | Unit | New fields accepted, old payloads still valid |
| Ingest router | Unit (mock DB) | New fields persisted to `MetricsEvent` |
| `MetricsRepository.total_tokens()` | Unit (mock session) | Correct aggregation SQL |
| `PricingService.estimate_cost()` | Unit | Real-token path vs. fallback path |
| `MetricsService` | Unit | Passes token data to pricing |
| Hook script `_extract_command()` | Unit (standalone) | Parses `/specify`, `/design`, no-command, missing file |
| Hook script `_extract_workspace()` | Unit (standalone) | Extracts first root, handles empty/missing |
| Hook script full payload | Unit | All Cursor fields mapped correctly |
| Backward compat | Integration | Old payload (no tokens) still returns 202 |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Alembic migration on production data | Low | Medium | All columns nullable, no data transformation |
| Transcript file unreadable | Medium | Low | Graceful fallback to `None` for command/skill |
| Hook script slower due to transcript read | Low | Low | 50-line cap, non-blocking to Cursor |
| Old hook clients send incomplete payloads | Expected | None | All new fields default to `None` |

---

## Decisions

| Decision | Rationale |
|----------|-----------|
| Single migration for all changes | All columns are additive/nullable — no multi-step needed |
| Cache write tokens tracked but not priced | Per user decision — stored for future analysis |
| Command mapping embedded in hook script | Simplest approach — no external config to manage |
| 50-line transcript read limit | Command is always in the first user message — no need to read entire file |
| `workspace` stores first `workspace_roots` entry | Multi-root workspaces are rare; first is the primary project |
