#!/usr/bin/env python3
"""Template for a local/offline ECharts operating dashboard.

Copy this file into one dashboard folder for a new analysis and adapt the
clearly named data functions first. The dashboard folder should be the
deliverable bundle: `index.html`, `dashboard_data.json`, this generation
script, reusable runtime assets, and source data under `data/`.

Automation-friendly pattern:

- daily jobs write immutable JSON, JSONL, or CSV snapshots to data/snapshots/;
- this script normalizes the snapshots into dated rows;
- `dashboard_data.json` stores the bounded reviewed payload;
- `index.html` inlines ECharts and dashboard_runtime.js for local use.

Keep generation layers separate: build_dashboard_blocks(payload) composes
dashboard structure, render_* helpers emit dashboard markup, and build_html()
only inlines assets and wraps the final shell.
"""

from __future__ import annotations

import csv
import html
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
ECHARTS_JS = ROOT / "echarts.min.js"
DASHBOARD_RUNTIME_JS = ROOT / "dashboard_runtime.js"
DASHBOARD_HTML = ROOT / "index.html"
DASHBOARD_DATA = ROOT / "dashboard_data.json"

DASHBOARD_TITLE = "Daily Revenue Command Center"
DASHBOARD_SUBTITLE = "Automation-ready sample dashboard for recurring operating metrics"
TIMEZONE_LABEL = "Asia/Shanghai"
DEFAULT_RANGE = "30D"


def fmt_num(value: float) -> str:
    return f"{value:,.0f}"


def fmt_money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:+.1f}%"


def demo_rows() -> list[dict]:
    """Return deterministic demo rows when the dashboard has no local data yet."""
    rows: list[dict] = []
    start = date(2026, 5, 1)
    segments = ["Enterprise", "Mid Market", "SMB"]
    for offset in range(56):
        day = start + timedelta(days=offset)
        for index, segment in enumerate(segments):
            base = 62000 + index * 18000 + offset * (900 - index * 120)
            weekly = 1 + ((offset % 7) - 3) * 0.018
            revenue = round(base * weekly, 2)
            pipeline = round(revenue * (2.4 + index * 0.24), 2)
            customers = 18 + index * 9 + (offset % 5)
            rows.append(
                {
                    "date": day.isoformat(),
                    "metric": "revenue",
                    "segment": segment,
                    "value": revenue,
                    "pipeline": pipeline,
                    "customers": customers,
                    "snapshot_date": day.isoformat(),
                    "captured_at": f"{day.isoformat()}T09:05:00+08:00",
                    "source": "demo.daily_revenue_metrics",
                    "timezone": TIMEZONE_LABEL,
                }
            )
    return rows


