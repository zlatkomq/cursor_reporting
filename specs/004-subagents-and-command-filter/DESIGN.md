# Design

## Metadata

| Field | Value |
|-------|-------|
| Spec ID | 004 |
| Name | Subagent Tracking & Command Filtering |
| Status | APPROVED |
| Date | 2026-05-13 |

---

## Architecture Overview

Two parallel tracks that converge on the dashboard:

**Track A — Subagent capture:** Add `subagentStop` to the hook config, extend the ingest pipeline with `subagent_type`, and let subagent events flow into the same `metrics_events` table as parent events.

**Track B — Command filtering:** Add a `command` query parameter to all dashboard/API routes, thread it through service → repository, and render a command filter button bar on the dashboard.

```
Track A: Subagent Capture
─────────────────────────
subagentStop event ──→ send-metrics.py ──→ POST /api/v1/ingest
                        (event_type = "subagent_stop")
                        (subagent_type = "generalPurpose")
                        (session_id links to parent)
                              │
                              ▼
                      metrics_events table
                        (new: subagent_type column)

Track B: Command Filtering
──────────────────────────
Dashboard pages ──→ ?command=specify ──→ dashboard router
                                             │
                        ┌────────────────────┘
                        ▼
                  MetricsService.get_overview(days, command)
                        │
                        ▼
                  MetricsRepository.count_events(since, command)
                  MetricsRepository.total_tokens(since, command)
                  ... all queries accept optional command filter
```

---

## Database Changes

### Migration: `003_add_subagent_type.py`

Single column addition:

```python
op.add_column("metrics_events", sa.Column("subagent_type", sa.String(50), nullable=True))
```

Downgrade: `op.drop_column("metrics_events", "subagent_type")`

---

## ORM Model Changes

### `MetricsEvent` (models/db.py)

Add one column:

```python
subagent_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
```

---

## Pydantic Schema Changes

### `IngestPayload` (models/metrics.py)

1. Expand `event_type` Literal:
```python
event_type: Literal["stop", "session_end", "subagent_stop"]
```

2. Add field:
```python
subagent_type: str | None = None
```

---

## Ingest Router Changes

### `routers/ingest.py`

Add `subagent_type=payload.subagent_type` to the `MetricsEvent` constructor. No other logic changes — the endpoint already accepts all event types.

---

## Hook Changes

### `~/.cursor/hooks.json`

Add `subagentStop` entry:

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

### `send-metrics.py` Changes

The script already reads `hook_event_name` and maps it to `event_type`. Changes:

