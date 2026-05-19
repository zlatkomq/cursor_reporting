# Figma Design Reference

## Source File

- **File Key:** `YJ1zG32GEYfQcJHG6pFQtV`
- **Figma URL:** https://www.figma.com/design/YJ1zG32GEYfQcJHG6pFQtV/Untitled

## Frames

| Frame | Node ID | Description | Reference PNG |
|-------|---------|-------------|---------------|
| Dark Admin Dashboard (Overview) | `1:2` | Overview tab — stat cards, charts, activity table | `assets/overview-tab-2x.png` |
| Dark Admin Dashboard (Funnel) | `2:2` | Workflow Funnel tab — funnel bars, stage selector, project list | `assets/funnel-tab-2x.png` |

## Design Tokens

See `assets/design-tokens.css` for the full CSS variables block.

### Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-bg-primary` | `#0a0a0a` | Page background, card backgrounds |
| `--color-bg-active` | `#171717` | Active button text color |
| `--color-border` | `#262626` | Card borders, table dividers, inactive buttons |
| `--color-surface` | `#fafafa` | Active button bg, metric icon bg, model badges |
| `--color-white` | `#ffffff` | Text on colored bars |
| `--color-text-secondary` | `#a1a1a1` | Labels, descriptions, secondary text |
| `--color-green-bright` | `#05df72` | Trend text, conversion rate percentage |
| `--color-red` | `#ff6467` | Drop-off labels, blocked count |
| `--color-purple-funnel` | `#ad46ff` | Spec stage bar |
| `--color-blue` | `#2b7fff` | Design stage bar, "In Progress" badge bg |
| `--color-blue-light` | `#51a2ff` | "In Progress" badge text |
| `--color-cyan` | `#00b8db` | Tasks stage bar |
| `--color-green` | `#00c950` | Implement stage bar |
| `--color-amber` | `#f0b100` | "Review" badge bg |
| `--color-amber-light` | `#fdc700` | "Review" badge text |
| `--color-purple` | `#8b5cf6` | Chart area fill (overview) |

### Typography

| Family | Weight | Size | Line Height | Usage |
|--------|--------|------|-------------|-------|
| Arimo | 700 | 24px | 32px | Page title "AI Usage Dashboard" |
| Arimo | 700 | 30px | 36px | Metric card values (2.4M, $4,832, etc.) |
| Arimo | 700 | 20px | 28px | Conversion rate percentage |
| Arimo | 700 | 14px | 20px | Project counts in funnel |
| Arimo | 400 | 18px | 27px | Section headings (chart titles, "Select Stage") |
| Arimo | 400 | 16px | 24px | Body text, button labels, project names |
| Arimo | 400 | 14px | 20px | Card labels, table cells, stage labels |
| Arimo | 400 | 12px | 16px | Badges, drop-off text, small labels |
| Inter | 400 | 12px | 15px | Chart axis labels |
| Liberation Mono | 400 | 12px | 16px | Spec IDs (SPEC-001) |

### Layout Constants

| Element | Value |
|---------|-------|
| Page max width | 1280px (centered with ~132px side padding) |
| Content padding | 32px top, 24px sides |
| Card border-radius | 10px |
| Badge border-radius | 8px |
| Card border | 1px solid `#262626` |
| Section gap | 32px |
| Card internal padding | ~25px |
| Tab button gap | 8px |
| Tab button height | 40px |
| Metric card height | 138px |
| Metric card width | 290px |
| Metric icon container | 44x44px |
| Funnel bar height | 48px |
| Funnel stage gap | 16px |

## Exported SVG Assets

### Overview Tab Icons (`assets/icons/overview/`)

| File | Figma Node | Description |
|------|-----------|-------------|
| `tab-overview-icon.svg` | `1:13` | Grid icon for Overview tab button |
| `tab-funnel-icon.svg` | `1:20` | Funnel icon for Workflow Funnel tab button |
| `metric-total-tokens-bg.svg` | `1:34` | Icon container bg for Total Tokens card |
| `metric-total-tokens-icon.svg` | `1:35` | Chart icon for Total Tokens |
| `metric-total-cost-bg.svg` | `1:43` | Icon container bg for Total Cost card |
| `metric-total-cost-icon.svg` | `1:44` | Dollar icon for Total Cost |
| `metric-avg-response-bg.svg` | `1:53` | Icon container bg for Avg Response Time card |
| `metric-avg-response-icon.svg` | `1:54` | Clock icon for Avg Response Time |
| `metric-api-requests-bg.svg` | `1:63` | Icon container bg for API Requests card |
| `metric-api-requests-icon.svg` | `1:64` | Grid icon for API Requests |

