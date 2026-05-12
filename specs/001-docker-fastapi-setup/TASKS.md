# Task Breakdown

## Metadata

| Field | Value |
|-------|-------|
| ID | 001 |
| Name | Docker & FastAPI Application Setup |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-12 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-12 |
| Jira Ticket | |

---

## Overview

Scaffold the complete cursor-metrics application per DESIGN.md: project config and dependencies first, then configuration layer, database layer with ORM models, Alembic migrations, API layer (app factory + endpoints), stub modules for future specs, Docker containerisation, and finally tests. Tasks are ordered so each builds on the previous — no task depends on something that comes later.

---

## Tasks

- [ ] T1: Create `pyproject.toml` with all dependencies and tool config (DESIGN: Dependencies)
  - Create: `pyproject.toml`
  - Produces: Project metadata, dependency declarations, ruff/pytest/mypy config sections
  - Verify: `uv sync --dry-run` → Expected: resolves all dependencies without errors

- [ ] T2: Create `.env.example` and `src/cursor_metrics/__init__.py` (DESIGN: Architecture)
  - Create: `.env.example`, `src/cursor_metrics/__init__.py`
  - Consumes: T1 (project exists with dependencies)
  - Produces: `__version__ = "0.1.0"` in package init; documented env var template
  - Verify: `python -c "from src.cursor_metrics import __version__; print(__version__)"` → Expected: `0.1.0`

- [ ] T3: Create `Settings` configuration class (DESIGN: Architecture — config.py)
  - Create: `src/cursor_metrics/config.py`
  - Consumes: T2 (`.env.example` for variable names)
  - Produces: `Settings` class with `DATABASE_URL`, `SECRET_KEY`, `APP_VERSION` fields; `get_settings()` dependency
  - Verify: Run tests for Settings → Expected: PASS

- [ ] T4: Create SQLAlchemy async engine and session management (DESIGN: Architecture — database.py)
  - Create: `src/cursor_metrics/database.py`
  - Consumes: T3.Settings (`DATABASE_URL`)
  - Produces: `async_engine`, `AsyncSessionLocal`, `get_db()` async dependency, `Base` declarative base
  - Verify: Run tests for database module → Expected: PASS

- [ ] T5: Create SQLAlchemy ORM table definitions (DESIGN: Data Model)
  - Create: `src/cursor_metrics/models/db.py`, `src/cursor_metrics/models/__init__.py`
  - Consumes: T4.Base (DeclarativeBase)
  - Produces: `MetricsEvent`, `ModelPricing`, `DashboardUser` ORM models with all columns, constraints, and indexes per DESIGN.md Data Model section
  - Verify: `python -c "from src.cursor_metrics.models.db import MetricsEvent, ModelPricing, DashboardUser; print('OK')"` → Expected: `OK`

- [ ] T6: Create Pydantic request/response schemas (DESIGN: API / Interfaces)
  - Create: `src/cursor_metrics/models/metrics.py`
  - Produces: `IngestPayload` Pydantic model (telemetry fields per CONSTITUTION), `HealthCheckResponse` model (status, version, database)
  - Verify: `python -c "from src.cursor_metrics.models.metrics import IngestPayload, HealthCheckResponse; print('OK')"` → Expected: `OK`

- [ ] T7: Set up Alembic configuration and initial migration (DESIGN: Architecture — alembic)
  - Create: `alembic.ini`, `alembic/env.py`, `alembic/script.mako`, `alembic/versions/001_initial_schema.py`
  - Consumes: T4 (async engine config), T5 (ORM metadata for autogenerate)
  - Produces: Alembic config with async runner; initial migration creating `metrics_events`, `model_pricing`, `dashboard_users` tables
  - Verify: `alembic check` → Expected: no pending migrations (head matches)

- [ ] T8: Create FastAPI app factory with health-check endpoint (DESIGN: Architecture — main.py, API / Interfaces)
  - Create: `src/cursor_metrics/main.py`
  - Consumes: T3.Settings, T4 (engine for DB connectivity check)
  - Produces: `app` FastAPI instance with lifespan handler; `GET /` returning `HealthCheckResponse` (status, version, database connectivity)
  - Verify: Run tests for health endpoint → Expected: PASS

- [ ] T9: Create stub ingest router (DESIGN: Architecture — routers/ingest.py)
  - Create: `src/cursor_metrics/routers/__init__.py`, `src/cursor_metrics/routers/ingest.py`
  - Consumes: T6.IngestPayload (Pydantic validation), T8.app (router registration)
  - Produces: `POST /api/v1/ingest` endpoint returning 202 Accepted
  - Verify: Run tests for ingest endpoint → Expected: PASS

