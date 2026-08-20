# Visual Interactions Reference

Use this reference when changing dashboard styling, controls, panel actions, or Data Source modal behavior.

## Visual Defaults

Preserve these defaults unless the user explicitly asks for a redesign:

- calm system UI font stack using `-apple-system`, BlinkMacSystemFont, Segoe UI, Helvetica Neue, and Arial;
- dense but breathable layouts built for scanning;
- a white paper-like page rather than a tinted app canvas;
- a restrained neutral shell; chart colors may be more saturated than UI chrome when they carry categorical meaning;
- no decorative gradients, orbs, bokeh, oversized heroes, or marketing sections;
- line-first framing: charts and tables should read as thin outlined modules, while KPI tiles should use separate bordered cards for fast scanning;
- chart and table panels should keep their outer shell mostly unfilled, with the data surface itself carrying the border;
- KPI tiles should be separate cards with grid gaps, their own thin border, and a modest radius; do not place all KPI tiles inside one large grouped card with internal divider lines;
- panel actions should stay visually quiet and may appear on hover/focus;
- 8px to 16px radius following local report conventions, with chart/table surfaces closer to the report figure style;
- sticky top controls with clear focus and hover states;
- avoid showing the same time range twice; if explicit start/end date inputs are visible, hide any generated active-range text label;
- stable panel dimensions so chart loading, hover states, and filter changes do not shift the layout;
- mobile layout should preserve control usability and avoid text overlap.

## Layout Planning

Use a 12-column panel grid and plan the reading order before writing markup. Block counts and spans are not fixed. Prefer deterministic layout inference over ad hoc sizing:

```text
KPI tiles: independent cards in the KPI grid, not panel-grid spans
Charts: inferred as span 6 for ordinary charts, span 12 for dense charts, scatter/heatmap views, or many-category views
Tables: inferred as span 6 for compact tables, span 12 for wide tables with many columns or long text fields
Notes and definitions: inferred as span 6, or span 4 only when marked compact
Mobile: all panel-grid blocks collapse to full width
```

Dashboard blocks may omit `span`. The renderer should infer `data-span` from block kind and content metadata. Use explicit `span: 4`, `span: 6`, or `span: 12` only as an override when the analytical layout needs it. Do not use `span: 4` for tables unless the table has only two or three short columns and no wrapped text.

## Theme System

Dashboards should ship with the built-in theme switcher unless the user explicitly asks for a single fixed theme. Keep `Light` as the default theme and offer `Dark` as an icon-only theme choice in the top controls.

Theme values are fixed design-system tokens, not suggestions. Do not invent new light or dark colors unless the user explicitly asks for a redesign.

The Light theme uses these exact core tokens:

```text
text primary / --ink #2f3437
text secondary / --muted #68707a
text faint / --faint #8b95a3
border / --line #e1e5ea
strong border / --line-strong #cbd3dc
page #ffffff
panel/surface #FAFAFA
soft fill / --soft #f2f3f5
soft blue / --soft-blue #f3f6fb
control background rgba(255, 255, 255, 0.94)
topbar background rgba(255, 255, 255, 0.96)
menu/modal background #ffffff
table head #FAFAFA
table hover #f1f2ff
chart background #FAFAFA
brand / emphasis #6979F8
brand hover / emphasis middle #9EA9FF
brand end / emphasis pale #CDD2FD
brand text #ffffff
accent #2F6BFF
accent 2 #00BFA6
```

The Light chart tokens are also fixed:

```text
chart text #2f3437
chart muted #68707a
chart line #e1e5ea
chart primary #2F6BFF
chart secondary #00BFA6
chart tertiary #FF7A3D
chart quaternary #F45BB3
chart-1 #F45BB3
chart-2 #2F6BFF
chart-3 #00BFA6
chart-4 #FF7A3D
chart-5 #9BD82E
chart-6 #7C3AED
chart-7 #FFD23F
```

The Trae dark theme uses these exact core tokens:

```text
bg/page #0c0c0d
panel #1a1b1d
surface #222427
elevated/menu #202123
border #2a2d31
text primary #f5f9fe
text secondary #d1d3db
text muted #9599a6
brand #32f08c
brand hover #0fdc78
```

The Trae dark chart tokens are also fixed:

```text
chart text #d1d3db
chart muted #9599a6
chart line #2a2d31
chart primary #28d9ff
chart secondary #32f08c
chart tertiary #f6c85f
chart quaternary #ff6b9a
chart-1 #32f08c
chart-2 #28d9ff
chart-3 #a78bfa
chart-4 #f6c85f
chart-5 #ff6b9a
chart-6 #6ea8ff
chart-7 #d1d3db
```

Use stable category-to-token mappings when category names are known, and trim category labels before lookup so trailing spaces do not break color stability. Keep `Other`, `其他`, and missing/unknown buckets in neutral gray such as `#8A94A3` or `#A7ADB6` so they do not compete with primary categories.

Theme colors should be token-driven. Define all surface, text, axis, gridline, and chart series colors as CSS variables in `:root` and `html[data-theme="trae-dark"]`; do not maintain a second parallel JavaScript theme object. Chart factories should read CSS chart tokens with `getComputedStyle(document.documentElement)`, then use semantic tokens such as `--chart-primary`, `--chart-secondary`, `--chart-tertiary`, `--chart-quaternary`, and the fallback `--chart-1` through `--chart-7` palette. Metric trend charts should use these tokens rather than hard-coded one-off colors. A theme switch should update charts immediately without regenerating the dashboard.

## Runtime Behavior

Keep reusable browser behavior in `assets/dashboard_runtime.js`:

- time-range filtering;
- chart initialization and resize handling;
- chart edit menus;
- Data Source modal behavior;
- code copy actions;
- theme switching and chart refresh on theme changes;
- freshness and active range labels.

Change `dashboard_runtime.js` only when the shared dashboard interaction model changes. Keep dashboard-specific chart option builders and source maps in `dashboard_template.py`.

## Control Expectations

Dashboard controls should use familiar UI patterns:

- segmented controls for time presets;
- date inputs for explicit start/end;
- icon-like compact buttons for panel menus when practical;
- toggles or checkboxes for binary settings;
- dropdowns for dimensions with many values.

Do not add visible instructional text explaining how to use basic controls. Labels should identify the control and its current state.

## Panel Actions

Panel menus should include:

- `Edit`, when alternate chart types exist;
- `View Data Source`, for all material charts and tables.

Use the report-style control pattern for chart editing:

- the panel action button is a compact three-dot icon button;
- clicking `Edit` closes the action menu and reveals a small adjacent `Type` select control beside the action button;
- the `Type` select should remain outside the menu so it is not clipped by chart canvases, legends, or panel surfaces;
- switching the chart type should keep the select value synchronized with the active chart state.

The Data Source modal should use the report-style modal structure: a calm white modal, a `modal-head` with title/subtitle, an icon-only close button, and separate source sections such as `Panel transform` and `Analysis logic`. Each source section should wrap code in a light `code-wrap` surface with an icon-only copy button. The modal should open quickly, preserve code formatting, and show analysis and transform logic only, not the dashboard rendering shell.
