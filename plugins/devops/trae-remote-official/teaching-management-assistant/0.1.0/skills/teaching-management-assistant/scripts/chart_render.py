#!/usr/bin/env python3
"""教学分析 HTML 渲染引擎。

三种模式，产物均为**单个自包含 HTML**（内联 ECharts，离线双击可打开，不依赖任何外部文件）：

1. 报告模式 `--report`（主交付物）：把叙事结论、KPI、多个图表、明细表、改进建议
   汇总成一份完整教学分析报告 HTML。用 --config 传入报告结构 JSON。
2. 看板模式 `--dashboard`：多图并排看板（配 --config）。
3. 单图模式 `--chart-type`：单个图表。

ECharts 运行时默认内联本地 assets/echarts.min.js；找不到时回退 CDN 并告警。
"""

import argparse
import json
import math
import sys
from pathlib import Path

ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
DATAZOOM_THRESHOLD = 15
COLORS = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452']


def load_data(data_path):
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_echarts_runtime():
    """返回 (script_tag, is_inline)。优先内联本地 echarts，保证离线自包含。"""
    local = Path(__file__).resolve().parent.parent / "assets" / "echarts.min.js"
    if local.exists():
        js = local.read_text(encoding='utf-8')
        return f"<script>{js}</script>", True
    print(f"警告：未找到本地 {local}，回退 CDN，生成的 HTML 将依赖网络", file=sys.stderr)
    return f'<script src="{ECHARTS_CDN}"></script>', False


# ═══════════════════════════════════════════════════════════════
# 图表构建器
# ═══════════════════════════════════════════════════════════════

def build_line_option(data, title, x_axis, y_axes):
    x_data = [row[x_axis] for row in data]
    series = []
    for y in y_axes:
        series.append({"name": y, "type": "line", "data": [row.get(y) for row in data],
                       "smooth": True, "symbolSize": 4})
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 30, "data": y_axes} if len(y_axes) > 1 else {},
        "grid": {"top": 60 if len(y_axes) <= 1 else 70, "bottom": 50, "left": 60, "right": 30},
        "xAxis": {"type": "category", "data": x_data, "boundaryGap": False},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": series,
    }
    if len(x_data) > DATAZOOM_THRESHOLD:
        option["dataZoom"] = [{"type": "slider", "bottom": 8}, {"type": "inside"}]
        option["grid"]["bottom"] = 70
    return option


def build_bar_option(data, title, x_axis, y_axes):
    x_data = [row[x_axis] for row in data]
    series = []
    for y in y_axes:
        series.append({"name": y, "type": "bar", "data": [row.get(y) for row in data], "barMaxWidth": 40})
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 30, "data": y_axes} if len(y_axes) > 1 else {},
        "grid": {"top": 60 if len(y_axes) <= 1 else 70, "bottom": 50, "left": 60, "right": 30},
        "xAxis": {"type": "category", "data": x_data, "axisLabel": {"rotate": 30 if len(x_data) > 8 else 0}},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": series,
    }
    if len(x_data) > DATAZOOM_THRESHOLD:
        option["dataZoom"] = [{"type": "slider", "bottom": 8}, {"type": "inside"}]
        option["grid"]["bottom"] = 70
    return option


def build_pie_option(data, title, x_axis, y_axes):
    y_col = y_axes[0]
    pie_data = [{"name": str(row[x_axis]), "value": row.get(y_col)} for row in data]
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"orient": "vertical", "left": 10, "top": 50},
        "series": [{"type": "pie", "radius": ["40%", "68%"], "center": ["58%", "55%"],
                    "data": pie_data, "label": {"formatter": "{b}\n{d}%", "fontSize": 11}}],
    }


