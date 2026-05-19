# Specification

## Metadata

| Field | Value |
|-------|-------|
| ID | 005 |
| Name | Dashboard Redesign — Two-Tab Layout with Workflow Funnel |
| Type | Feature |
| Status | APPROVED |
| Author | PO / AI-assisted |
| Date | 2026-05-14 |
| Approved By | PO |
| Approval Date | 2026-05-15 |
| Jira Ticket | |

---

## Overview

The existing dashboard has four separate pages (Overview, By Developer, By Model, By Command) with independent sidebar navigation. This spec replaces that with a single-page, two-tab layout — an **Overview** tab consolidating metrics visualizations, and a **Workflow Funnel** tab tracking specs through framework stages (Spec → Design → UIX → Tasks → Implement → Review). The redesign follows the approved Figma dark admin dashboard design.

---

## User Stories

- As a **team lead**, I want to see all key AI metrics (tokens, cost, response time, request count) with trend indicators on a single Overview tab, so that I can assess usage at a glance without switching pages.
- As a **team lead**, I want a Workflow Funnel tab that shows how many specs are at each framework stage (Spec → Design → UIX → Tasks → Implement → Review) with drop-off rates, so that I can identify bottlenecks in the development pipeline.
- As a **project manager**, I want to click a funnel stage and see the individual specs in that stage with their status and time-in-stage, so that I can act on blocked or stale items.
- As a **dashboard user**, I want to switch between Overview and Workflow Funnel via top-level tabs instead of navigating separate sidebar pages, so that the experience is faster and more cohesive.

---

## Acceptance Criteria

### Tab Layout

- [ ] Given the dashboard loads, when the user sees the page header, then a subtitle "Monitor your firm's AI token consumption and costs" is displayed, followed by two tab buttons: "Overview" (with grid icon) and "Workflow Funnel" (with funnel icon).
- [ ] Given the user clicks a tab, when the tab switches, then the content area swaps without a full page reload (HTMX partial swap).

### Overview Tab

- [ ] Given the Overview tab is active, when the user views the stat cards row, then four cards are shown: **Total Tokens** (with chart icon, green trend %), **Total Cost** (with dollar icon, green trend %), **Avg Response Time** (with clock icon, trend delta), **API Requests** (with grid icon, green trend %).
- [ ] Given the Overview tab is active, when the user views the charts section, then two charts appear side by side: a **line/area chart** of token usage over time (left) and a **bar chart** of usage broken down by model (right), both in purple/blue accent on dark background.
- [ ] Given the Overview tab is active, when the user scrolls below the charts, then a **data table** is shown with columns: Date, Model (as colored badge/pill), Tokens, Cost, Duration — listing recent individual events.

### Workflow Funnel Tab

- [ ] Given the Workflow Funnel tab is active, when the funnel visualization renders, then it shows six horizontal bars representing framework stages: **Spec**, **Design**, **UIX**, **Tasks**, **Implement**, **Review**, each with its own colour, the count of specs at that stage, and the percentage relative to the first stage.
- [ ] Given the funnel renders, when drop-off occurs between stages, then a red "−N drop-off" label is shown between bars, and arrows (→) connect each stage to the next.
- [ ] Given the funnel renders, when the bottom of the funnel section is visible, then an "Overall Conversion Rate" line shows the percentage and count (e.g., "52 of 124 projects successfully implemented").
- [ ] Given the funnel is displayed, when the user views the right-side panel, then a vertical stage selector lists all stages (Spec, Design, UIX, Tasks, Implement, Review), with the selected stage highlighted.
- [ ] Given the user clicks a stage in the right-side selector, when the selection changes, then the bottom table filters to show only specs in that stage.
- [ ] Given the Workflow Funnel tab is active, when the user views the stat cards below the funnel, then three cards are shown: **Active Projects** (count "of N total"), **Avg Time in Stage**, and **Blocked** (count in red, "requiring attention").
- [ ] Given the Workflow Funnel tab is active, when the user views the bottom table, then each row shows: Spec ID (e.g., SPEC-001), Status badge (color-coded: "In Progress", "Review", etc.), and Time in stage (e.g., "1.2 days").

### Visual Design

- [ ] Given the dashboard renders, when comparing to the Figma exports (`Dark Admin Dashboard.png` and `Dark Admin Dashboard_.png`), then the color palette (dark background, purple/blue/cyan/green accents, green trend text, red drop-off text), card border styling, typography hierarchy, and spacing match the reference designs.
- [ ] Given the dashboard is viewed on screens narrower than 1024px, when the layout responds, then content remains usable without horizontal scrolling.

---

## Scope

**In Scope:**
- Replace four-page sidebar navigation with a two-tab single-page layout (Overview + Workflow Funnel)
- Overview tab: 4 stat cards with icons and trend %, dual side-by-side charts (line + bar), data table with model badges
- Workflow Funnel tab: horizontal bar funnel visualization with drop-off indicators, stage selector panel, 3 summary stat cards, filtered spec list table
- Updated Jinja2 templates, inline CSS, and HTMX interactions for tab switching
- Mapping existing metrics data (tokens, cost, duration, events, models) to the Overview tab
- New data source/query for framework stage tracking (counting specs at each stage) for the Workflow Funnel tab

**Out of Scope:**
- Changes to the ingest API or hook telemetry payloads
- Authentication or login page redesign
- Mobile-first responsive design beyond basic usability at 1024px
- Automated spec stage detection from filesystem (manual or simple database tracking is acceptable for v1)
- Sidebar removal — sidebar may remain but should reflect the simplified two-tab model

---

## Dependencies

- Figma design reference: `specs/005-dashboard-redesign/Dark Admin Dashboard.png` (Overview tab)
- Figma design reference: `specs/005-dashboard-redesign/Dark Admin Dashboard_.png` (Workflow Funnel tab)

---

## Open Questions

None — all resolved.

---

## Decisions Made

| Question | Decision |
|----------|----------|
| How many pages should the dashboard have? | Single page with two tabs: Overview and Workflow Funnel |
| What replaces the four separate sidebar navigation pages? | Overview tab consolidates stat cards, charts, and data table; Workflow Funnel tab replaces per-step CTAs with a unified funnel |
| What funnel step display format to use? | Horizontal bar funnel with counts, percentages, drop-off labels, and a right-side stage selector (per Figma design 2) |
| How are the four current views grouped? | Model + Developer + Command data merged into Overview charts and table; Workflow stages are a new Funnel view |
| Should sidebar nav be updated? | Yes, reflect two-tab model instead of four separate pages |
| How should spec stage data be sourced? | Track stages in the database via a new `workflow_projects` table — filesystem scanning is fragile and out of scope for v1 |
| How should trend percentages be calculated? | Compare to previous equivalent period (e.g., last 30 days vs prior 30 days) |
| What statuses appear as badges in the Funnel table? | DRAFT, IN PROGRESS, REVIEW, APPROVED, BLOCKED |

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
