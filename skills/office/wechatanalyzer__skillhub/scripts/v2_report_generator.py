#!/usr/bin/env python3
"""
v2 报告生成器

生成完全自包含的单文件 HTML 分析报告：
- 内联 CSS + Python 生成的 SVG 图表（雷达图/环形图/条形图）
- 禁止任何 CDN / 外部资源，离线可开
- 中文界面，现代清爽风格

同时提供 generate_v2_summary() 生成"一句话总结"，
供终端报告（analyze-v2）与 HTML 报告共用。
"""

import html
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# v2.5.0：报告标题/页脚版本号统一读取，避免升级时漏改
from core.version import __version__


# ============== 一句话总结（终端/HTML 共用）==============

def generate_v2_summary(results: Dict[str, Dict[str, Any]]) -> str:
    """基于各分析器结果生成 1-2 句中文总结（规则生成）

    Args:
        results: {analyzer_name: AnalysisResult.to_dict()}

    Returns:
        总结文本，如 "对方偏外向感性，聊天氛围积极，未发现风险信号。建议保持当前互动节奏。"
    """
    def details(name: str) -> Dict[str, Any]:
        return (results.get(name) or {}).get("details", {}) or {}

    # 性格画像（MBTI E/I + F/T）
    trait = ""
    mbti = details("mbti")
    mbti_type = mbti.get("type", "") or ""
    if mbti_type and mbti_type != "未知":
        t1 = "偏外向" if mbti_type.startswith("E") else (
            "偏内向" if mbti_type.startswith("I") else "")
        t2 = "感性" if "F" in mbti_type else ("理性" if "T" in mbti_type else "")
        if t1 or t2:
            trait = f"对方{t1}{t2}"

    # 聊天氛围（情感占比）
    sent = details("sentiment")
    pos = float(sent.get("positive", 0) or 0)
    neg = float(sent.get("negative", 0) or 0)
    if pos >= 40 and pos >= neg * 1.5:
        mood = "聊天氛围积极"
    elif neg >= 40 and neg >= pos * 1.5:
        mood = "聊天氛围偏消极"
    else:
        mood = "聊天氛围平稳"

    # 风险信号
    risk = details("risk")
    level = risk.get("overall_level", "low")
    if level == "high":
        risk_part = "检测到高风险信号，需重点留意"
    elif level == "medium":
        risk_part = "发现少量风险提示，建议适当留意"
    else:
        risk_part = "未发现风险信号"

    first = "，".join(p for p in [trait, mood, risk_part] if p)

    # 建议
    if level == "high":
        advice = "建议提高警惕，涉及钱财、隐私的话题务必核实对方身份。"
    elif level == "medium":
        advice = "建议保持理性判断，留意对话中的异常引导。"
    elif mood == "聊天氛围偏消极":
        advice = "建议主动关心对方状态，放缓互动节奏。"
    else:
        advice = "建议保持当前互动节奏。"

    return f"{first}。{advice}" if first else advice


# ============== HTML 报告生成器 ==============

class V2ReportGenerator:
    """v2.1.0 单文件 HTML 报告生成器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        project_root = Path(__file__).resolve().parent.parent
        self.reports_dir = project_root / self.config.get("reports_dir", "data/reports")

    # ---------- 公开接口 ----------

    def generate(self, results: Dict[str, Dict[str, Any]],
                 meta: Optional[Dict[str, Any]] = None,
                 output_path: Optional[str] = None) -> str:
        """生成 HTML 报告

        Args:
            results: {analyzer_name: AnalysisResult.to_dict()}
            meta: 消息统计元数据（total_messages / self_messages / other_messages 等）
            output_path: 输出路径，默认 data/reports/v2_report_<时间戳>.html

        Returns:
            生成的文件绝对路径
        """
        meta = meta or {}
        if output_path is None:
            self.reports_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = str(self.reports_dir / f"v2_report_{ts}.html")
        else:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        body = self._render_body(results, meta, generated_at)
        page = _HTML_TEMPLATE.replace("{{TITLE}}", f"微信聊天分析报告 v{__version__}") \
                             .replace("{{BODY}}", body)
        Path(output_path).write_text(page, encoding="utf-8")
        return str(Path(output_path).resolve())

    # ---------- 渲染 ----------

    def _render_body(self, results: Dict[str, Dict[str, Any]],
                     meta: Dict[str, Any], generated_at: str) -> str:
        def details(name: str) -> Dict[str, Any]:
            return (results.get(name) or {}).get("details", {}) or {}

        sections: List[str] = []

        # 头部
        total = meta.get("total_messages")
        meta_line = f"共 {total} 条消息 · " if total else ""
        sections.append(f"""
