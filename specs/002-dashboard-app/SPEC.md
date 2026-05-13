# Specification

## Metadata

| Field | Value |
|-------|-------|
| ID | 002 |
| Name | Dashboard Application |
| Type | Feature |
| Status | APPROVED |
| Author | Tech Lead / AI-assisted |
| Date | 2026-05-12 |
| Approved By | Tech Lead |
| Approval Date | 2026-05-12 |
| Jira Ticket | |

---

## Overview

Build an attractive, minimal dashboard for authenticated users to view Cursor IDE usage metrics. The dashboard presents key stats (total events, active developers, model usage, estimated costs) with clean time-series charts and a sidebar navigation — styled after the Cursor usage dashboard (dark theme, clean typography, card-based layout). Authentication uses email/password login with JWT session cookies. The dashboard is server-rendered with Jinja2 templates enhanced by HTMX for interactivity and Chart.js for graphs.

---

## User Stories

- As a **team lead**, I want to log in and see a dashboard with key usage metrics at a glance, so that I can understand how the team is using AI tools without digging through raw data.
- As a **team lead**, I want to see usage broken down by developer and model over time, so that I can identify trends and optimise costs.
- As a **developer**, I want to see my own AI usage stats, so that I can understand my patterns and productivity gains.
- As a **dashboard admin**, I want a simple login page, so that only authorised users can access the metrics.

---

## Acceptance Criteria

- [ ] AC-1: Given an unauthenticated user, when they navigate to `/dashboard`, then they are redirected to `/dashboard/login`.
- [ ] AC-2: Given the login page, when a user enters valid email/password, then they receive a JWT session cookie and are redirected to `/dashboard`.
- [ ] AC-3: Given invalid credentials, when a user submits the login form, then they see an error message on the login page (no redirect).
- [ ] AC-4: Given a logged-in user, when they visit `/dashboard`, then they see a sidebar with navigation links (Overview, By Developer, By Model, Settings) and a main content area.
- [ ] AC-5: Given a logged-in user on the Overview page, when the page loads, then they see four stat cards (Total Events, Active Developers, Top Model, Estimated Cost) with current values.
- [ ] AC-6: Given a logged-in user on the Overview page, when the page loads, then they see a time-series chart showing daily event counts for the past 30 days.
- [ ] AC-7: Given a logged-in user, when they click "By Developer" in the sidebar, then they see a table of developers ranked by event count with usage stats.
- [ ] AC-8: Given a logged-in user, when they click "By Model" in the sidebar, then they see a breakdown of model usage with event counts and estimated costs.
- [ ] AC-9: Given the dashboard pages, when they are rendered, then the design uses a dark theme with clean card-based layout similar to cursor.com/dashboard/usage.
- [ ] AC-10: Given a logged-in user, when they click "Logout" in the sidebar, then the session cookie is cleared and they are redirected to the login page.
- [ ] AC-11: Given the dashboard, when date filters are applied (last 7d, 30d, 90d), then the charts and stats update to reflect the selected period.
- [ ] AC-12: Given a CLI or script, when a `POST /api/v1/auth/login` request is sent with valid credentials, then a JWT token is returned in the response body.

---

## Scope

**In Scope:**

- Login page (`/dashboard/login`) with email/password form
- JWT session cookie authentication (sign, verify, expiry)
- Password hashing with bcrypt via `passlib`
- Dashboard layout with dark-themed sidebar and main content area
- Overview page with 4 stat cards and a daily events line chart
- By Developer page with ranked table
- By Model page with model usage breakdown and cost estimates
- Date range filter (7d / 30d / 90d toggle)
- Logout functionality
- Server-side rendered templates (Jinja2 + HTMX)
- Chart.js for client-side chart rendering
- API endpoints for metrics data (`/api/v1/metrics`, `/api/v1/metrics/by-developer`, `/api/v1/metrics/by-model`)
- Auth API endpoint (`POST /api/v1/auth/login`)
- Alembic migration if schema changes are needed
- Seed script or management command to create an initial dashboard user
- Responsive design (works on 1280px+ screens)

**Out of Scope:**

- User registration (admin creates accounts manually or via seed script)
- Role-based access control (all logged-in users see all data)
- CSV/PDF export
- Real-time WebSocket updates
- Mobile-first responsive layout (desktop focus, usable but not optimised below 1280px)
- Custom date range picker (only preset periods: 7d, 30d, 90d)
- Cursor hooks (`hooks/` directory)

---

## Dependencies

- **SPEC-001** (Docker & FastAPI Application Setup) — provides the FastAPI app, database, Docker infrastructure, ORM models, and stub routers/services/repositories that this spec implements.

---

## Open Questions

None — all questions resolved.

---

## Decisions Made

| Question | Decision |
|----------|----------|
| Authentication method | JWT session cookie with `python-jose` + `passlib[bcrypt]` |
| Frontend rendering | Server-side Jinja2 + HTMX for interactivity (no SPA, no build step) |
| Charting | Chart.js via CDN — lightweight, no bundler needed |
| Design direction | Dark theme, sidebar nav, card-based stats — matching cursor.com/dashboard style |
| Initial user creation | CLI command: `uv run python -m cursor_metrics.cli create-user` |
| Chart library | Chart.js via CDN — no build step needed |
| Default date range | 30 days when dashboard first loads |

---

## Visual Design Direction

The dashboard takes direct inspiration from the Cursor usage analytics page:

- **Dark background** (`#0a0a0f` or similar near-black) with subtle card surfaces (`#141419`)
- **Sidebar** (left, ~240px): logo/project name at top, nav links with icons, logout at bottom
- **Stat cards**: row of 4 across the top, each with label, large value, and subtle trend indicator
- **Charts**: dark-themed Chart.js with accent colour palette (blue/purple/green tones on dark background)
- **Tables**: dark-themed with subtle row hover, no heavy borders
- **Typography**: system font stack, clean headings, muted secondary text (`#888`)
- **Accent colours**: primary blue (`#3b82f6`), success green (`#22c55e`), warning amber (`#f59e0b`)

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
