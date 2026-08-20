#!/usr/bin/env python3
"""ECharts HTML 渲染引擎。接收 JSON 数据和图表配置，输出交互式 HTML 文件。"""

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


# ═══════════════════════════════════════════════════════════════
# 图表构建器
# ═══════════════════════════════════════════════════════════════

def build_line_option(data, title, x_axis, y_axes):
    x_data = [row[x_axis] for row in data]
    series = []
    for i, y in enumerate(y_axes):
        series.append({
            "name": y,
            "type": "line",
            "data": [row.get(y) for row in data],
            "smooth": True,
            "symbolSize": 4,
        })
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
    for i, y in enumerate(y_axes):
        series.append({
            "name": y,
            "type": "bar",
            "data": [row.get(y) for row in data],
            "barMaxWidth": 40,
        })
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
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c} ({d}%)"},
        "legend": {"orient": "vertical", "left": 10, "top": 50},
        "series": [{
            "type": "pie",
            "radius": ["40%", "68%"],
            "center": ["58%", "55%"],
            "data": pie_data,
            "label": {"formatter": "{b}\n{d}%", "fontSize": 11},
        }],
    }
    return option


def build_scatter_option(data, title, x_axis, y_axes):
    y_col = y_axes[0]
    scatter_data = [[row.get(x_axis), row.get(y_col)] for row in data]
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "xAxis": {"type": "value", "name": x_axis, "nameLocation": "center", "nameGap": 28, "splitLine": {"lineStyle": {"type": "dashed"}}},
        "yAxis": {"type": "value", "name": y_col, "nameLocation": "center", "nameGap": 36, "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": [{"type": "scatter", "data": scatter_data, "symbolSize": 10}],
    }
    return option


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
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": labels, "name": col},
        "yAxis": {"type": "value", "name": "频数", "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": [{"type": "bar", "data": bins, "barWidth": "80%"}],
    }
    return option


def build_boxplot_option(data, title, x_axis, y_axes):
    cols = y_axes if y_axes else [k for k in data[0].keys() if isinstance(data[0].get(k), (int, float))]
    box_data = []
    for col in cols:
        values = sorted([row[col] for row in data if row.get(col) is not None])
        if len(values) < 5:
            continue
        n = len(values)
        q1 = values[n // 4]
        median = values[n // 2]
        q3 = values[3 * n // 4]
        iqr = q3 - q1
        low = max(values[0], q1 - 1.5 * iqr)
        high = min(values[-1], q3 + 1.5 * iqr)
        box_data.append([low, q1, median, q3, high])
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "grid": {"left": 60, "right": 30, "bottom": 50},
        "xAxis": {"type": "category", "data": cols},
        "yAxis": {"type": "value", "splitLine": {"lineStyle": {"type": "dashed"}}},
        "series": [{"type": "boxplot", "data": box_data}],
    }
    return option


def build_radar_option(data, title, x_axis, y_axes):
    max_val = 0
    for row in data:
        for y in y_axes:
            v = row.get(y, 0) or 0
            if v > max_val:
                max_val = v
    indicators = [{"name": row[x_axis], "max": max_val * 1.2} for row in data]
    series_data = []
    for i, y in enumerate(y_axes):
        series_data.append({
            "name": y,
            "value": [row.get(y, 0) for row in data],
        })
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "legend": {"top": 30, "data": y_axes},
        "radar": {"indicator": indicators, "center": ["50%", "58%"], "radius": "60%"},
        "series": [{"type": "radar", "data": series_data}],
    }
    return option


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
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"position": "top"},
        "grid": {"top": 50, "bottom": 50, "left": 70, "right": 30},
        "xAxis": {"type": "category", "data": x_cats, "splitArea": {"show": True}},
        "yAxis": {"type": "category", "data": y_cats, "splitArea": {"show": True}},
        "visualMap": {"min": min(all_vals) if all_vals else 0, "max": max(all_vals) if all_vals else 1, "calculable": True, "orient": "horizontal", "left": "center", "bottom": 8},
        "series": [{"type": "heatmap", "data": heat_data, "label": {"show": len(heat_data) < 100, "fontSize": 10}}],
    }
    return option


def build_funnel_option(data, title, x_axis, y_axes):
    y_col = y_axes[0]
    funnel_data = [{"name": str(row[x_axis]), "value": row.get(y_col)} for row in data]
    funnel_data.sort(key=lambda x: x["value"] or 0, reverse=True)
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {c}"},
        "series": [{
            "type": "funnel",
            "left": "15%", "width": "70%", "top": 50, "bottom": 20,
            "data": funnel_data,
            "label": {"formatter": "{b}\n{c}", "fontSize": 11},
        }],
    }
    return option