<header>
  <h1>微信聊天分析报告</h1>
  <p class="sub">{html.escape(meta_line + "生成时间 " + generated_at)}</p>
</header>""")

        # 一句话总结
        summary = generate_v2_summary(results)
        sections.append(f"""
<div class="card summary-card">
  <div class="card-title">一句话总结</div>
  <p class="summary-text">{html.escape(summary)}</p>
</div>""")

        # MBTI 卡片
        mbti = details("mbti")
        if mbti:
            conf = (results.get("mbti") or {}).get("confidence", 0)
            stability = mbti.get("stability")
            stab_html = ""
            if stability is not None:
                stab_pct = round(float(stability) * 100)
                stab_html = f'<div class="kv"><span>稳定性</span><b>{stab_pct}%</b></div>'
                if stab_pct < 50:
                    stab_html += ('<p class="hint">样本较少或特征不明显，'
                                  '结果仅供参考</p>')
            sections.append(f"""
<div class="card">
  <div class="card-title">MBTI 人格</div>
  <div class="mbti-type">{html.escape(str(mbti.get('type', '未知')))}
    <span class="mbti-name">{html.escape(str(mbti.get('name', '')))}</span></div>
  <div class="kv"><span>置信度</span><b>{conf:.0f}%</b></div>
  <div class="kv"><span>特征</span><b>{html.escape(str(mbti.get('dim_description', '')))}</b></div>
  {stab_html}
</div>""")

        # 大五雷达图
        bf = details("bigfive")
        radar = bf.get("radar_data") or []
        if radar:
            sections.append(f"""
<div class="card">
  <div class="card-title">大五人格（OCEAN）</div>
  <div class="chart-wrap">{_svg_radar(radar)}</div>
</div>""")

        # 情感：环形图 + 高频词条形图
        sent = details("sentiment")
        if sent:
            pos = float(sent.get("positive", 0) or 0)
            neg = float(sent.get("negative", 0) or 0)
            neu = float(sent.get("neutral", 0) or 0)
            ew = sent.get("emotional_words", {}) or {}
            pos_words = ew.get("positive", [])[:8]
            neg_words = ew.get("negative", [])[:8]
            trend_map = {"up": "上升 ↗", "down": "下降 ↘", "stable": "平稳 →"}
            word_bars = ""
            if pos_words or neg_words:
                word_bars = '<div class="word-cols">'
                if pos_words:
                    word_bars += ('<div><h4>正面高频词</h4>'
                                  + _word_bars(pos_words, "pos") + '</div>')
                if neg_words:
                    word_bars += ('<div><h4>负面高频词</h4>'
                                  + _word_bars(neg_words, "neg") + '</div>')
                word_bars += '</div>'
            sections.append(f"""
<div class="card">
  <div class="card-title">情感分析 <span class="tag">趋势：{trend_map.get(sent.get('trend', 'stable'), '平稳')}</span></div>
  <div class="chart-wrap">{_svg_donut(pos, neg, neu)}</div>
  {word_bars}
</div>""")

        # 对话模式统计卡片
        pat = details("pattern")
        if pat:
            init = pat.get("initiation", {}) or {}
            rs = pat.get("reply_speed", {}) or {}
            duration = pat.get("duration_days")
            cells = [
                ("主动发起（我）", f"{init.get('self_pct', 0):.0f}%"),
                ("主动发起（TA）", f"{init.get('other_pct', 0):.0f}%"),
                ("平均回复速度", f"{rs.get('avg_seconds', 0):.0f} 秒"),
                ("快速回复(&lt;1分钟)", str(rs.get("fast_replies", 0))),
                ("慢速回复(&gt;1小时)", str(rs.get("slow_replies", 0))),
            ]
            if duration is not None:
                cells.append(("聊天跨度", f"{duration} 天"))
            grid = "".join(
                f'<div class="stat"><div class="stat-v">{v}</div>'
                f'<div class="stat-k">{k}</div></div>' for k, v in cells)
            sections.append(f"""
<div class="card">
  <div class="card-title">对话模式</div>
  <div class="stat-grid">{grid}</div>
</div>""")

        # 风险卡片（分级配色）
        risk = details("risk")
        if risk:
            level = risk.get("overall_level", "low")
            level_cn = {"low": "低", "medium": "中", "high": "高"}.get(level, "低")
            risks = risk.get("risks", {}) or {}
            items = ""
            if risks:
                lis = []
                for rtype, data in risks.items():
                    lv = data.get("level", "low")
                    desc = html.escape(str(data.get("description", "")))
                    lis.append(f'<li><span class="badge badge-{lv}">'
                               f'{ {"low":"低","medium":"中","high":"高"}.get(lv,"低") }'
                               f'</span> <b>{html.escape(str(rtype))}</b> {desc}</li>')
                items = f'<ul class="risk-list">{"".join(lis)}</ul>'
            else:
                items = '<p class="ok-text">未检测到明显风险</p>'
            sections.append(f"""