def build_scatter_option(data, title, x_axis, y_axes):
    y_col = y_axes[0]
    scatter_data = [[row.get(x_axis), row.get(y_col)] for row in data]
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "xAxis": {"type": "value", "name": x_axis, "nameLocation": "center", "nameGap": 28, "splitLine": {"lineStyle": {"type": "dashed"}}},
        "yAxis": {"type": "value", "name": y_col, "nameLocation": "center", "nameGap": 36, "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": [{"type": "scatter", "data": scatter_data, "symbolSize": 10}],
    }


def build_histogram_option(data, title, x_axis, y_axes):
    col = x_axis
    values = [row.get(col) for row in data if row.get(col) is not None]
    if not values:
        return {"title": {"text": title}, "series": []}
    min_v, max_v = min(values), max(values)
    bin_count = min(20, max(5, int(math.sqrt(len(values)))))
    bin_width = (max_v - min_v) / bin_count if max_v != min_v else 1
    bins = [0] * bin_count
    labels = []
    for i in range(bin_count):
        low = min_v + i * bin_width
        high = low + bin_width
        labels.append(f"{low:.0f}")
        for v in values:
            if low <= v < high or (i == bin_count - 1 and v == max_v):
                bins[i] += 1
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": labels, "name": col},
        "yAxis": {"type": "value", "name": "频数", "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": [{"type": "bar", "data": bins, "barWidth": "80%"}],
    }


def build_boxplot_option(data, title, x_axis, y_axes):
    cols = y_axes if y_axes else [k for k in data[0].keys() if isinstance(data[0].get(k), (int, float))]
    box_data = []
    valid_cols = []
    for col in cols:
        values = sorted([row[col] for row in data if row.get(col) is not None])
        if len(values) < 5:
            continue
        n = len(values)
        q1, median, q3 = values[n // 4], values[n // 2], values[3 * n // 4]
        iqr = q3 - q1
        low = max(values[0], q1 - 1.5 * iqr)
        high = min(values[-1], q3 + 1.5 * iqr)
        box_data.append([low, q1, median, q3, high])
        valid_cols.append(col)
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "grid": {"left": 60, "right": 30, "bottom": 50},
        "xAxis": {"type": "category", "data": valid_cols},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": [{"type": "boxplot", "data": box_data}],
    }


def build_radar_option(data, title, x_axis, y_axes):
    max_val = 0
    for row in data:
        for y in y_axes:
            v = row.get(y, 0) or 0
            max_val = max(max_val, v)
    indicators = [{"name": row[x_axis], "max": max_val * 1.2} for row in data]
    series_data = [{"name": y, "value": [row.get(y, 0) for row in data]} for y in y_axes]
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "legend": {"top": 30, "data": y_axes},
        "radar": {"indicator": indicators, "center": ["50%", "58%"], "radius": "60%"},
        "series": [{"type": "radar", "data": series_data}],
    }


def build_heatmap_option(data, title, x_axis, y_axes):
    y_col = y_axes[0] if y_axes else list(data[0].keys())[1]
    remaining = [k for k in data[0].keys() if k != x_axis and k != y_col]
    val_col = remaining[0] if remaining else y_col
    x_cats = sorted(set(str(row[x_axis]) for row in data))
    y_cats = sorted(set(str(row[y_col]) for row in data))
    heat_data = []
    for row in data:
        xi = x_cats.index(str(row[x_axis]))
        yi = y_cats.index(str(row[y_col]))
        heat_data.append([xi, yi, row.get(val_col, 0)])
    all_vals = [d[2] for d in heat_data if d[2] is not None]
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"position": "top"},
        "grid": {"top": 50, "bottom": 50, "left": 70, "right": 30},
        "xAxis": {"type": "category", "data": x_cats, "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": y_cats, "splitArea": {"show": True}},
        "visualMap": {"min": min(all_vals) if all_vals else 0, "max": max(all_vals) if all_vals else 1,
                      "calculable": True, "orient": "horizontal", "left": "center", "bottom": 8},
        "series": [{"type": "heatmap", "data": heat_data, "label": {"show": len(heat_data) < 100, "fontSize": 10}}],
    }