def build_treemap_option(data, title, x_axis, y_axes):
    y_col = y_axes[0]
    tree_data = [{"name": str(row[x_axis]), "value": row.get(y_col)} for row in data]
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"formatter": "{b}: {c}"},
        "series": [{
            "type": "treemap",
            "data": tree_data,
            "top": 40,
            "label": {"formatter": "{b}\n{c}", "fontSize": 11},
            "breadcrumb": {"show": False}
        }],
    }
    return option


def build_sunburst_option(data, title, x_axis, y_axes):
    y_col = y_axes[0]
    sb_data = [{"name": str(row[x_axis]), "value": row.get(y_col)} for row in data]
    option = {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 15, "fontWeight": 600}},
        "tooltip": {"trigger": "item"},
        "series": [{
            "type": "sunburst",
            "data": sb_data,
            "radius": ["20%", "72%"],
            "label": {"rotate": "radial", "fontSize": 10},
        }],
    }
    return option


CHART_BUILDERS = {
    "line": build_line_option,
    "bar": build_bar_option,
    "pie": build_pie_option,
    "scatter": build_scatter_option,
    "histogram": build_histogram_option,
    "boxplot": build_boxplot_option,
    "radar": build_radar_option,
    "heatmap": build_heatmap_option,
    "funnel": build_funnel_option,
    "treemap": build_treemap_option,
    "sunburst": build_sunburst_option,
}


# ═══════════════════════════════════════════════════════════════
# HTML 模板
# ═══════════════════════════════════════════════════════════════

def render_single_html(option_json, title="数据图表"):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script src="{ECHARTS_CDN}"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #fafafa; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }}
.panel {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 24px; width: 100%; max-width: 960px; }}
.chart {{ width: 100%; height: 480px; }}
@media (max-width: 768px) {{ .chart {{ height: 360px; }} }}
</style>
</head>
<body>
<div class="panel">
  <div id="chart" class="chart"></div>
</div>
<script>
var chart = echarts.init(document.getElementById('chart'));
var option = {option_json};
chart.setOption(option);
window.addEventListener('resize', function() {{ chart.resize(); }});
</script>
</body>
</html>"""


def build_metric_card_html(metrics):
    if not metrics:
        return ""
    status_colors = {"danger": "#e53e3e", "warning": "#d69e2e", "success": "#38a169"}
    cards = ""
    for m in metrics[:6]:
        status = m.get('status', '')
        border_color = status_colors.get(status, '#d1d5db')
        cards += f"""
      <div class="metric-card" style="border-left: 3px solid {border_color};">
        <div class="metric-label">{m.get('label', '')}</div>
        <div class="metric-value">{m.get('value', '')}</div>
      </div>"""
    return f'<div class="metrics-row">{cards}\n    </div>'


def build_insights_html(insights):
    if not insights:
        return ""
    items = ""
    for ins in insights:
        level = ins.get('level', '')
        marker = "!" if level == "danger" else "~" if level == "warning" else "-"
        items += f'<li class="insight-{level or "info"}">{marker} {ins.get("text", "")}</li>'
    return f'<div class="insights-section"><ul>{items}</ul></div>'


def build_table_html(table_config):
    if not table_config:
        return ""
    title = table_config.get('title', '数据明细')
    columns = table_config.get('columns', [])
    data = table_config.get('data', [])
    header = "".join(f"<th>{col}</th>" for col in columns)
    rows = ""
    for row in data:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        rows += f"<tr>{cells}</tr>"
    return f"""
    <div class="table-section">
      <h3>{title}</h3>
      <table>
        <thead><tr>{header}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""


def render_dashboard_html(options, dashboard_title="数据看板", metrics=None, insights=None, table=None):
    charts_html = ""
    init_scripts = ""
    for i, opt in enumerate(options):
        charts_html += f'    <div class="chart-panel"><div id="chart{i}" class="chart"></div></div>\n'
        init_scripts += f"var c{i}=echarts.init(document.getElementById('chart{i}'));c{i}.setOption({json.dumps(opt, ensure_ascii=False)});\n"

    resize_script = ";".join(f"c{i}.resize()" for i in range(len(options)))
    metrics_html = build_metric_card_html(metrics) if metrics else ""
    insights_html = build_insights_html(insights) if insights else ""
    table_html = build_table_html(table) if table else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{dashboard_title}</title>