<div class="card risk-{level}">
  <div class="card-title">风险预警 <span class="badge badge-{level}">综合等级：{level_cn}</span></div>
  {items}
</div>""")

        # 场景权重条形图
        scen = details("scenario")
        sorted_scen = scen.get("sorted") or []
        if sorted_scen:
            name_map = {"romantic": "恋爱", "work": "工作",
                        "social": "社交", "important": "重要"}
            max_w = max((s.get("weight", 0) for s in sorted_scen), default=1) or 1
            bars = "".join(
                f'''<div class="bar-row">
  <span class="bar-label">{name_map.get(s.get("scenario"), s.get("scenario"))}</span>
  <div class="bar-track"><div class="bar-fill" style="width:{s.get("weight", 0) / max_w * 100:.0f}%"></div></div>
  <span class="bar-val">{s.get("weight", 0)}</span>
</div>''' for s in sorted_scen)
            primary_cn = name_map.get(scen.get("primary"), scen.get("primary", ""))
            sections.append(f"""
<div class="card">
  <div class="card-title">对话场景 <span class="tag">主场景：{html.escape(str(primary_cn))}</span></div>
  {bars}
</div>""")

        sections.append(f'<footer>由微信聊天分析助手 v{__version__} 本地生成 · 数据未离开本机</footer>')
        return "\n".join(sections)


# ============== SVG 图表（Python 生成，零外部依赖）==============

def _svg_radar(radar_data: List[Dict[str, Any]], size: int = 320) -> str:
    """大五人格雷达图（SVG）"""
    n = len(radar_data)
    if n < 3:
        return ""
    cx = cy = size / 2
    radius = size / 2 - 56

    def point(i: int, value: float) -> tuple:
        angle = -math.pi / 2 + 2 * math.pi * i / n
        r = radius * max(0.0, min(100.0, value)) / 100.0
        return cx + r * math.cos(angle), cy + r * math.sin(angle)

    # 背景网格（25/50/75/100%）
    grids = ""
    for pct in (25, 50, 75, 100):
        pts = " ".join(f"{point(i, pct)[0]:.1f},{point(i, pct)[1]:.1f}" for i in range(n))
        grids += f'<polygon points="{pts}" fill="none" stroke="#e5e7eb" stroke-width="1"/>'
    # 轴线 + 标签
    axes = ""
    for i, item in enumerate(radar_data):
        x, y = point(i, 100)
        axes += f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#e5e7eb"/>'
        lx, ly = point(i, 122)
        anchor = "middle"
        if lx > cx + 5:
            anchor = "start"
        elif lx < cx - 5:
            anchor = "end"
        label = html.escape(str(item.get("label", "")))
        value = float(item.get("value", 0) or 0)
        axes += (f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                 f'font-size="12" fill="#374151">{label} {value:.0f}%</text>')
    # 数据多边形
    data_pts = " ".join(
        f"{point(i, float(item.get('value', 0) or 0))[0]:.1f},"
        f"{point(i, float(item.get('value', 0) or 0))[1]:.1f}"
        for i, item in enumerate(radar_data))
    polygon = (f'<polygon points="{data_pts}" fill="rgba(99,102,241,0.25)" '
               f'stroke="#6366f1" stroke-width="2"/>')
    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
            f'role="img" aria-label="大五人格雷达图">{grids}{axes}{polygon}</svg>')


def _svg_donut(positive: float, negative: float, neutral: float,
               size: int = 200) -> str:
    """情感占比环形图（SVG，stroke-dasharray 画法）"""
    total = positive + negative + neutral
    if total <= 0:
        positive, negative, neutral, total = 0.0, 0.0, 100.0, 100.0
    r = 70.0
    circumference = 2 * math.pi * r
    segs = [
        (positive / total, "#22c55e", "正面"),
        (negative / total, "#ef4444", "负面"),
        (neutral / total, "#d1d5db", "中性"),
    ]
    offset = 0.0
    circles = ""
    for frac, color, _label in segs:
        dash = frac * circumference
        circles += (f'<circle cx="100" cy="100" r="{r}" fill="none" stroke="{color}" '
                    f'stroke-width="26" stroke-dasharray="{dash:.2f} {circumference - dash:.2f}" '
                    f'stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 100 100)"/>')
        offset += dash
    center = (f'<text x="100" y="94" text-anchor="middle" font-size="22" '
              f'font-weight="bold" fill="#111827">{positive:.0f}%</text>'
              f'<text x="100" y="116" text-anchor="middle" font-size="12" '
              f'fill="#6b7280">正面</text>')
    legend = "".join(
        f'<span class="lg"><i style="background:{c}"></i>{l} '
        f'{v:.0f}%</span>'
        for (frac, c, l), v in zip(segs, [positive, negative, neutral]))
    return (f'<svg viewBox="0 0 200 200" width="{size}" height="{size}" '
            f'role="img" aria-label="情感占比环形图">{circles}{center}</svg>'
            f'<div class="legend">{legend}</div>')


def _word_bars(words: List[str], kind: str) -> str:
    """高频词条形图（HTML div）"""
    color = "#22c55e" if kind == "pos" else "#ef4444"
    rows = []
    n = len(words)
    for i, w in enumerate(words):
        width = round((n - i) / n * 100)
        rows.append(
            f'<div class="bar-row"><span class="bar-label">{html.escape(str(w))}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width}%;'
            f'background:{color}"></div></div></div>')
    return "".join(rows)


# ============== 自包含 HTML 模板（内联 CSS，无外部资源）==============

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
         background: #f3f4f6; color: #111827; line-height: 1.6; padding: 24px; }
  header { text-align: center; margin-bottom: 24px; }
  header h1 { font-size: 26px; letter-spacing: 2px; }
  header .sub { color: #6b7280; font-size: 13px; margin-top: 6px; }
  .card { background: #fff; border-radius: 14px; padding: 20px 22px;
          margin: 0 auto 18px; max-width: 720px;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }
  .card-title { font-size: 16px; font-weight: 700; margin-bottom: 12px;
                display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .summary-card { border-left: 5px solid #6366f1; }
  .summary-text { font-size: 15px; }
  .mbti-type { font-size: 34px; font-weight: 800; color: #6366f1; margin-bottom: 8px; }
  .mbti-name { font-size: 15px; color: #6b7280; font-weight: 400; margin-left: 8px; }
  .kv { display: flex; justify-content: space-between; padding: 4px 0;
        border-bottom: 1px dashed #f0f0f0; font-size: 14px; }
  .kv span { color: #6b7280; }
  .hint { margin-top: 8px; font-size: 12px; color: #b45309; background: #fffbeb;
          border-radius: 6px; padding: 6px 10px; }
  .chart-wrap { display: flex; flex-direction: column; align-items: center; }
  .legend { display: flex; gap: 16px; justify-content: center; margin-top: 8px;
            font-size: 13px; color: #374151; }
  .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px;
              margin-right: 4px; }
  .word-cols { display: flex; gap: 24px; margin-top: 14px; flex-wrap: wrap; }
  .word-cols > div { flex: 1; min-width: 220px; }
  .word-cols h4 { font-size: 13px; color: #6b7280; margin-bottom: 6px; }
  .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
               gap: 12px; }
  .stat { background: #f9fafb; border-radius: 10px; padding: 12px; text-align: center; }
  .stat-v { font-size: 20px; font-weight: 700; color: #111827; }
  .stat-k { font-size: 12px; color: #6b7280; margin-top: 2px; }
  .bar-row { display: flex; align-items: center; gap: 8px; margin: 6px 0; font-size: 13px; }
  .bar-label { width: 90px; text-align: right; color: #374151; flex-shrink: 0; }
  .bar-track { flex: 1; background: #f3f4f6; border-radius: 6px; height: 14px;
               overflow: hidden; }
  .bar-fill { height: 100%; background: #6366f1; border-radius: 6px; }
  .bar-val { width: 36px; color: #6b7280; flex-shrink: 0; }
  .tag { font-size: 12px; font-weight: 400; color: #4f46e5; background: #eef2ff;
         border-radius: 999px; padding: 2px 10px; }
  .badge { font-size: 12px; border-radius: 999px; padding: 2px 10px; font-weight: 600; }
  .badge-low { background: #ecfdf5; color: #047857; }
  .badge-medium { background: #fffbeb; color: #b45309; }
  .badge-high { background: #fef2f2; color: #b91c1c; }
  .risk-low { border-left: 5px solid #22c55e; }
  .risk-medium { border-left: 5px solid #f59e0b; }
  .risk-high { border-left: 5px solid #ef4444; }
  .risk-list { list-style: none; }
  .risk-list li { padding: 6px 0; font-size: 14px; border-bottom: 1px dashed #f0f0f0; }
  .ok-text { color: #047857; font-size: 14px; }
  footer { text-align: center; color: #9ca3af; font-size: 12px; margin: 24px 0 8px; }
</style>
</head>
<body>
{{BODY}}
</body>
</html>
"""
