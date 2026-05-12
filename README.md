# Cursor Report

Internal telemetry API for collecting AI Cursor IDE usage metrics across the development team. Receives tokens, model, price, and duration data automatically via Cursor Hooks after each completed AI milestone.

## Architecture

```
┌─────────────────────┐         ┌──────────────────────┐         ┌────────────┐
│  Developer Laptop   │         │   Company Infra      │         │            │
│                     │  POST   │                      │         │  MariaDB   │
│  Cursor IDE         │────────▶│  FastAPI API         │────────▶│  port 3306 │
│  + hooks/           │         │  port 8000           │         │            │
│                     │         │                      │         └────────────┘
└─────────────────────┘         │  Dashboard (Jinja2)  │
                                └──────────────────────┘
```

- **Ingest**: Cursor hooks fire on milestone completion, POST telemetry to `/api/v1/ingest`
- **Storage**: MariaDB on infrastructure, port 3306
- **Dashboard**: Basic-login web UI for viewing usage reports

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.12 |
| Framework | FastAPI 0.115 |
| Database | MariaDB (MySQL-compatible) |
| ORM | SQLAlchemy 2.x + aiomysql |
| Server | uvicorn |
| Dashboard | Jinja2 + HTMX |
| Package Manager | uv |

## Getting Started

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- MariaDB instance (infrastructure, port 3306)

### Installation

```bash
git clone git@gitlab.qagency.io:ai/cursor-report.git
cd cursor-report
uv sync
```

### Configuration

Copy the example env file and fill in your infrastructure values:

```bash
cp .env.example .env
```

Required variables:

```
DATABASE_URL=mysql+aiomysql://user:password@infra-host:3306/cursor_metrics
SECRET_KEY=<your-secret-key>
```

### Running

```bash
uv run uvicorn src.cursor_metrics.main:app --reload
```

The API will be available at `http://localhost:8000` and the dashboard at `http://localhost:8000/dashboard`.

## Developer Setup (Hooks)

Each developer receives the `hooks/` directory as part of the internal framework. The hook automatically sends telemetry in the background — no API keys or registration needed.

The hook identifies developers by `user_email` provided automatically by Cursor.

### Hook Events

| Event | Trigger |
|-------|---------|
| `stop` | Agent loop completes (milestone accepted) |
| `sessionEnd` | Session lifecycle ends |

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/ingest` | Receive hook telemetry (internal network, no auth) |
| GET | `/api/v1/metrics` | Query aggregated metrics |
| GET | `/api/v1/metrics/by-developer` | Metrics grouped by developer |
| GET | `/api/v1/metrics/by-model` | Metrics grouped by model |
| GET | `/dashboard` | Reporting dashboard (basic login) |

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check
uv run mypy src/
```

## Project Status

Active development — greenfield project.