1. Map `"subagentStop"` → `"subagent_stop"` in the event_type mapping
2. Add `subagent_type` to payload from `event.get("subagent_type")`
3. Skip `_extract_command()` when `hook_event_name != "stop"` (subagents don't have their own transcript)
4. All other field mapping stays the same (tokens, session_id, etc.)

```python
event_type_map = {"stop": "stop", "subagentStop": "subagent_stop"}
payload["event_type"] = event_type_map.get(event.get("hook_event_name", "stop"), "stop")
payload["subagent_type"] = event.get("subagent_type")

if event.get("hook_event_name") == "stop":
    command_name, skill_name = _extract_command(event.get("transcript_path"))
    payload["command_name"] = command_name
    payload["skill_name"] = skill_name
```

---

## Repository Changes

### `MetricsRepository` — Add optional `command_name` filter

Every query method gets an optional `command_name: str | None = None` parameter. When provided, an additional WHERE clause is added:

```python
if command_name:
    stmt = stmt.where(MetricsEvent.command_name == command_name)
```

Affected methods:
- `count_events(since, command_name=None)`
- `count_active_developers(since, command_name=None)`
- `top_model(since, command_name=None)`
- `daily_event_counts(since, command_name=None)`
- `events_by_developer(since, command_name=None)`
- `events_by_model(since, command_name=None)`
- `total_tokens(since, command_name=None)`

### New method: `distinct_commands(since)`

```python
async def distinct_commands(self, since: datetime) -> list[str]:
    """Return distinct non-null command_name values for the period."""
    stmt = (
        select(MetricsEvent.command_name)
        .where(MetricsEvent.timestamp >= since, MetricsEvent.command_name.isnot(None))
        .distinct()
        .order_by(MetricsEvent.command_name)
    )
    result = await self._session.execute(stmt)
    return [row[0] for row in result.all()]
```

---

## Service Changes

### `MetricsService`

All methods get an optional `command: str | None = None` parameter and pass it to the repository:

```python
async def get_overview(self, days: int = 30, command: str | None = None) -> dict:
    ...
    total_events = await self._repository.count_events(since, command_name=command)
    ...
```

### New method: `get_available_commands(days)`

```python
async def get_available_commands(self, days: int = 30) -> list[str]:
    since = datetime.utcnow() - timedelta(days=days)
    return await self._repository.distinct_commands(since)
```

---

## Dashboard Router Changes

### All routes — add `command` parameter

```python
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_overview(
    request: Request,
    current_user: str = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
    command: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    service = _build_metrics_service(session)
    overview = await service.get_overview(days, command=command)
    commands = await service.get_available_commands(days)
    ...
    context = {
        ...
        "commands": commands,
        "current_command": command,
    }
```

Same pattern for `/dashboard/by-developer`, `/dashboard/by-model`.

### New route: `/dashboard/by-command`

```python
@router.get("/dashboard/by-command", response_class=HTMLResponse)
async def dashboard_by_command(
    request: Request,
    current_user: str = Depends(get_current_user),
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    service = _build_metrics_service(session)
    data = await service.get_by_command(days)
    ...
```

### Reports API routes — same `command` parameter

All three `/api/v1/metrics*` routes get `command: str | None = Query(default=None)`.

---

## Template Changes

### New partial: `partials/command_filter.html`

Button bar matching the date filter style:

```html
<div class="filter-bar">
    <button
        class="btn{% if not current_command %} active{% endif %}"
        hx-get="{{ filter_url | default('/dashboard') }}?days={{ current_days }}"
        hx-target="#dashboard-content"
        hx-swap="innerHTML"
        hx-push-url="true"
    >All</button>
    {% for cmd in commands %}
    <button
        class="btn{% if current_command == cmd %} active{% endif %}"
        hx-get="{{ filter_url | default('/dashboard') }}?days={{ current_days }}&command={{ cmd }}"
        hx-target="#dashboard-content"
        hx-swap="innerHTML"
        hx-push-url="true"
    >{{ cmd }}</button>
    {% endfor %}
</div>
```

### Updated date filter

The date filter buttons must also preserve the current `command` parameter:

```html
hx-get="{{ filter_url }}?days=7{% if current_command %}&command={{ current_command }}{% endif %}"
```

### Include command filter on all pages

In `dashboard.html`, `by_developer.html`, `by_model.html` — add after date filter:

```html
{% include "partials/command_filter.html" %}
```

### New templates for by-command page

- `by_command.html` — full page
- `partials/by_command_content.html` — HTMX-swappable content

### Sidebar update

Add "By Command" link to `partials/sidebar.html`.

---

## Testing Strategy

| Area | Test Type | Key Assertions |
|------|-----------|----------------|
| Migration 003 | Unit | Upgrade/downgrade without errors |
| `IngestPayload` | Unit | `subagent_stop` event type accepted, `subagent_type` field |
| Ingest router | Unit | subagent_stop payload persisted with subagent_type |
| Hook script | Unit | subagentStop → subagent_stop mapping, subagent_type in payload |
| `distinct_commands()` | Unit (mock) | Returns sorted list of command names |
| Repository command filter | Unit (mock) | Queries include WHERE clause when command provided |
| Service command passthrough | Unit (mock) | Command parameter forwarded to repository |
| Dashboard routes | Unit (mock) | `command` query param accepted, passed to context |
| Command filter template | Unit | Renders buttons for each command, active state correct |
| By-command page | Unit | Route exists, renders without error |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| subagentStop payload differs from guess | Medium | Low | Raw logging captures real events; script handles missing fields gracefully |
| Too many commands for button row | Low | Low | ~7-8 expected; can switch to dropdown later if needed |
| Command filter + date filter interaction | Low | Low | Both are simple query params, HTMX preserves both |
| Subagent events inflate totals | Expected | None | Per user decision — counted in totals |

---

## Decisions

| Decision | Rationale |
|----------|-----------|
| Single migration for one column | Minimal schema change |
| Button row for command filter | 7-8 commands fits well, matches date filter UX |
| Subagents counted in totals | Simpler, reflects true usage volume |
| Log-first for subagentStop | Capture real payloads before over-engineering the mapping |
| Skip command extraction for subagents | Subagents inherit parent context via session_id |