def read_json_snapshot(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    rows = data.get("rows", [])
    for row in rows:
        row.setdefault("snapshot_date", data.get("snapshot_date"))
        row.setdefault("captured_at", data.get("captured_at"))
        row.setdefault("source", data.get("source"))
        row.setdefault("timezone", data.get("timezone"))
    return rows


def read_jsonl_snapshot(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_csv_snapshot(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def read_sources() -> list[dict]:
    rows: list[dict] = []
    paths = sorted(SNAPSHOT_DIR.glob("*")) if SNAPSHOT_DIR.exists() else []
    if not paths:
        return demo_rows()
    for path in paths:
        if path.suffix.lower() == ".json":
            rows.extend(read_json_snapshot(path))
        elif path.suffix.lower() == ".jsonl":
            rows.extend(read_jsonl_snapshot(path))
        elif path.suffix.lower() == ".csv":
            rows.extend(read_csv_snapshot(path))
    return rows


def normalize_snapshots(rows: list[dict]) -> list[dict]:
    normalized = []
    for raw in rows:
        row = dict(raw)
        row["date"] = str(row.get("date") or row.get("snapshot_date") or "")[:10]
        row["snapshot_date"] = str(row.get("snapshot_date") or row["date"])[:10]
        row["captured_at"] = str(row.get("captured_at") or "")
        row["metric"] = str(row.get("metric") or "value")
        row["segment"] = str(row.get("segment") or "All")
        row["value"] = float(row.get("value") or 0)
        row["pipeline"] = float(row.get("pipeline") or 0)
        row["customers"] = int(float(row.get("customers") or 0))
        row["source"] = str(row.get("source") or "local snapshot")
        if row["date"]:
            normalized.append(row)

    latest_by_key: dict[tuple[str, str, str], dict] = {}
    for row in normalized:
        key = (row["date"], row["metric"], row["segment"])
        previous = latest_by_key.get(key)
        if previous is None or row["captured_at"] >= previous.get("captured_at", ""):
            latest_by_key[key] = row
    return sorted(latest_by_key.values(), key=lambda item: (item["date"], item["segment"]))


def latest_date(rows: list[dict]) -> str:
    dates = sorted({row["date"] for row in rows if row.get("date")})
    return dates[-1] if dates else ""


def sum_between(rows: list[dict], start: str, end: str, field: str = "value") -> float:
    return sum(float(row.get(field) or 0) for row in rows if start <= row["date"] <= end)


def make_daily_series(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = defaultdict(lambda: {"date": "", "revenue": 0.0, "pipeline": 0.0, "customers": 0})
    for row in rows:
        item = grouped[row["date"]]
        item["date"] = row["date"]
        item["revenue"] += row["value"]
        item["pipeline"] += row["pipeline"]
        item["customers"] += row["customers"]
    return [grouped[key] for key in sorted(grouped)]


def make_segment_series(rows: list[dict]) -> list[dict]:
    return [
        {
            "date": row["date"],
            "segment": row["segment"],
            "revenue": row["value"],
            "pipeline": row["pipeline"],
            "customers": row["customers"],
            "snapshot_date": row["snapshot_date"],
            "source": row["source"],
        }
        for row in rows
    ]


def make_leaderboard(rows: list[dict]) -> list[dict]:
    grouped: dict[str, dict] = defaultdict(lambda: {"segment": "", "revenue": 0.0, "pipeline": 0.0, "customers": 0})
    for row in rows:
        item = grouped[row["segment"]]
        item["segment"] = row["segment"]
        item["revenue"] += row["value"]
        item["pipeline"] += row["pipeline"]
        item["customers"] += row["customers"]
    out = list(grouped.values())
    out.sort(key=lambda item: item["revenue"], reverse=True)
    return out


def make_dashboard_payload(rows: list[dict]) -> dict:
    daily = make_daily_series(rows)
    by_segment = make_segment_series(rows)
    leaderboard = make_leaderboard(rows)
    dates = [item["date"] for item in daily]
    latest = dates[-1] if dates else ""
    start_30 = dates[-30] if len(dates) >= 30 else (dates[0] if dates else "")
    previous_start = dates[-60] if len(dates) >= 60 else (dates[0] if dates else "")
    previous_end = dates[-31] if len(dates) >= 31 else latest
    revenue_30 = sum_between(daily, start_30, latest, "revenue") if latest else 0
    previous_30 = sum_between(daily, previous_start, previous_end, "revenue") if latest else 0
    delta = (revenue_30 - previous_30) / previous_30 if previous_30 else 0
    pipeline_30 = sum_between(daily, start_30, latest, "pipeline") if latest else 0
    customers_30 = sum(int(row["customers"]) for row in daily if start_30 <= row["date"] <= latest) if latest else 0
    latest_captured = max((row.get("captured_at", "") for row in rows), default="")

    source_snippets = {
        "revenueTrend": """daily = make_daily_series(rows)
filtered = [row for row in daily if start_date <= row["date"] <= end_date]
series = [{"date": row["date"], "revenue": row["revenue"]} for row in filtered]""",
        "segmentMix": """by_segment = make_segment_series(rows)
filtered = [row for row in by_segment if start_date <= row["date"] <= end_date]
grouped = sum revenue by segment for the active time range""",
        "pipelineCoverage": """daily = make_daily_series(rows)
coverage = row["pipeline"] / row["revenue"] when revenue is non-zero
the chart recomputes coverage after the time filter changes""",
        "leaderboard": """leaderboard = make_leaderboard(rows)
table rows are sorted by revenue descending and bounded for display""",
    }

    return {
        "title": DASHBOARD_TITLE,
        "subtitle": DASHBOARD_SUBTITLE,
        "timezone": TIMEZONE_LABEL,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "freshness": {
            "latestDataDate": latest,
            "latestCapturedAt": latest_captured,
            "source": rows[-1]["source"] if rows else "No source rows",
        },
        "availableDates": dates,
        "defaultRange": DEFAULT_RANGE,
        "kpis": [
            {
                "id": "revenue30",
                "label": "30 day revenue",
                "value": fmt_money(revenue_30),
                "delta": pct(delta),
                "detail": "vs prior available 30 day window",
            },
            {
                "id": "pipeline30",
                "label": "30 day pipeline",
                "value": fmt_money(pipeline_30),
                "delta": f"{pipeline_30 / revenue_30:.1f}x" if revenue_30 else "n/a",
                "detail": "pipeline coverage",
            },
            {
                "id": "customers30",
                "label": "30 day customers",
                "value": fmt_num(customers_30),
                "delta": f"{len(leaderboard)} segments",
                "detail": "active segment rows",
            },
        ],
        "datasets": {
            "daily": daily,
            "bySegment": by_segment,
            "leaderboard": leaderboard,
        },
        "sourceSnippets": source_snippets,
    }


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False).replace("</", "<\\/")


def json_script(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def render_kpi_block(block: dict) -> str:
    return f"""
    <section class="kpi-tile" id="{html.escape(block["id"])}">
      <p>{html.escape(block["label"])}</p>
      <strong>{html.escape(block["value"])}</strong>
      <span>{html.escape(block["delta"])}</span>
      <small>{html.escape(block["detail"])}</small>
    </section>
    """


def render_panel_actions(block: dict) -> str:
    edit = ""
    edit_command = ""
    if len(block.get("allowed_types", [])) > 1:
        options = "\n".join(
            f'<option value="{html.escape(kind)}"{" selected" if kind == block.get("initial_type") else ""}>{html.escape(kind)}</option>'
            for kind in block["allowed_types"]
        )
        edit_command = f"""<button onclick="toggleEdit('{html.escape(block["chart_id"])}')">Edit</button>"""
        edit = f"""
        <div class="edit-panel" id="edit-{html.escape(block["chart_id"])}">
          <label for="select-{html.escape(block["chart_id"])}">Type</label>
          <select id="select-{html.escape(block["chart_id"])}" onchange="setChartType('{html.escape(block["chart_id"])}', this.value)">
            {options}
          </select>
        </div>
        """
    return f"""
    <div class="chart-actions">
      {edit}
      <div class="toolbox">
        <button class="tool-button" aria-label="Panel actions" onclick="toggleMenu('{html.escape(block["chart_id"])}')"><span class="dot"></span><span class="dot"></span><span class="dot"></span></button>
        <div class="menu" id="menu-{html.escape(block["chart_id"])}">
          {edit_command}
          <button onclick="viewSource('{html.escape(block["source_key"])}')">View Data Source</button>
        </div>
      </div>
    </div>
    """


def infer_panel_span(block: dict) -> int:
    if block.get("span") is not None:
        span = int(block["span"])
        return span if span in (4, 6, 12) else 6
    if block["kind"] == "table":
        columns = block.get("columns", [])
        has_long_text = any(col.get("long_text") for col in columns)
        return 12 if len(columns) >= 6 or has_long_text else 6
    if block["kind"] == "chart":
        chart_type = str(block.get("initial_type") or "")
        dense_chart = chart_type in {"heatmap", "scatter"} or block.get("dense")
        many_categories = int(block.get("category_count") or 0) > 8
        return 12 if dense_chart or many_categories else 6
    if block["kind"] == "note":
        return 4 if block.get("compact") else 6
    return 6


def panel_span_attr(block: dict) -> str:
    span = infer_panel_span(block)
    return f'data-span="{span}"'


def render_chart_block(block: dict) -> str:
    return f"""
    <section class="dashboard-panel chart-panel" {panel_span_attr(block)} id="{html.escape(block["id"])}">
      <header>
        <div>
          <h2>{html.escape(block["title"])}</h2>
          <p>{html.escape(block["subtitle"])}</p>
        </div>
        {render_panel_actions(block)}
      </header>
      <div class="chart" id="{html.escape(block["chart_id"])}" role="img" aria-label="{html.escape(block["title"])}"></div>
      <footer>{html.escape(block["unit"])} | {html.escape(block["source_context"])}</footer>
    </section>
    """


def render_table_block(block: dict) -> str:
    columns = block["columns"]
    head = "".join(f"<th>{html.escape(col['label'])}</th>" for col in columns)
    return f"""
    <section class="dashboard-panel table-panel" {panel_span_attr(block)} id="{html.escape(block["id"])}">
      <header>
        <div>
          <h2>{html.escape(block["title"])}</h2>
          <p>{html.escape(block["subtitle"])}</p>
        </div>
        <div class="toolbox">
          <button class="tool-button" aria-label="Panel actions" onclick="toggleMenu('{html.escape(block["source_key"])}')"><span class="dot"></span><span class="dot"></span><span class="dot"></span></button>
          <div class="menu" id="menu-{html.escape(block["source_key"])}">
            <button onclick="viewSource('{html.escape(block["source_key"])}')">View Data Source</button>
          </div>
        </div>
      </header>
      <div class="table-scroll">
        <table id="{html.escape(block["table_id"])}">
          <thead><tr>{head}</tr></thead>
          <tbody></tbody>
        </table>
      </div>
      <footer>{html.escape(block["source_context"])}</footer>
    </section>
    """


def render_note_block(block: dict) -> str:
    return f"""
    <section class="dashboard-note" {panel_span_attr(block)} id="{html.escape(block["id"])}">
      <strong>{html.escape(block["title"])}</strong>
      <span>{html.escape(block["body"])}</span>
    </section>
    """


def build_dashboard_blocks(payload: dict) -> list[dict]:
    blocks = []
    blocks.extend({"kind": "kpi", **kpi} for kpi in payload["kpis"])
    blocks.extend(
        [
            {
                "kind": "chart",
                "id": "panel-revenue-trend",
                "chart_id": "revenueTrend",
                "source_key": "revenueTrend",
                "title": "Revenue trend",
                "subtitle": "Daily revenue updates with active time filtering",
                "unit": "USD",
                "source_context": "Source: daily snapshots normalized by dashboard.py",
                "allowed_types": ["line", "bar"],
                "initial_type": "line",
            },
            {
                "kind": "chart",
                "id": "panel-segment-mix",
                "chart_id": "segmentMix",
                "source_key": "segmentMix",
                "title": "Segment mix",
                "subtitle": "Revenue contribution by segment in selected range",
                "unit": "USD",
                "source_context": "Source: data/snapshots rows grouped by segment",
                "allowed_types": ["bar", "pie"],
                "initial_type": "bar",
            },
            {
                "kind": "chart",
                "id": "panel-pipeline-coverage",
                "chart_id": "pipelineCoverage",
                "source_key": "pipelineCoverage",
                "title": "Pipeline coverage",
                "subtitle": "Daily pipeline divided by revenue",
                "unit": "Coverage multiple",
                "source_context": "Source: daily snapshot pipeline and revenue fields",
                "allowed_types": ["line"],
                "initial_type": "line",
            },
            {
                "kind": "table",
                "id": "panel-leaderboard",
                "table_id": "leaderboardTable",
                "source_key": "leaderboard",
                "title": "Segment leaderboard",
                "subtitle": "Sorted by revenue after time filtering",
                "source_context": "Source: same bounded payload used by charts",
                "columns": [
                    {"field": "segment", "label": "Segment"},
                    {"field": "revenue", "label": "Revenue", "numeric": True},
                    {"field": "pipeline", "label": "Pipeline", "numeric": True},
                    {"field": "customers", "label": "Customers", "numeric": True},
                ],
            },
            {
                "kind": "note",
                "id": "automation-note",
                "title": "Automation handoff",
                "body": "Schedule a daily job to write a dated snapshot to data/snapshots, then run python dashboard.py to refresh this HTML.",
            },
        ]
    )
    return blocks


def render_dashboard_blocks(blocks: list[dict]) -> str:
    kpis = "\n".join(render_kpi_block(block) for block in blocks if block["kind"] == "kpi")
    panels = []
    for block in blocks:
        if block["kind"] == "chart":
            panels.append(render_chart_block(block))
        elif block["kind"] == "table":
            panels.append(render_table_block(block))
        elif block["kind"] == "note":
            panels.append(render_note_block(block))
    return f"""
    <section class="kpi-grid">{kpis}</section>
    <section class="panel-grid">{"".join(panels)}</section>
    """


ANALYSIS_LOGIC = """Analysis logic
- read_sources() loads JSON, JSONL, and CSV snapshots from data/snapshots/.
- normalize_snapshots() standardizes date, snapshot_date, metric, segment, value, pipeline, customers, source, and captured_at.
- duplicate rows are resolved by date, metric, and segment, keeping the newest captured_at.
- make_dashboard_payload() creates daily, segment, and leaderboard datasets plus freshness metadata.
- dashboard_runtime.js applies client-side date filtering against the analytical date field."""


def build_html(payload: dict) -> str:
    echarts = ECHARTS_JS.read_text(encoding="utf-8")
    runtime = DASHBOARD_RUNTIME_JS.read_text(encoding="utf-8")
    blocks = build_dashboard_blocks(payload)
    content = render_dashboard_blocks(blocks)
    initial_charts = [
        {"id": block["chart_id"], "type": block["initial_type"]}
        for block in blocks
        if block["kind"] == "chart"
    ]
    table_config = {
        "leaderboardTable": {
            "dataset": "leaderboard",
            "sortField": "revenue",
            "sortDirection": "desc",
            "limit": 10,
            "columns": [
                {"field": "segment"},
                {"field": "revenue", "numeric": True},
                {"field": "pipeline", "numeric": True},
                {"field": "customers", "numeric": True},
            ],
        }
    }
    source_map = payload["sourceSnippets"]

    css = """
    :root {
      color-scheme: light;
      --ink: #2f3437;
      --muted: #68707a;
      --faint: #8b95a3;
      --line: #e1e5ea;
      --line-strong: #cbd3dc;
      --panel: #FAFAFA;
      --page: #ffffff;
      --surface: #FAFAFA;
      --soft: #f2f3f5;
      --soft-blue: #f3f6fb;
      --control-bg: rgba(255, 255, 255, 0.94);
      --topbar-bg: rgba(255, 255, 255, 0.96);
      --menu-bg: #ffffff;
      --modal-bg: #ffffff;
      --modal-backdrop: rgba(55, 53, 47, 0.34);
      --table-head: #FAFAFA;
      --table-hover: #f1f2ff;
      --chart-bg: #FAFAFA;
      --chart-text: #2f3437;
      --chart-muted: #68707a;
      --chart-line: #e1e5ea;
      --chart-primary: #2F6BFF;
      --chart-secondary: #00BFA6;
      --chart-tertiary: #FF7A3D;
      --chart-quaternary: #F45BB3;
      --chart-1: #F45BB3;
      --chart-2: #2F6BFF;
      --chart-3: #00BFA6;
      --chart-4: #FF7A3D;
      --chart-5: #9BD82E;
      --chart-6: #7C3AED;
      --chart-7: #FFD23F;
      --brand: #6979F8;
      --brand-hover: #9EA9FF;
      --brand-end: #CDD2FD;
      --brand-text: #ffffff;
      --accent: #2F6BFF;
      --accent-2: #00BFA6;
      --warn: #b7791f;
    }
    html[data-theme="trae-dark"] {
      color-scheme: dark;
      --ink: #f5f9fe;
      --muted: #9599a6;
      --faint: #666b75;
      --line: #2a2d31;
      --line-strong: #3a3f45;
      --panel: #1a1b1d;
      --page: #0c0c0d;
      --surface: #222427;
      --soft: #2a2d31;
      --soft-blue: #202123;
      --control-bg: #202123;
      --topbar-bg: rgba(12, 12, 13, 0.92);
      --menu-bg: #202123;
      --modal-bg: #1a1b1d;
      --modal-backdrop: rgba(0, 0, 0, 0.58);
      --table-head: #222427;
      --table-hover: #202123;
      --chart-bg: #222427;
      --chart-text: #d1d3db;
      --chart-muted: #9599a6;
      --chart-line: #2a2d31;
      --chart-primary: #28d9ff;
      --chart-secondary: #32f08c;
      --chart-tertiary: #f6c85f;
      --chart-quaternary: #ff6b9a;
      --chart-1: #32f08c;
      --chart-2: #28d9ff;
      --chart-3: #a78bfa;
      --chart-4: #f6c85f;
      --chart-5: #ff6b9a;
      --chart-6: #6ea8ff;
      --chart-7: #d1d3db;
      --brand: #32f08c;
      --brand-hover: #0fdc78;
      --brand-end: #32f08c;
      --brand-text: #0c0c0d;
      --accent: #32f08c;
      --accent-2: #0fdc78;
    }
    * { box-sizing: border-box; }
    html { background: var(--page); }
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Helvetica Neue", Arial, sans-serif;
      background: var(--page);
      color: var(--ink);
      font-size: 1rem;
      line-height: 1.55;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }
    .topbar {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid var(--line);
      background: var(--topbar-bg);
      backdrop-filter: blur(12px);
    }
    .topbar-inner {
      max-width: 1320px;
      margin: 0 auto;
      padding: 14px 22px;
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto;
      gap: 18px;
      align-items: center;
    }
    h1, h2, p { margin: 0; }
    h1 { font-size: 22px; font-weight: 500; letter-spacing: 0; }
    .subtitle, .freshness, .range-label, .dashboard-panel p, footer, small {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      font-weight: 400;
    }
    .controls {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
    }
    .range-label { display: none; }
    .segmented {
      display: inline-flex;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--control-bg);
    }
    .segmented button, .menu button, .edit-panel button {
      border: 0;
      background: transparent;
      color: var(--ink);
      font: inherit;
      cursor: pointer;
    }
    .segmented button {
      min-width: 44px;
      height: 34px;
      padding: 0 10px;
      border-right: 1px solid var(--line);
      font-size: 13px;
      font-weight: 400;
    }
    .segmented button:last-child { border-right: 0; }
    .segmented button.active { background: var(--brand); color: var(--brand-text); font-weight: 500; }
    .theme-switch button.active { background: var(--brand); color: var(--brand-text); }
    .theme-switch button {
      width: 38px;
      min-width: 38px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0;
    }
    .theme-switch svg {
      width: 16px;
      height: 16px;
      stroke-width: 2;
    }
    .date-fields { display: inline-flex; align-items: center; gap: 6px; }
    input[type="date"] {
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 0 8px;
      background: var(--control-bg);
      color: var(--ink);
      font: inherit;
      font-size: 13px;
      font-weight: 400;
    }
    .dashboard-shell {
      max-width: 1320px;
      margin: 0 auto;
      padding: 18px 22px 44px;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }
    .kpi-tile {
      min-height: 126px;
      padding: 15px;
      display: grid;
      align-content: space-between;
      gap: 8px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 12px;
    }
    .kpi-tile:first-child {
      background: linear-gradient(135deg, var(--brand) 0%, var(--brand-hover) 58%, var(--brand-end) 100%);
      border-color: var(--brand);
    }
    .kpi-tile p { color: var(--muted); font-size: 13px; font-weight: 500; }
    .kpi-tile strong { font-size: 28px; font-weight: 500; letter-spacing: 0; }
    .kpi-tile span { color: var(--ink); font-size: 15px; font-weight: 500; line-height: 1.35; }
    .kpi-tile small { font-size: 13px; font-weight: 400; }
    .kpi-tile:first-child p,
    .kpi-tile:first-child strong,
    .kpi-tile:first-child span,
    .kpi-tile:first-child small { color: var(--brand-text); }
    .panel-grid {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 20px 16px;
    }
    .dashboard-panel {
      min-height: 360px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: transparent;
      border: 0;
      border-radius: 0;
      padding: 0;
    }
    [data-span="4"] { grid-column: span 4; }
    [data-span="6"] { grid-column: span 6; }
    [data-span="12"] { grid-column: 1 / -1; }
    .dashboard-note {
      min-height: 180px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: transparent;
    }
    .dashboard-panel header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 12px;
      min-height: 42px;
    }
    .dashboard-panel h2 { font-size: 17px; font-weight: 500; letter-spacing: 0; }
    .chart {
      width: 100%;
      height: 276px;
      min-height: 276px;
      padding: 8px 0 6px;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--chart-bg);
    }
    .chart-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 8px;
      flex: 0 0 auto;
      position: relative;
      z-index: 12;
    }
    .toolbox { position: relative; flex: 0 0 auto; }
    .tool-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 3px;
      width: 34px;
      height: 30px;
      border: 1px solid var(--line-strong);
      border-radius: 999px;
      background: var(--control-bg);
      color: var(--muted);
      cursor: pointer;
      font-size: 0;
      line-height: 0;
      padding: 0;
      opacity: 0;
      transition: opacity 140ms ease, background-color 140ms ease;
    }
    .tool-button .dot {
      display: block;
      width: 3px;
      height: 3px;
      border-radius: 50%;
      background: currentColor;
    }
    .dashboard-panel:hover .tool-button,
    .dashboard-panel:focus-within .tool-button,
    .dashboard-note:hover .tool-button,
    .dashboard-note:focus-within .tool-button { opacity: 1; }
    .menu {
      display: none;
      position: absolute;
      right: 0;
      top: 34px;
      z-index: 40;
      width: 188px;
      padding: 6px;
      border: 1px solid var(--line-strong);
      border-radius: 8px;
      background: var(--menu-bg);
      box-shadow: 0 8px 18px rgba(32, 33, 36, 0.12);
    }
    .menu.open { display: block; }
    .edit-panel {
      display: none;
      align-items: center;
      gap: 6px;
      height: 28px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--control-bg);
      color: var(--muted);
      font-size: 13px;
    }
    .edit-panel.open { display: flex; }
    .edit-panel label {
      padding-left: 8px;
      white-space: nowrap;
    }
    .edit-panel select {
      height: 26px;
      border: 0;
      border-left: 1px solid var(--line);
      border-radius: 0 5px 5px 0;
      padding: 0 24px 0 7px;
      background: transparent;
      color: var(--ink);
      font: inherit;
      font-size: 13px;
      outline: none;
      cursor: pointer;
    }
    .menu button {
      display: block;
      width: 100%;
      border: 0;
      background: transparent;
      padding: 8px 10px;
      border-radius: 6px;
      text-align: left;
      cursor: pointer;
      color: var(--ink);
      font: inherit;
      font-size: 13px;
    }
    .menu button:hover, .menu button:focus-visible {
      background: var(--soft-blue);
      outline: none;
    }
    .table-scroll {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 16px;
      background: var(--surface);
    }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 10px; border-bottom: 1px solid var(--line); text-align: left; white-space: nowrap; }
    th { color: var(--muted); font-weight: 500; background: var(--table-head); }
    td.num { text-align: right; font-variant-numeric: tabular-nums; }
    tbody tr:last-child td { border-bottom: 0; }
    tbody tr:hover td { background: var(--table-hover); }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 24px;
      background: var(--modal-backdrop);
      z-index: 50;
    }
    .modal-backdrop.open { display: flex; }
    .modal {
      width: min(860px, 100%);
      max-height: min(780px, 92vh);
      overflow: auto;
      border-radius: 16px;
      background: var(--modal-bg);
      border: 1px solid var(--line-strong);
      box-shadow: 0 18px 48px rgba(55, 53, 47, 0.18);
    }
    .modal-head {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
      padding: 18px 20px 14px;
      border-bottom: 1px solid var(--line);
    }
    .modal-head h3 {
      margin: 0;
      font-size: 16px;
      line-height: 1.4;
      font-weight: 600;
    }
    .modal-subtitle {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 14px;
      line-height: 1.45;
    }
    .modal-body { padding: 18px 20px 20px; }
    .source-section + .source-section { margin-top: 16px; }
    .source-section h4 {
      margin: 0 0 8px;
      color: var(--ink);
      font-size: 14px;
      line-height: 1.4;
      font-weight: 600;
    }
    .code-wrap { position: relative; }
    pre {
      margin: 0;
      padding: 14px;
      overflow: auto;
      border-radius: 8px;
      border: 1px solid var(--line);
      background: var(--soft);
      color: var(--ink);
      font-size: 12px;
      line-height: 1.5;
    }
    .close {
      width: 32px;
      height: 32px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      padding: 0;
    }
    .close svg { width: 18px; height: 18px; stroke-width: 2.1; }
    .close:hover, .close:focus-visible { background: var(--soft); outline: none; }
    .copy-button {
      position: absolute;
      right: 8px;
      top: 8px;
      width: 28px;
      height: 28px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--control-bg);
      color: var(--muted);
      cursor: pointer;
    }
    .copy-button svg { width: 15px; height: 15px; stroke-width: 2; }
    .copy-button:hover, .copy-button:focus-visible {
      background: var(--soft);
      color: var(--ink);
      outline: none;
    }
    @media (max-width: 900px) {
      .topbar-inner { grid-template-columns: 1fr; }
      .controls { justify-content: flex-start; }
      .kpi-grid { grid-template-columns: 1fr; }
      .dashboard-panel, .dashboard-note, [data-span] { grid-column: 1 / -1; }
    }
    @media (max-width: 620px) {
      .topbar-inner, .dashboard-shell { padding-left: 14px; padding-right: 14px; }
      .segmented { width: 100%; }
      .segmented button { flex: 1; min-width: 0; }
      .date-fields { width: 100%; }
      input[type="date"] { min-width: 0; width: 100%; }
      .chart { height: 240px; min-height: 240px; }
    }
    """

    chart_js = f"""
    const dashboardPayload = {json_script(payload)};
    function cssToken(name) {{
      return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }}
    function chartTheme() {{
      return {{
        text: cssToken("--chart-text"),
        muted: cssToken("--chart-muted"),
        line: cssToken("--chart-line"),
        primary: cssToken("--chart-primary"),
        secondary: cssToken("--chart-secondary"),
        tertiary: cssToken("--chart-tertiary"),
        quaternary: cssToken("--chart-quaternary"),
        palette: [1, 2, 3, 4, 5, 6, 7].map(index => cssToken("--chart-" + index))
      }};
    }}
    function axisStyle(extra) {{
      const theme = chartTheme();
      const base = {{
        axisLabel: {{ color: theme.muted }},
        axisLine: {{ lineStyle: {{ color: theme.line }} }},
        axisTick: {{ lineStyle: {{ color: theme.line }} }},
        splitLine: {{ lineStyle: {{ color: theme.line }} }}
      }};
      const merged = Object.assign({{}}, base, extra || {{}});
      merged.axisLabel = Object.assign({{}}, base.axisLabel, (extra || {{}}).axisLabel || {{}});
      return merged;
    }}
    function chartBase(...colorKeys) {{
      const theme = chartTheme();
      return {{
        textStyle: {{ color: theme.text }},
        color: colorKeys.map(key => theme[key] || key)
      }};
    }}
    const categoryColorKeys = {{
      "Enterprise": "primary",
      "Mid Market": "secondary",
      "SMB": "tertiary",
      "Other": "#8A94A3",
      "其他": "#8A94A3",
      "Unknown": "#A7ADB6",
      "未填写": "#A7ADB6"
    }};
    function categoricalColor(name, index) {{
      const key = String(name || "").trim();
      const theme = chartTheme();
      const tokenOrColor = categoryColorKeys[key];
      return theme[tokenOrColor] || tokenOrColor || theme.palette[index % theme.palette.length];
    }}
    const chartFactories = {{
      revenueTrend: function(type, filteredRows) {{
        const rows = filteredRows("daily");
        return {{
          ...chartBase("primary"),
          tooltip: {{ trigger: "axis" }},
          grid: {{ left: 52, right: 18, top: 28, bottom: 36 }},
          xAxis: axisStyle({{ type: "category", data: rows.map(row => row.date), axisLabel: {{ hideOverlap: true }} }}),
          yAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => "$" + Math.round(value / 1000) + "k" }} }}),
          series: [{{ type: type, smooth: type === "line", data: rows.map(row => row.revenue), areaStyle: type === "line" ? {{ opacity: 0.08 }} : undefined }}]
        }};
      }},
      segmentMix: function(type, filteredRows) {{
        const totals = new Map();
        filteredRows("bySegment").forEach(row => totals.set(row.segment, (totals.get(row.segment) || 0) + row.revenue));
        const rows = Array.from(totals, ([segment, revenue]) => ({{ segment, revenue }})).sort((a, b) => b.revenue - a.revenue);
        if (type === "pie") {{
          return {{
            ...chartBase(),
            color: rows.map((row, index) => categoricalColor(row.segment, index)),
            tooltip: {{ trigger: "item" }},
            series: [{{ type: "pie", radius: ["42%", "70%"], data: rows.map(row => ({{ name: row.segment, value: row.revenue }})) }}]
          }};
        }}
        return {{
          ...chartBase("secondary"),
          tooltip: {{ trigger: "axis" }},
          grid: {{ left: 74, right: 18, top: 24, bottom: 30 }},
          xAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => "$" + Math.round(value / 1000) + "k" }} }}),
          yAxis: axisStyle({{ type: "category", data: rows.map(row => row.segment) }}),
          series: [{{ type: "bar", data: rows.map(row => row.revenue), barMaxWidth: 30 }}]
        }};
      }},
      pipelineCoverage: function(type, filteredRows) {{
        const rows = filteredRows("daily").map(row => ({{
          date: row.date,
          coverage: row.revenue ? row.pipeline / row.revenue : 0
        }}));
        return {{
          ...chartBase("tertiary"),
          tooltip: {{ trigger: "axis", valueFormatter: value => Number(value).toFixed(2) + "x" }},
          grid: {{ left: 48, right: 18, top: 28, bottom: 36 }},
          xAxis: axisStyle({{ type: "category", data: rows.map(row => row.date), axisLabel: {{ hideOverlap: true }} }}),
          yAxis: axisStyle({{ type: "value", axisLabel: {{ formatter: value => value.toFixed(1) + "x" }} }}),
          series: [{{ type: "line", smooth: true, data: rows.map(row => Number(row.coverage.toFixed(3))) }}]
        }};
      }}
    }};
    const sourceMap = {json_script(source_map)};
    setupDashboardRuntime({{
      datasets: dashboardPayload.datasets,
      availableDates: dashboardPayload.availableDates,
      defaultRange: dashboardPayload.defaultRange,
      initialCharts: {json_script(initial_charts)},
      chartFactories,
      sourceMap,
      tables: {json_script(table_config)},
      fullScript: {js_string(ANALYSIS_LOGIC)},
      modalSubtitlePrefix: "Dashboard panel transform for "
    }});
    """

    return f"""<!-- Generated by Trae Work -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(payload["title"])}</title>
  <style>{css}</style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div>
        <h1>{html.escape(payload["title"])}</h1>
        <p class="subtitle">{html.escape(payload["subtitle"])}</p>
        <p class="freshness" id="dataFreshness">Latest data: {html.escape(payload["freshness"]["latestDataDate"])} | Captured: {html.escape(payload["freshness"]["latestCapturedAt"])} | {html.escape(payload["timezone"])}</p>
      </div>
      <div class="controls" aria-label="Dashboard time controls">
        <span class="range-label" id="activeRangeLabel"></span>
        <div class="segmented" aria-label="Time preset">
          <button data-range-preset="7D">7D</button>
          <button data-range-preset="30D">30D</button>
          <button data-range-preset="MTD">MTD</button>
          <button data-range-preset="QTD">QTD</button>
          <button data-range-preset="YTD">YTD</button>
          <button data-range-preset="ALL">All</button>
        </div>
        <div class="date-fields">
          <input id="rangeStart" data-range-input type="date" aria-label="Start date">
          <input id="rangeEnd" data-range-input type="date" aria-label="End date">
        </div>
        <div class="segmented theme-switch" aria-label="Theme">
          <button data-theme-choice="light" type="button" aria-label="Light theme" title="Light">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <circle cx="12" cy="12" r="4"></circle>
              <path d="M12 2v2"></path>
              <path d="M12 20v2"></path>
              <path d="m4.93 4.93 1.41 1.41"></path>
              <path d="m17.66 17.66 1.41 1.41"></path>
              <path d="M2 12h2"></path>
              <path d="M20 12h2"></path>
              <path d="m6.34 17.66-1.41 1.41"></path>
              <path d="m19.07 4.93-1.41 1.41"></path>
            </svg>
          </button>
          <button data-theme-choice="trae-dark" type="button" aria-label="Dark theme" title="Dark">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
              <path d="M20.99 13.53A8.5 8.5 0 1 1 10.47 3.01 7 7 0 0 0 20.99 13.53Z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </header>
  <main class="dashboard-shell">
    {content}
  </main>
  <div id="modalBackdrop" class="modal-backdrop" role="dialog" aria-modal="true">
    <section class="modal">
      <div class="modal-head">
        <div>
          <h3 id="modalTitle">Data Source</h3>
          <p class="modal-subtitle" id="modalSubtitle"></p>
        </div>
        <button class="close" aria-label="Close" onclick="closeModal()">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
            <path d="M18 6 6 18"></path>
            <path d="m6 6 12 12"></path>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <section class="source-section">
          <h4>Panel transform</h4>
          <div class="code-wrap">
            <button class="copy-button" aria-label="Copy panel transform" onclick="copyCode('modalSnippet', this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <pre><code id="modalSnippet"></code></pre>
          </div>
        </section>
        <section class="source-section">
          <h4>Analysis logic</h4>
          <div class="code-wrap">
            <button class="copy-button" aria-label="Copy analysis logic" onclick="copyCode('modalCode', this)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
            </button>
            <pre><code id="modalCode"></code></pre>
          </div>
        </section>
      </div>
    </section>
  </div>
  <script>{echarts}</script>
  <script>{runtime}</script>
  <script>{chart_js}</script>
</body>
</html>
"""


def main() -> None:
    rows = normalize_snapshots(read_sources())
    payload = make_dashboard_payload(rows)
    DASHBOARD_DATA.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    DASHBOARD_HTML.write_text(build_html(payload), encoding="utf-8")
    print(f"Wrote {DASHBOARD_HTML}")
    print(f"Wrote {DASHBOARD_DATA}")


if __name__ == "__main__":
    main()