### Funnel Tab Icons (`assets/icons/funnel/`)

| File | Figma Node | Description |
|------|-----------|-------------|
| `tab-overview-icon.svg` | `2:13` | Grid icon for Overview tab (inactive state) |
| `tab-funnel-icon.svg` | `2:20` | Funnel icon for Workflow Funnel tab (active state) |
| `stage-spec-label.svg` | `2:37` | "Spec →" label with arrow |
| `stage-spec-arrow.svg` | `2:40` | Arrow icon for Spec stage |
| `stage-design-label.svg` | `2:56` | "Design →" label with arrow |
| `stage-design-arrow.svg` | `2:59` | Arrow icon for Design stage |
| `stage-design-stats.svg` | `2:62` | "79% 98 projects" stats |
| `stage-tasks-label.svg` | `2:75` | "Tasks →" label with arrow |
| `stage-tasks-arrow.svg` | `2:78` | Arrow icon for Tasks stage |
| `stage-tasks-stats.svg` | `2:81` | "61% 76 projects" stats |
| `stage-implement-stats.svg` | `2:96` | "42% 52 projects" stats |
| `stat-active-projects-icon.svg` | `2:129` | Trend icon for Active Projects card |
| `stat-avg-time-icon.svg` | `2:140` | Clock icon for Avg Time in Stage card |
| `stat-blocked-icon.svg` | `2:149` | Alert icon for Blocked card |

## Component Structure

### Overview Tab (Frame `1:2`)
```
Header (border-bottom)
├── Title: "AI Usage Dashboard" (24px bold)
├── Subtitle: "Monitor your firm's AI token consumption and costs"
└── Tabs: [Overview (active)] [Workflow Funnel]

Content (32px gap between sections)
├── MetricCards row (4x cards, space-between)
│   ├── Total Tokens — value + trend% + icon
│   ├── Total Cost — value + trend% + icon
│   ├── Avg Response Time — value + trend + icon
│   └── API Requests — value + trend% + icon
├── Charts row (2 side-by-side, 604px each)
│   ├── UsageChart — "Token Usage Over Time" (line/area, purple)
│   └── ModelDistribution — "Model Distribution" (bar, purple)
└── UsageTable — "Recent Activity"
    └── Columns: Date | Model (badge) | Tokens | Cost | Duration
```

### Workflow Funnel Tab (Frame `2:2`)
```
Header (same as Overview, Funnel tab active)

Content (32px gap between sections)
├── Main row (funnel + selector side-by-side)
│   ├── WorkflowFunnel card (813px)
│   │   ├── Title: "Workflow Funnel"
│   │   ├── Subtitle: "Track projects through your framework stages"
│   │   ├── 4 funnel bars:
│   │   │   ├── Spec:      124 (100%) — purple (#ad46ff)
│   │   │   ├── Design:     98 (79%, -26 drop-off) — blue (#2b7fff)
│   │   │   ├── Tasks:      76 (61%, -22 drop-off) — cyan (#00b8db)
│   │   │   └── Implement:  52 (42%, -24 drop-off) — green (#00c950)
│   │   └── Conversion Rate: 42% — "52 of 124 projects successfully implemented"
│   └── Stage Selector card (395px)
│       ├── Title: "Select Stage"
│       └── 4 buttons: [Spec (active)] [Design] [Tasks] [Implement]
└── StageDetails
    ├── 3 stat cards (400px each)
    │   ├── Active Projects: 32 "of 124 total"
    │   ├── Avg Time in Stage: "2.3 days"
    │   └── Blocked: 5 (red) "requiring attention"
    └── Projects table: "Recent Projects in {Stage}"
        └── Rows: SPEC-ID | Status badge | Project name | Time in stage
```
