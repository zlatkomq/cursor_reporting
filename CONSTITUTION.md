# Project Constitution

## Metadata

| Field | Value |
|-------|-------|
| Project Name | cursor-metrics |
| Project Type | GREENFIELD |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-11 |

---

## Overview

An internal metrics collection API deployed on company infrastructure that receives telemetry data (tokens, model, price, duration) from developer Cursor IDE sessions via Cursor Hooks. Each developer's Cursor automatically sends data in the background when an AI milestone completes. A reporting dashboard with basic login provides visibility into AI usage and costs across the development team.

---

## Tech Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.12 |
| Framework | FastAPI | 0.115 |
| Database | MariaDB (MySQL-compatible) | Infrastructure, port 3306 |
| ORM / Client | SQLAlchemy + aiomysql | 2.x / 0.2.x |
| Testing | pytest | 8.x |
| Linting | ruff | 0.8.x |
| Package Manager | uv | 0.5.x |
| Server | uvicorn | 0.32.x |
| Dashboard | Jinja2 + HTMX | (bundled) |

---

## Commands

| Action | Command |
|--------|---------|
| Run all tests | `uv run pytest` |
| Run single test file | `uv run pytest <file>` |
| Build | N/A (interpreted) |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run mypy src/` |
| Dev server | `uv run uvicorn src.cursor_metrics.main:app --reload` |

---

## Coding Standards

### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Files | snake_case | `metrics_router.py` |
| Functions | snake_case | `get_session_metrics()` |
| Classes | PascalCase | `MetricsService` |
| Variables | snake_case | `total_tokens` |
| Constants | UPPER_SNAKE_CASE | `DATABASE_URL` |
| API endpoints | kebab-case | `/api/v1/session-metrics` |

### File Structure

```
src/
├── cursor_metrics/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app factory
│   ├── config.py               # Settings via pydantic-settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── metrics.py          # Pydantic models for ingest + responses
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ingest.py           # POST endpoint for hook telemetry
│   │   ├── reports.py          # GET endpoints for querying metrics
│   │   ├── auth.py             # Dashboard login
│   │   └── dashboard.py        # Dashboard HTML views
│   ├── services/
│   │   ├── __init__.py
│   │   ├── metrics_service.py  # Aggregation and business logic
│   │   └── pricing_service.py  # Model-to-price mapping
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── metrics_repo.py     # MariaDB queries via SQLAlchemy
│   └── templates/
│       ├── base.html
│       ├── login.html
│       └── dashboard.html
hooks/
├── hooks.json                  # Distributable Cursor hooks config
└── send_metrics.ts             # Bun hook script — POSTs to infra API
tests/
├── conftest.py
├── test_ingest.py
├── test_metrics_service.py
└── test_pricing_service.py
pyproject.toml
.env.example
```

### Patterns to Use

- Repository pattern for all database access via SQLAlchemy
- Dependency Injection via FastAPI `Depends()`
- Pydantic models for all request/response schemas
- Service layer between routers and repositories (OOP classes)
- async/await for all I/O-bound operations
- Fire-and-forget telemetry from hooks (non-blocking to developer workflow)

### Patterns to Avoid

- Direct database calls from routers (always go through repository)
- Global mutable state
- Raw SQL strings without parameterization
- Synchronous blocking calls in async endpoints
- Fat routers — business logic belongs in services
- Any hook logic that blocks or slows down the developer's Cursor session

---

## Error Handling

| Concern | Approach |
|---------|----------|
| Strategy | Raise `HTTPException` for client errors; custom exception classes for domain errors caught by FastAPI exception handlers |
| Logging | `structlog` with JSON output; levels: DEBUG (dev), INFO (prod), ERROR (failures) |
| User-facing errors | JSON: `{"error": "<code>", "detail": "<message>", "timestamp": "<iso>"}` |

---

## Testing Standards

| Requirement | Value |
|-------------|-------|
| Minimum Coverage | 80% |
| Unit Tests Required | YES |
| Integration Tests Required | YES |

### Test File Conventions

- Test files mirror source: `src/cursor_metrics/services/metrics_service.py` → `tests/test_metrics_service.py`
- Use `pytest` fixtures for database session mocking
- Integration tests use a test MariaDB schema or SQLite in-memory fallback
- Prefix test functions with `test_`

---

## API Standards

| Convention | Value |
|------------|-------|
| Style | REST |
| Versioning | URL prefix `/api/v1/` |
| Error Format | `{"error": "<CODE>", "detail": "<message>", "timestamp": "<ISO 8601>"}` |

### Endpoints

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/v1/ingest` | None (internal network) | Receive hook telemetry from developer machines |
| GET | `/api/v1/metrics` | Dashboard session | Query aggregated metrics |
| GET | `/api/v1/metrics/by-developer` | Dashboard session | Metrics grouped by developer |
| GET | `/api/v1/metrics/by-model` | Dashboard session | Metrics grouped by model |
| POST | `/api/v1/auth/login` | None | Dashboard login |
| GET | `/dashboard` | Session cookie | Reporting dashboard |

