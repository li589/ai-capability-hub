# Data And Automation Reference

Use this reference when adapting data pipelines, snapshot schemas, time filtering, or automation handoff.

## Source Discipline

Every visible metric should be traceable to reviewed data or named external sources. Derive metrics programmatically, not by hand-copying values into UI text.

Confirm before building:

- source files, tables, sheet names, APIs, or source URLs;
- data grain and primary date column;
- timezone and daily cutoff;
- units, currencies, and sign conventions;
- metric definitions and denominators;
- refresh cadence and data owner;
- late-arriving data behavior;
- snapshot retention needs.

For market, stock, legal, regulatory, current-news, or source-freshness-sensitive dashboards, verify current information before finalizing and include concrete dates in visible freshness notes.

## Snapshot Store

Recurring dashboards should use immutable snapshots.

Recommended daily JSON snapshot:

```json
{
  "snapshot_date": "2026-06-25",
  "captured_at": "2026-06-25T09:05:00+08:00",
  "source": "finance_warehouse.daily_metrics",
  "timezone": "Asia/Shanghai",
  "rows": [
    {"date": "2026-06-25", "metric": "revenue", "segment": "Enterprise", "value": 12345}
  ]
}
```

Recommended JSONL row:

```json
{"snapshot_date":"2026-06-25","captured_at":"2026-06-25T09:05:00+08:00","date":"2026-06-25","metric":"revenue","segment":"Enterprise","value":12345}
```

The generator should normalize snapshots into one analytical table, deduplicate by stable keys, and expose available date ranges in `dashboard_data.json`.

## Automation Handoff

When combining with automation, create a recurring task that:

1. Fetches source data for the chosen cutoff.
2. Writes a dated snapshot under `data/snapshots/`.
3. Runs `python dashboard.py` to regenerate `index.html` and `dashboard_data.json`.
4. Optionally sends a short summary or link to the dashboard.

Automation should append new snapshots. Avoid overwriting historical snapshots unless the user explicitly requests a backfill or correction. For corrections, write a replacement snapshot with the same `snapshot_date` and a newer `captured_at`, then let the generator choose the latest capture per key.

## Payload Requirements

For each dashboard panel, include:

- the bounded rows used for the visual;
- a concise transform snippet in `sourceMap`;
- an analysis-only source excerpt for the modal's full-context code block;
- visible units and clear labels in panel subtitles, captions, axes, or tables;
- an initial chart type and any allowed alternate chart types.

The Data Source modal should show both the panel transform snippet and an `Analysis logic` excerpt that explains source rows, metric calculations, time filtering, and payload construction. Do not expose dashboard shell internals such as `build_html()`, CSS, JavaScript runtime wiring, ECharts option builders, or rendering helpers in the modal.

## Time Filtering

Prefer ISO date strings (`YYYY-MM-DD`) in payload rows. Preserve timezone in payload metadata. Range controls should filter by the primary analytical date, not by file modification time.

If the dashboard has multiple date grains, expose the filter grain clearly in the UI, such as "Order date", "Snapshot date", or "Invoice due date".