CHART_BUILDERS = {
    "line": build_line_option, "bar": build_bar_option, "pie": build_pie_option,
    "scatter": build_scatter_option, "histogram": build_histogram_option,
    "boxplot": build_boxplot_option, "radar": build_radar_option, "heatmap": build_heatmap_option,
}


def build_option(chart_cfg, fallback_data):
    """从图表配置构建 ECharts option。图表可自带 data，否则用全局 fallback_data。"""
    ct = chart_cfg["type"]
    builder = CHART_BUILDERS.get(ct)
    if not builder:
        print(f"警告：不支持的图表类型 {ct}，跳过", file=sys.stderr)
        return None
    cdata = chart_cfg.get("data", fallback_data)
    y_axis = chart_cfg.get("y_axis", [])
    if isinstance(y_axis, str):
        y_axis = [y_axis]
    opt = builder(cdata, chart_cfg.get("title", ""), chart_cfg.get("x_axis", ""), y_axis)
    subtitle = chart_cfg.get("subtitle", "")
    if subtitle:
        opt["title"]["subtext"] = subtitle
        opt["title"]["subtextStyle"] = {"fontSize": 12, "color": "#8c8c8c"}
    return opt


# ═══════════════════════════════════════════════════════════════
# 通用 HTML 片段
# ═══════════════════════════════════════════════════════════════