### Ingest Endpoint Behavior

- Accepts telemetry fire-and-forget — always returns `202 Accepted`
- Identifies developer by `user_email` field (provided automatically by Cursor hooks)
- Validates payload shape, drops malformed requests silently (logs warning)
- No authentication required — endpoint is on internal network only

---

## Security Standards

| Concern | Approach |
|---------|----------|
| Input Validation | Pydantic models validate ingest payloads |
| Ingest Auth | None — internal network trust, endpoint not exposed to public internet |
| Dashboard Auth | Basic login (email/password), JWT session cookie |
| Secrets Handling | Environment variables via `.env` file (never committed), loaded by `pydantic-settings` |

---

## Quality Gates

Before merge, code must pass:

- [ ] All tests pass (`uv run pytest`)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Formatting clean (`uv run ruff format --check .`)
- [ ] Type checking passes (`uv run mypy src/`)
- [ ] Test coverage ≥ 80%
- [ ] No hardcoded secrets or credentials

---

## Cursor Hooks Integration

The project ships a `hooks/` directory distributed to all developers as part of the internal framework. The hook fires in the background after an AI milestone is accepted and POSTs telemetry to the infra endpoint. It must never block or slow down the developer's Cursor session.

### Hook Events Used

| Hook | Trigger | Data Captured |
|------|---------|---------------|
| `stop` | Agent loop completes (milestone accepted) | model, status, loop_count, conversation_id, generation_id, user_email |
| `sessionEnd` | Session lifecycle ends | duration_ms, reason, user_email |

### Developer Identity

Developer is identified by `user_email` — a field Cursor hooks provide automatically in every hook input. No registration or API key needed on the developer side.

### Ingest Payload Schema (POST /api/v1/ingest)

```json
{
  "event_type": "stop | session_end",
  "conversation_id": "string",
  "generation_id": "string",
  "model": "string",
  "user_email": "string",
  "status": "completed | aborted | error",
  "duration_ms": 45000,
  "loop_count": 3,
  "cursor_version": "string",
  "timestamp": "ISO 8601"
}
```

### Pricing Calculation

Token costs are derived server-side using a configurable pricing table mapping model identifiers to per-token rates. The hook sends the model identifier; the server looks up the cost.

---

## Database Schema (MariaDB)

### Tables

| Table | Purpose |
|-------|---------|
| `metrics_events` | Raw telemetry events from all developers |
| `model_pricing` | Configurable model → cost-per-token mapping |
| `dashboard_users` | Dashboard login accounts (email, password_hash) |

### Key Indexes

- `metrics_events(user_email, timestamp)` — per-developer queries
- `metrics_events(model, timestamp)` — per-model aggregation
- `metrics_events(conversation_id)` — session lookups

---

## Deployment

| Concern | Value |
|---------|-------|
| Target | Company infrastructure server |
| MariaDB | Infrastructure instance, port 3306 |
| API port | 8000 (default uvicorn) |
| Process manager | systemd or Docker |
| Network | Internal only — not exposed to public internet |

---

## Open Questions

- [ ] Should the pricing table be pre-seeded with known model rates or configured manually per deployment?
- [ ] Data retention policy: keep all raw events or aggregate/purge after N days?