- [ ] T10: Create stub service and repository classes (DESIGN: Architecture — services, repositories)
  - Create: `src/cursor_metrics/services/__init__.py`, `src/cursor_metrics/services/metrics_service.py`, `src/cursor_metrics/services/pricing_service.py`, `src/cursor_metrics/repositories/__init__.py`, `src/cursor_metrics/repositories/metrics_repo.py`
  - Produces: `MetricsService` class, `PricingService` class, `MetricsRepository` class — all OOP stubs with docstrings, no business logic
  - Verify: `python -c "from src.cursor_metrics.services.metrics_service import MetricsService; from src.cursor_metrics.services.pricing_service import PricingService; from src.cursor_metrics.repositories.metrics_repo import MetricsRepository; print('OK')"` → Expected: `OK`

- [ ] T11: Create stub router placeholders and Jinja2 base template (DESIGN: Architecture — routers, templates)
  - Create: `src/cursor_metrics/routers/reports.py`, `src/cursor_metrics/routers/auth.py`, `src/cursor_metrics/routers/dashboard.py`, `src/cursor_metrics/templates/base.html`
  - Produces: Empty router modules (importable, no routes yet); Jinja2 base HTML layout
  - Verify: `python -c "from src.cursor_metrics.routers import reports, auth, dashboard; print('OK')"` → Expected: `OK`

- [ ] T12: Create multi-stage Dockerfile (DESIGN: Architecture — Dockerfile)
  - Create: `Dockerfile`
  - Consumes: T1 (pyproject.toml for dependency install)
  - Produces: Multi-stage Dockerfile — build stage with `uv` for dependency resolution, slim Python 3.12 runtime stage with uvicorn entrypoint
  - Verify: `docker build -t cursor-metrics:test .` → Expected: build succeeds, image created

- [ ] T13: Create `docker-compose.yml` with API and MariaDB services (DESIGN: Architecture — docker-compose.yml)
  - Create: `docker-compose.yml`
  - Consumes: T12 (Dockerfile for API image)
  - Produces: Compose file with `api` service (port 8000, env_file, depends_on db), `db` service (MariaDB, port 3306, named volume `mariadb_data`), healthcheck for db
  - Verify: `docker compose config` → Expected: valid configuration, no errors

- [ ] T14: Create test fixtures and conftest (DESIGN: Architecture — tests)
  - Create: `tests/__init__.py`, `tests/conftest.py`
  - Consumes: T8.app (FastAPI test client), T4 (session override for test DB)
  - Produces: `async_client` fixture (httpx AsyncClient), test settings override, `conftest.py` with pytest-asyncio config
  - Verify: `uv run pytest --co` → Expected: collection succeeds, no errors

- [ ] T15: Unit tests for health-check endpoint (DESIGN: Architecture — tests/test_health.py)
  - Create: `tests/test_health.py`
  - Consumes: T14 (async_client fixture), T8 (health endpoint)
  - Verify: `uv run pytest tests/test_health.py -v` → Expected: PASS (at least 2 tests — OK response, response schema shape)

- [ ] T16: Unit tests for stub ingest endpoint (DESIGN: Architecture — tests/test_ingest.py)
  - Create: `tests/test_ingest.py`
  - Consumes: T14 (async_client fixture), T9 (ingest endpoint)
  - Verify: `uv run pytest tests/test_ingest.py -v` → Expected: PASS (at least 3 tests — valid payload 202, invalid payload 422, missing fields 422)

- [ ] T17: Integration test — Docker Compose full stack (DESIGN: Architecture)
  - Create: `tests/test_integration.py`
  - Consumes: T13 (docker-compose.yml), T8 (health endpoint), T9 (ingest endpoint)
  - Verify: `docker compose up -d && sleep 5 && curl -s http://localhost:8000/ | python -m json.tool && docker compose down` → Expected: health-check JSON with `"status": "ok"`

- [ ] T18: Verify linting and formatting compliance (DESIGN: Dependencies — ruff config)
  - Verify: `uv run ruff check . && uv run ruff format --check .` → Expected: zero errors, zero formatting issues

---

## Testing

- [ ] T15: Unit tests for health-check endpoint
- [ ] T16: Unit tests for stub ingest endpoint
- [ ] T17: Integration test — Docker Compose full stack smoke test (multi-component: API + DB + Docker)

---

## Previous Spec Learnings

First spec — no previous learnings available.

---

## References

- DESIGN.md#Architecture — component table, Mermaid diagram
- DESIGN.md#Data Model — all table definitions, columns, indexes
- DESIGN.md#API / Interfaces — health-check response schema, ingest endpoint contract
- DESIGN.md#Dependencies — full package list with versions
- DESIGN.md#Acceptance Criteria Traceability — AC-to-component mapping
- CONSTITUTION.md#File Structure — canonical package layout
- CONSTITUTION.md#Coding Standards — naming, patterns to use/avoid
- CONSTITUTION.md#Ingest Payload Schema — telemetry JSON shape

---

## Definition of Done

- [ ] All tasks completed (T1–T18)
- [ ] All tests passing (`uv run pytest`)
- [ ] Linting clean (`uv run ruff check .`)
- [ ] Formatting clean (`uv run ruff format --check .`)
- [ ] Test coverage meets CONSTITUTION.md threshold (≥ 80%)
- [ ] Docker Compose stack starts and health-check responds
- [ ] No open questions remaining