BASE_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f6f8; color: #1a1a1a; line-height: 1.6; padding: 24px; }
.wrap { max-width: 1100px; margin: 0 auto; }
.report-header { border-bottom: 2px solid #1a1a1a; padding-bottom: 14px; margin-bottom: 4px; }
.report-header h1 { font-size: 22px; font-weight: 700; }
.report-header .meta { font-size: 12px; color: #666; margin-top: 6px; }
.report-header .meta span { margin-right: 16px; }
section.block { background: #fff; border: 1px solid #e5e5e5; border-radius: 6px; padding: 20px 24px; margin-top: 16px; }
section.block > h2 { font-size: 16px; font-weight: 700; margin-bottom: 12px; padding-left: 10px; border-left: 3px solid #5470c6; }
.prose p { font-size: 14px; margin: 6px 0; }
.prose ul { margin: 6px 0 6px 22px; }
.prose li { font-size: 14px; margin: 4px 0; }
.metrics-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px; }
.metric-card { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 4px; padding: 14px 16px; }
.metric-label { font-size: 12px; color: #666; margin-bottom: 4px; }
.metric-value { font-size: 20px; font-weight: 700; }
.metric-sub { font-size: 11px; color: #999; margin-top: 2px; }
.charts-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 16px; }
.chart-panel { border: 1px solid #eee; border-radius: 4px; padding: 8px; }
.chart { width: 100%; height: 340px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { padding: 8px 10px; text-align: left; font-weight: 600; color: #555; border-bottom: 1px solid #d1d5db; background: #fafafa; }
td { padding: 8px 10px; border-bottom: 1px solid #f0f0f0; }
tr:hover td { background: #fafbfc; }
.tag { display: inline-block; font-size: 11px; padding: 1px 8px; border-radius: 10px; margin-right: 6px; }
.tag-fact { background: #eef2ff; color: #3b4a9c; }
.tag-stat { background: #e8f5e9; color: #2e7d32; }
.tag-hypo { background: #fff4e5; color: #b26a00; }
.tag-action { background: #fce8e6; color: #b42318; }
.callout { background: #fffbe6; border: 1px solid #ffe58f; border-radius: 4px; padding: 10px 14px; font-size: 12px; color: #614700; margin-top: 8px; }
.footer-note { text-align: center; font-size: 12px; color: #999; margin-top: 20px; padding-top: 12px; }
@media (max-width: 768px) { .charts-grid { grid-template-columns: 1fr; } body { padding: 12px; } }
"""


def html_metrics(metrics):
    if not metrics:
        return ""
    status_colors = {"danger": "#e53e3e", "warning": "#d69e2e", "success": "#38a169"}
    cards = ""
    for m in metrics:
        border = status_colors.get(m.get('status', ''), '#d1d5db')
        sub = f'<div class="metric-sub">{m["sub"]}</div>' if m.get('sub') else ''
        cards += (f'<div class="metric-card" style="border-left:3px solid {border};">'
                  f'<div class="metric-label">{m.get("label","")}</div>'
                  f'<div class="metric-value">{m.get("value","")}</div>{sub}</div>')
    return f'<div class="metrics-row">{cards}</div>'


def html_table(tbl):
    if not tbl:
        return ""
    columns = tbl.get('columns', [])
    rows = tbl.get('data', [])
    header = "".join(f"<th>{c}</th>" for c in columns)
    body = ""
    for row in rows:
        body += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
    cap = f'<h2>{tbl["title"]}</h2>' if tbl.get('title') else ''
    return f'{cap}<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>'


# ═══════════════════════════════════════════════════════════════
# 报告模式：单个自包含 HTML，汇总全部信息
# ═══════════════════════════════════════════════════════════════

def render_report_html(config, echarts_tag):
    """config 结构：
    {
      "title": "...", "meta": {"数据范围":"...","生成时间":"...","分析对象":"..."},
      "sections": [
        {"type":"prose","heading":"核心结论","html":"<p>..</p>"},
        {"type":"metrics","heading":"关键指标","metrics":[{label,value,sub,status}]},
        {"type":"charts","heading":"成绩分布","charts":[{type,title,x_axis,y_axis,data}]},
        {"type":"table","heading":"需关注学生","table":{title,columns,data}},
        {"type":"prose","heading":"改进建议","html":"<p>..</p>"}
      ],
      "footer": "AI 辅助分析，请结合教学实际判断"
    }
    """
    title = config.get("title", "教学分析报告")
    meta = config.get("meta", {})
    meta_html = "".join(f"<span>{k}：{v}</span>" for k, v in meta.items())

    chart_init = []
    body_parts = []
    chart_idx = 0

    for sec in config.get("sections", []):
        stype = sec.get("type")
        heading = f'<h2>{sec["heading"]}</h2>' if sec.get("heading") else ""

        if stype == "prose":
            body_parts.append(f'<section class="block">{heading}<div class="prose">{sec.get("html","")}</div>'
                              + (f'<div class="callout">{sec["callout"]}</div>' if sec.get("callout") else "")
                              + '</section>')
        elif stype == "metrics":
            body_parts.append(f'<section class="block">{heading}{html_metrics(sec.get("metrics",[]))}</section>')
        elif stype == "charts":
            panels = ""
            for ch in sec.get("charts", []):
                opt = build_option(ch, ch.get("data", []))
                if opt is None:
                    continue
                panels += f'<div class="chart-panel"><div id="chart{chart_idx}" class="chart"></div></div>'
                chart_init.append(f"var c{chart_idx}=echarts.init(document.getElementById('chart{chart_idx}'));"
                                  f"c{chart_idx}.setOption({json.dumps(opt, ensure_ascii=False)});")
                chart_idx += 1
            body_parts.append(f'<section class="block">{heading}<div class="charts-grid">{panels}</div></section>')
        elif stype == "table":
            body_parts.append(f'<section class="block">{heading}{html_table(sec.get("table"))}</section>')

    resize = ";".join(f"c{i}.resize()" for i in range(chart_idx))
    footer = config.get("footer", "AI 辅助分析，请结合教学实际判断")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{echarts_tag}
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="report-header">
    <h1>{title}</h1>
    <div class="meta">{meta_html}</div>
  </div>
  {''.join(body_parts)}
  <div class="footer-note">{footer}</div>
</div>
<script>
{''.join(chart_init)}
window.addEventListener('resize',function(){{{resize}}});
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# 看板模式 / 单图模式
# ═══════════════════════════════════════════════════════════════

def render_dashboard_html(config, data, echarts_tag):
    dashboard_title = config.get("title", "数据看板")
    options = []
    for ch in config["charts"]:
        opt = build_option(ch, data)
        if opt is not None:
            options.append(opt)
    charts_html = ""
    init = ""
    for i, opt in enumerate(options):
        charts_html += f'<div class="chart-panel"><div id="chart{i}" class="chart"></div></div>'
        init += f"var c{i}=echarts.init(document.getElementById('chart{i}'));c{i}.setOption({json.dumps(opt, ensure_ascii=False)});"
    resize = ";".join(f"c{i}.resize()" for i in range(len(options)))
    metrics_html = html_metrics(config.get("metrics", []))
    table_html = f'<section class="block">{html_table(config["table"])}</section>' if config.get("table") else ""
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{dashboard_title}</title>
{echarts_tag}
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <div class="report-header"><h1>{dashboard_title}</h1></div>
  {f'<section class="block">{metrics_html}</section>' if metrics_html else ''}
  <section class="block"><div class="charts-grid">{charts_html}</div></section>
  {table_html}
</div>
<script>
{init}
window.addEventListener('resize',function(){{{resize}}});
</script>
</body>
</html>"""


def render_single_html(option, title, echarts_tag):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{echarts_tag}
<style>{BASE_CSS}</style>
</head>
<body>
<div class="wrap">
  <section class="block"><div id="chart" class="chart" style="height:480px;"></div></section>
</div>
<script>
var chart = echarts.init(document.getElementById('chart'));
chart.setOption({json.dumps(option, ensure_ascii=False)});
window.addEventListener('resize', function() {{ chart.resize(); }});
</script>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(description='教学分析 HTML 渲染引擎（自包含单文件）')
    parser.add_argument('--report', action='store_true', help='报告模式（主交付物）：结论+KPI+图表+表格汇总为单个 HTML')
    parser.add_argument('--dashboard', action='store_true', help='看板模式：多图并排')
    parser.add_argument('--chart-type', help='单图模式: line/bar/pie/scatter/histogram/boxplot/radar/heatmap')
    parser.add_argument('--config', help='报告/看板结构 JSON 路径')
    parser.add_argument('--data', help='单图/看板的 JSON 数据路径')
    parser.add_argument('--title', default='数据图表')
    parser.add_argument('--x-axis')
    parser.add_argument('--y-axis', nargs='+')
    parser.add_argument('--output', default='report.html', help='输出 HTML 路径')
    args = parser.parse_args()

    echarts_tag, inline = load_echarts_runtime()

    if args.report:
        if not args.config:
            print("错误：报告模式需要 --config", file=sys.stderr)
            sys.exit(1)
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        html = render_report_html(config, echarts_tag)
    elif args.dashboard:
        if not args.config:
            print("错误：看板模式需要 --config", file=sys.stderr)
            sys.exit(1)
        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)
        data = load_data(args.data) if args.data else []
        html = render_dashboard_html(config, data, echarts_tag)
    else:
        if not args.chart_type or not args.data:
            print("错误：单图模式需要 --chart-type 和 --data", file=sys.stderr)
            sys.exit(1)
        data = load_data(args.data)
        builder = CHART_BUILDERS.get(args.chart_type)
        if not builder:
            print(f"错误：不支持的图表类型 '{args.chart_type}'，支持: {', '.join(CHART_BUILDERS)}", file=sys.stderr)
            sys.exit(1)
        option = builder(data, args.title, args.x_axis or "", args.y_axis or [])
        html = render_single_html(option, args.title, echarts_tag)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    size_kb = len(html.encode('utf-8')) / 1024
    print(f"已生成: {args.output} ({size_kb:.0f} KB, {'内联ECharts离线可用' if inline else 'CDN依赖网络'})")


if __name__ == "__main__":
    main()
