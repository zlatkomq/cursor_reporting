# Cursor Metrics

Internal telemetry API for collecting Cursor IDE usage metrics across a development team. Cursor Hooks fire automatically after each agent milestone and POST token, model, cost, and timing data to the API — no manual instrumentation needed.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐         ┌────────────┐
│  Developer Laptop   │         │   Company Infra       │         │            │
│                     │  POST   │                       │         │  MariaDB   │
│  Cursor IDE         │────────▶│  FastAPI  :8000       │────────▶│  :3306     │
│  ~/.cursor/hooks/   │         │                       │         │            │
│                     │         │  Dashboard (Jinja2)   │         └────────────┘
└─────────────────────┘         └──────────────────────┘
```

- **Ingest** — hook fires on agent `stop` / `subagentStop`, POSTs telemetry to `/api/v1/ingest`
- **Storage** — MariaDB; Alembic manages schema migrations automatically on startup
- **Dashboard** — JWT-protected web UI at `/dashboard` with HTMX filters and Chart.js charts

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Framework | FastAPI 0.115 |
| Database | MariaDB 11 (MySQL-compatible) |
| ORM | SQLAlchemy 2.x async + aiomysql |
| Server | uvicorn |
| Dashboard | Jinja2 + HTMX + Chart.js |
| Package manager | uv |
| Containers | Docker Compose |

---

## Quick Start (Docker — recommended)

The fastest way to run the full stack locally. Requires [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/).

### 1. Clone and configure

```bash
git clone git@gitlab.qagency.io:ai/cursor-report.git
cd cursor-report
cp .env.example .env
```

The defaults in `.env.example` work out of the box with Docker Compose — no changes needed for local testing.

### 2. Start the stack

```bash
docker compose up --build
```

This will:
- Build the API image
- Start MariaDB and wait for it to be healthy
- Run `alembic upgrade head` (applies all migrations)
- Start uvicorn on `http://localhost:8000`

### 3. Seed pricing data

Model token rates must be loaded once before cost estimates appear:

```bash
docker compose exec api python -m cursor_metrics seed-pricing
```

### 4. Create a dashboard user

```bash
docker compose exec api python -m cursor_metrics create-user \
  --email you@example.com \
  --password yourpassword
```

### 5. Open the dashboard

Navigate to `http://localhost:8000/dashboard` and log in with the credentials you just created.

---

## Local Dev (without Docker)

Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/). You still need a running MariaDB instance (you can run just the DB container: `docker compose up db -d`).

### Install dependencies

```bash
uv sync
```

### Configure

```bash
cp .env.example .env
# Edit DATABASE_URL to point at localhost instead of the "db" service name:
# DATABASE_URL=mysql+aiomysql://user:password@localhost:3307/cursor_metrics
```

### Run migrations

```bash
uv run alembic upgrade head
```

### Start the server

```bash
uv run uvicorn src.cursor_metrics.main:app --reload
```

### Seed and create a user

```bash
uv run python -m cursor_metrics seed-pricing
uv run python -m cursor_metrics create-user --email you@example.com --password yourpassword
```

---

## Hook Installation (Developer Setup)

Each developer runs the install script once. It copies `send-metrics.py` into `~/.cursor/hooks/` and registers the `stop` and `subagentStop` hooks.

```bash
# Default: POSTs to http://localhost:8000 (for local testing)
./scripts/install-hook.sh

# Production: point at your hosted API
CURSOR_METRICS_URL=https://metrics.example.com ./scripts/install-hook.sh
```

Restart Cursor after installing. The hook will fire automatically on every agent completion — no further setup needed.

### Hook events

| Hook event | Trigger |
|---|---|
| `stop` | Agent loop completes (milestone accepted) |
| `subagentStop` | Subagent within a session completes |

### Verifying the hook works

Events are logged locally before being sent:

```bash
tail -f ~/.cursor/hooks-logs/stop-events.jsonl
```

Each line is a JSON record with the raw Cursor event. If lines appear after an agent run but no rows appear in the DB, the API is unreachable — check `CURSOR_METRICS_URL`.

### Changing the API URL after install

The URL is read from the environment at hook runtime, not baked into the script:

```bash
# Add to ~/.bashrc or ~/.zshrc
export CURSOR_METRICS_URL=https://metrics.example.com
```

---

## API Reference

All `/api/v1/metrics*` endpoints require a `Bearer` token in the `Authorization` header (or a `session` cookie from the dashboard login).

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `GET` | `/` | — | Health check + DB connectivity |
| `POST` | `/api/v1/ingest` | — | Receive hook telemetry |
| `GET` | `/api/v1/metrics` | JWT | Overview aggregates |
| `GET` | `/api/v1/metrics/by-developer` | JWT | Aggregates per developer |
| `GET` | `/api/v1/metrics/by-model` | JWT | Aggregates per model with cost |
| `GET` | `/api/v1/metrics/by-command` | JWT | Aggregates per `/command` |
| `POST` | `/api/v1/auth/login` | — | Obtain JWT token |
| `GET` | `/dashboard` | JWT cookie | Web dashboard |

### Query parameters

`days` — filter window. Accepted values for the JSON API: `7`, `30`, `90`.

### Quick API test with curl

```bash
# Health check
curl http://localhost:8000/

# Get a token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"yourpassword"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Overview metrics — last 30 days
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/metrics?days=30"

# By model — last 7 days
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/metrics/by-model?days=7"

# By developer — last 90 days
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/metrics/by-developer?days=90"

# Manual ingest (for testing)
curl -X POST http://localhost:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "stop",
    "conversation_id": "test-001",
    "generation_id": "gen-001",
    "model": "claude-opus-4-6",
    "user_email": "you@example.com",
    "status": "completed",
    "input_tokens": 5000,
    "output_tokens": 800
  }'
```

---

## Admin CLI

Both commands run inside the container or locally with `uv run python -m cursor_metrics`.

### `create-user`

Creates a dashboard/API login account.

```bash
# Docker
docker compose exec api python -m cursor_metrics create-user \
  --email alice@example.com --password secret123

# Local
uv run python -m cursor_metrics create-user \
  --email alice@example.com --password secret123
```

### `seed-pricing`

Loads token pricing for all supported models. Safe to re-run — updates existing rows, inserts new ones.

```bash
# Docker
docker compose exec api python -m cursor_metrics seed-pricing

# Local
uv run python -m cursor_metrics seed-pricing
```

---

## Development

```bash
# Run tests
uv run pytest

# Run tests with output
uv run pytest -v

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/

# Alembic — create a new migration
uv run alembic revision --autogenerate -m "describe the change"

# Alembic — apply migrations
uv run alembic upgrade head

# Alembic — rollback one step
uv run alembic downgrade -1
```

### Interactive API docs

When the server is running, Swagger UI is available at `http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

---

## Changelog

### 2026-05

- **Fix: hook compatibility with Python 3.10** — `send-metrics.py` used `datetime.UTC` (Python 3.11+). Replaced with `timezone.utc` so the hook works on any Python 3.10+ installation.
- Added `subagentStop` hook event and `subagent_type` field to track nested agent calls separately.
- Added `command_name` and `skill_name` extraction from agent transcripts (parses first user message for `/command` syntax).
- Added `/api/v1/metrics/by-command` endpoint and dashboard page.
- Docker Compose: Alembic migrations now run automatically on container startup via `entrypoint.sh`.