<script src="{ECHARTS_CDN}"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #fafafa; color: #1a1a1a; line-height: 1.5; padding: 24px; }}
.dashboard {{ max-width: 1200px; margin: 0 auto; }}
.dashboard-header {{ margin-bottom: 20px; }}
.dashboard-header h1 {{ font-size: 18px; font-weight: 600; }}
.dashboard-header p {{ font-size: 12px; color: #666; margin-top: 2px; }}
.metrics-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 20px; }}
.metric-card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 14px 16px; }}
.metric-label {{ font-size: 12px; color: #666; margin-bottom: 4px; }}
.metric-value {{ font-size: 18px; font-weight: 600; }}
.insights-section {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 14px 18px; margin-bottom: 20px; }}
.insights-section ul {{ list-style: none; padding: 0; }}
.insights-section li {{ font-size: 13px; padding: 4px 0; color: #333; }}
.insights-section .insight-danger {{ color: #c53030; }}
.insights-section .insight-warning {{ color: #975a16; }}
.charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 16px; margin-bottom: 20px; }}
.chart-panel {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 16px; }}
.chart {{ width: 100%; height: 340px; }}
.table-section {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 4px; padding: 16px 18px; margin-bottom: 20px; }}
.table-section h3 {{ font-size: 14px; font-weight: 600; margin-bottom: 10px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
th {{ padding: 8px 10px; text-align: left; font-weight: 600; color: #666; border-bottom: 1px solid #d1d5db; }}
td {{ padding: 8px 10px; border-bottom: 1px solid #f0f0f0; }}
@media (max-width: 768px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<div class="dashboard">
  <div class="dashboard-header">
    <h1>{dashboard_title}</h1>
    <p>数据可视化看板</p>
  </div>
  {metrics_html}
  {insights_html}
  <div class="charts-grid">
{charts_html}  </div>
  {table_html}
</div>
<script>
{init_scripts}window.addEventListener('resize',function(){{{resize_script}}});
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

def auto_metrics_from_data(data):
    if not data:
        return []
    metrics = []
    metrics.append({"label": "数据行数", "value": f"{len(data):,}"})
    numeric_cols = [k for k, v in data[0].items() if isinstance(v, (int, float))]
    for col in numeric_cols[:3]:
        vals = [row.get(col) for row in data if row.get(col) is not None]
        if vals:
            total = sum(vals)
            if total > 10000:
                metrics.append({"label": f"{col}总计", "value": f"{total:,.0f}"})
            else:
                metrics.append({"label": f"{col}均值", "value": f"{sum(vals)/len(vals):,.1f}"})
    return metrics


def main():
    parser = argparse.ArgumentParser(description='ECharts HTML 渲染引擎')
    parser.add_argument('--data', required=True, help='JSON 数据文件路径')
    parser.add_argument('--chart-type', help='图表类型: line/bar/pie/scatter/histogram/boxplot/radar/heatmap/funnel/treemap/sunburst')
    parser.add_argument('--title', default='数据图表', help='图表标题')
    parser.add_argument('--x-axis', help='X轴字段名')
    parser.add_argument('--y-axis', nargs='+', help='Y轴字段名（可多个）')
    parser.add_argument('--output', default='chart.html', help='输出HTML文件路径')
    parser.add_argument('--dashboard', action='store_true', help='仪表板模式')
    parser.add_argument('--config', help='仪表板配置JSON文件路径')

    args = parser.parse_args()
    data = load_data(args.data)

    if args.dashboard:
        if not args.config:
            print("错误：仪表板模式需要 --config 参数", file=sys.stderr)
            sys.exit(1)

        with open(args.config, 'r', encoding='utf-8') as f:
            config = json.load(f)

        dashboard_title = config.get("title", "数据看板")
        options = []
        for chart_cfg in config["charts"]:
            ct = chart_cfg["type"]
            builder = CHART_BUILDERS.get(ct)
            if not builder:
                print(f"警告：不支持的图表类型 {ct}，跳过", file=sys.stderr)
                continue
            y_axis = chart_cfg.get("y_axis", [])
            if isinstance(y_axis, str):
                y_axis = [y_axis]
            chart_title = chart_cfg.get("title", "")
            subtitle = chart_cfg.get("subtitle", "")
            opt = builder(data, chart_title, chart_cfg.get("x_axis", ""), y_axis)
            if subtitle:
                opt["title"]["subtext"] = subtitle
                opt["title"]["subtextStyle"] = {"fontSize": 12, "color": "#8c8c8c"}
            options.append(opt)

        metrics = config.get("metrics") or auto_metrics_from_data(data)
        insights = config.get("insights")
        table = config.get("table")
        html = render_dashboard_html(options, dashboard_title, metrics, insights, table)
    else:
        if not args.chart_type:
            print("错误：需要 --chart-type 参数", file=sys.stderr)
            sys.exit(1)
        builder = CHART_BUILDERS.get(args.chart_type)
        if not builder:
            supported = ', '.join(CHART_BUILDERS.keys())
            print(f"错误：不支持的图表类型 '{args.chart_type}'，支持: {supported}", file=sys.stderr)
            sys.exit(1)

        y_axes = args.y_axis or []
        option = builder(data, args.title, args.x_axis or "", y_axes)
        option_json = json.dumps(option, ensure_ascii=False)
        html = render_single_html(option_json, args.title)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"已生成: {args.output}")


if __name__ == "__main__":
    main()
