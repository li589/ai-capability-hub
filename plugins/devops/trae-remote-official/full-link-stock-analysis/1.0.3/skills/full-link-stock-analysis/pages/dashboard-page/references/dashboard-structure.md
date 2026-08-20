# Dashboard Structure Reference

Use this reference when planning or modifying the dashboard shell, filters, panel model, or rendered markup.

## Operating Shape

The rendered output should behave like an internal analytics dashboard:

- a sticky top bar with title, data freshness, and primary time controls;
- a constrained but wide workspace around 1180px to 1440px;
- compact KPI tiles near the top, preferably grouped in one outlined strip with internal dividers;
- charts and tables arranged in responsive grids;
- clear panel headings, units, source context, and action menus;
- chart and table data surfaces rendered as thin line-framed modules rather than heavy filled cards;
- no marketing hero, slide canvas, narrative document rail, or card-feed abstractions.

The first viewport should show the dashboard itself, not an explanation of the dashboard.

## Filter Model

The default dashboard must include time selection:

- `range` presets such as 7D, 30D, MTD, QTD, YTD, and All;
- optional explicit start/end dates when the data warrants it;
- visible date coverage and latest refresh timestamp.

Filter controls should operate on a precomputed payload when possible. If a dashboard is too large for full client-side filtering, generate a bounded payload and make the truncation explicit in a visible freshness/source note.

## Block Model

Compose the dashboard with four block kinds:

- `kpi`: compact metric tiles with label, value, unit, delta, comparison basis, sparkline rows, and source context.
- `chart`: ECharts panels rendered as `<section class="dashboard-panel chart-panel">` with panel actions and optional alternate chart types.
- `table`: evidence tables rendered as `<section class="dashboard-panel table-panel">` with stable default sorting.
- `note`: source notes, freshness warnings, caveats, or automation status blocks.

Every block should have a stable `id`. Chart blocks should include chart container id, title, subtitle, unit, allowed chart types, and source key. Table blocks should include table HTML and source context.

## Template Layers

Keep generation layers separate:

- `build_dashboard_blocks(payload)` composes `kpi`, `chart`, `table`, and `note` blocks from analyzed data.
- `render_kpi_block()`, `render_chart_block()`, `render_table_block()`, `render_note_block()`, and `render_dashboard_blocks()` emit the established dashboard markup.
- `build_html(payload)` reads inline assets, calls `build_dashboard_blocks(payload)`, and wraps the final HTML shell.

Dashboard block assembly should not live inside `build_html(payload)`.
