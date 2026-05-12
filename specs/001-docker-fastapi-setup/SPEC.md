# Specification

## Metadata

| Field | Value |
|-------|-------|
| ID | 001 |
| Name | Docker & FastAPI Application Setup |
| Type | Infrastructure |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-12 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-12 |
| Jira Ticket | |

---

## Overview

Set up the full cursor-metrics application with Docker containerisation and FastAPI scaffolding so the project can be developed, tested, and deployed from a single `docker compose` command. This establishes the foundational infrastructure that all subsequent features build on.

---

## User Stories

- As a **backend developer**, I want to run the entire application stack locally with one command, so that I can start contributing without manually provisioning a database or configuring services.
- As a **DevOps engineer**, I want a production-ready Docker image for the API, so that I can deploy the service on company infrastructure consistently and repeatably.
- As a **team lead**, I want the project scaffolded with the agreed file structure and coding patterns, so that all future specs build on a consistent, well-organised codebase.

---

## Acceptance Criteria

- [ ] Given a fresh clone of the repository, when a developer runs `docker compose up`, then the FastAPI application starts and responds to `GET /` with a health-check response.
- [ ] Given the Docker Compose stack is running, when the application starts, then it connects to a MariaDB instance on port 3306 and Alembic migrations can be run to create the initial schema.
- [ ] Given the application is running, when a developer sends a `POST` to `/api/v1/ingest` with a valid telemetry payload, then the endpoint returns `202 Accepted`.
- [ ] Given the application is running, when a developer navigates to `/docs`, then the auto-generated FastAPI OpenAPI documentation is accessible.
- [ ] Given the full project file structure as defined in the constitution, when a developer inspects the `src/` directory, then all expected packages, modules, and placeholder files are present.
- [ ] Given the Docker Compose configuration, when the stack is started, then environment variables are loaded from a `.env` file and the application reads them via pydantic-settings.
- [ ] Given the project is set up, when a developer runs `uv run pytest`, then the test suite executes successfully (initial placeholder tests pass).
- [ ] Given the project is set up, when a developer runs `uv run ruff check .` and `uv run ruff format --check .`, then linting and formatting pass with zero errors.
- [ ] Given the Dockerfile, when the image is built, then it produces a minimal production image that runs the API via uvicorn without development dependencies.

---

## Scope

**In Scope:**
- Dockerfile for the FastAPI application (multi-stage, production-ready)
- `docker-compose.yml` with API service and MariaDB service
- `.env.example` with all required environment variables documented
- Full `src/cursor_metrics/` package scaffolding (main, config, models, routers, services, repositories, templates)
- Database connection setup with SQLAlchemy async engine and session management
- Alembic migration setup with initial migration for the MariaDB schema (metrics_events, model_pricing, dashboard_users tables)
- Health-check endpoint at `GET /`
- Stub ingest endpoint at `POST /api/v1/ingest` returning 202
- `pyproject.toml` with all dependencies and tool configuration (ruff, pytest, mypy)
- Initial placeholder tests and `conftest.py`
- Jinja2 template directory with base template

**Out of Scope:**
- Full business logic for metrics aggregation or pricing calculation
- Dashboard UI implementation (login, reports, charts)
- Cursor hooks (`hooks/` directory and hook scripts)
- CI/CD pipeline configuration
- Production deployment scripts or systemd service files
- JWT authentication or session management for the dashboard
- Data seeding beyond initial schema

---

## Dependencies

- None — this is the foundational spec; all other specs depend on it.

---

## Open Questions

None — all questions resolved.

---

## Decisions Made

| Question | Decision |
|----------|----------|
| MariaDB data persistence in Docker Compose? | Yes — include a named volume mount for MariaDB data so local dev data survives container restarts |
| Schema management approach? | Use Alembic migrations from day one — no `create_all` on startup |
| Health-check response detail? | Medium — return OK status plus app version and database connectivity status (no full build metadata) |

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
