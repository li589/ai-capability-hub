#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户画像与人群洞察 · 白皮书级 HTML 报告渲染

与 render_output.py 配套：读同一份数据 JSON（+可选 case.json 元），渲染成
editorial 风格的 report.html（封面 / 执行摘要 / 关键数据 / 雷达图 / 人物卡 / 洞察）。

用法:
  python3 render_report.py <data.json> --out <report.html> [--meta <case.json>]

  - data.json：render_output.py 用的同一份数据 JSON（必填）。
  --out：     输出 HTML 路径（必填）。
  --meta：    可选 case.json（playbook 案例时提供，用于封面标题/标签/质审分；
              普通运行不传则用数据 JSON 里的 report 块或默认值）。

可选 report 块（写在 data.json 顶层，render_output.py 会忽略，本脚本消费）：
  "report": {
    "title":"封面标题","subtitle":"封面副标题",
    "kpis":[{"num":"9200万+","label":"累计会员"}],
    "exec":{"findings":[{"icon":"📈","title":"...","text":"..."}],
            "recs":[{"pri":"P0","title":"...","text":"..."}]}
  }
未提供 report 块时，本脚本从 dimensions/projects 自动派生（绝不报错）。

纯标准库。退出码：0 成功 / 1 参数错误 / 2 读文件或解析失败 / 3 写盘失败。
"""
import argparse, json, math, sys, html
from pathlib import Path


def esc(s):
    return html.escape(str(s))


def sc(s):
    s = float(s)
    return "#2f7d5b" if s >= 4 else ("#b06a1e" if s == 3 else "#a8324a")


def pbadge(p):
    m = {"P0": ("#a8324a", "#fff0f3"), "P1": ("#b06a1e", "#fff7ea"), "P2": ("#3d5a80", "#eef3fa")}
    fg, bg = m.get(p, ("#6b7280", "#f1f3f5"))
    return f'<span class="pri" style="color:{fg};background:{bg}">{esc(p)}</span>'


def radar_svg(dims, R=130, cx=170, cy=160):
    n = len(dims)
    ang = lambda i: -math.pi / 2 + 2 * math.pi * i / n
    grid = ""
    for lvl in (1, 2, 3, 4, 5):
        pts = " ".join(f"{cx+lvl/5*R*math.cos(ang(i)):.1f},{cy+lvl/5*R*math.sin(ang(i)):.1f}" for i in range(n))
        grid += f'<polygon points="{pts}" fill="none" stroke="#e4ddd0" stroke-width="1"/>'
    axes = "".join(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx+R*math.cos(ang(i)):.1f}" y2="{cy+R*math.sin(ang(i)):.1f}" stroke="#e4ddd0" stroke-width="1"/>' for i in range(n))
    dp = [(cx + d["score"] / 5 * R * math.cos(ang(i)), cy + d["score"] / 5 * R * math.sin(ang(i))) for i, d in enumerate(dims)]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in dp)
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#b08a3e"/>' for x, y in dp)
    lab = ""
    for i, d in enumerate(dims):
        lx, ly = cx + (R + 30) * math.cos(ang(i)), cy + (R + 30) * math.sin(ang(i))
        anc = "middle"
        if math.cos(ang(i)) > 0.4:
            anc = "start"
        elif math.cos(ang(i)) < -0.4:
            anc = "end"
        lab += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anc}" dominant-baseline="middle" class="rlabel">{esc(d["name"])}</text>'
        lab += f'<text x="{lx:.1f}" y="{ly+16:.1f}" text-anchor="{anc}" dominant-baseline="middle" class="rscore" style="fill:{sc(d["score"])}">{d["score"]}/5</text>'
    return f'<svg viewBox="0 0 340 360" class="radar">{grid}{axes}<polygon points="{poly}" fill="#b08a3e" fill-opacity="0.18" stroke="#b08a3e" stroke-width="2"/>{dots}{lab}</svg>'


def derive(D):
    """未提供 report 块时的兜底派生：KPI / 执行摘要。"""
    mat = D["maturity"]
    kpis = [{"num": f'{mat["score"]:g}/5', "label": f'画像就绪度 · {mat["stage"]}'},
            {"num": str(len(D["dimensions"])), "label": "评估维度"}]
    # 从 dimensions current_value 里捞带数字的当 KPI（最多 4 个）
    import re
    for d in D["dimensions"]:
        cv = d.get("current_value", "")
        if re.search(r"\d", cv) and len(kpis) < 6:
            kpis.append({"num": cv.split("；")[0][:12], "label": d["name"]})
    # findings：低分维度（score<=3）
    findings = []
    ico = {0: "⚠️", 1: "⚠️", 2: "📉", 3: "🎯"}
    for d in D["dimensions"]:
        if d["score"] <= 3:
            findings.append({"icon": ico.get(d["score"], "📌"), "title": f'{d["name"]}待提升（{d["score"]}/5）',
                             "text": f'{d["problem"]} → {d["impact"]}'})
    if not findings:
        findings = [{"icon": "📊", "title": "整体就绪度", "text": mat["summary"]}]
    # recs：P0 项目
    recs = [{"pri": p["priority"], "title": p["name"], "text": p["output"]}
            for p in D["projects"] if p["priority"] == "P0"][:3]
    if not recs:
        recs = [{"pri": "P1", "title": p["name"], "text": p["output"]} for p in D["projects"][:3]]
    return kpis, {"findings": findings, "recs": recs}


def main():
    ap = argparse.ArgumentParser(description="渲染白皮书级 HTML 报告（用户画像与人群洞察）")
    ap.add_argument("data", help="数据 JSON 路径（与 render_output.py 同源）")
    ap.add_argument("--out", required=True, help="输出 HTML 路径")
    ap.add_argument("--meta", default=None, help="可选 case.json（封面元数据来源）")
    args = ap.parse_args()

    try:
        D = json.loads(Path(args.data).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"错误（exit 2）：读取/解析数据 JSON 失败：{e}", file=sys.stderr); return 2
    meta = {}
    if args.meta:
        try:
            meta = json.loads(Path(args.meta).read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARN：读取 meta 失败，改用默认：{e}", file=sys.stderr)

    rep = D.get("report", {}) or {}
    kpis, exec_ = (rep.get("kpis"), rep.get("exec")) if rep else (None, None)
    if not kpis or not exec_:
        dkpis, dexec = derive(D)
        kpis = kpis or dkpis
        exec_ = exec_ or dexec

    score = D["maturity"]["score"]; stage = D["maturity"]["stage"]
    title = meta.get("title") or rep.get("title") or "用户画像与人群洞察报告"
    subtitle = meta.get("subtitle") or rep.get("subtitle") or D["conclusion"]
    sk = (meta.get("skills") or [{"name": "用户画像与人群洞察"}])[0]
    tags = meta.get("tags", []) or rep.get("tags", [])
    qs = meta.get("quality_score")
    av_colors = ["#a8324a", "#b06a1e", "#3d5a80", "#2f7d5b", "#6b4e9e"]
    B = []

    # COVER
    qrow = f'<div><span>质审</span><b>{qs} / 100</b></div>' if qs else ""
    B.append(f'''
    <section class="cover">
      <div class="cover-inner">
        <div class="cover-eyebrow">用户画像与人群洞察 · 诊断报告</div>
        <h1 class="cover-title">{esc(title)}</h1>
        <p class="cover-sub">{esc(subtitle)}</p>
        <div class="cover-rule"></div>
        <div class="cover-meta">
          <div><span>画像就绪度</span><b style="color:#e8c87a">{score:g}/5 · {esc(stage)}</b></div>
          <div><span>能力域</span><b>{esc(sk.get("name","用户画像与人群洞察"))}</b></div>
          <div><span>主体</span><b>（脱敏）</b></div>
          {qrow}
        </div>
      </div>
      <div class="cover-foot">由「用户画像与人群洞察」skill 产出 · 数据请以业务真实口径校准</div>
    </section>''')

    # EXEC
    fnd = "".join(f'''<div class="finding"><div class="f-icon">{f["icon"]}</div><div><div class="f-title">{esc(f["title"])}</div><div class="f-text">{esc(f["text"])}</div></div></div>''' for f in exec_["findings"])
    rec = "".join(f'''<div class="rec">{pbadge(r["pri"])}<div><div class="r-title">{esc(r["title"])}</div><div class="r-text">{esc(r["text"])}</div></div></div>''' for r in exec_["recs"])
    B.append(f'''
    <section class="page"><div class="kicker">EXECUTIVE SUMMARY</div><h2 class="h-title">执行摘要</h2>
      <p class="conclusion">{esc(D["conclusion"])}</p>
      <div class="exec-grid"><div><div class="blk-h">关键发现</div>{fnd}</div><div><div class="blk-h">优先建议</div>{rec}</div></div>
    </section>''')

    # KPI
    kpi = "".join(f'<div class="kpi"><div class="kpi-num">{esc(k["num"])}</div><div class="kpi-lab">{esc(k["label"])}</div></div>' for k in kpis)
    B.append(f'<section class="page"><div class="kicker">KEY METRICS</div><h2 class="h-title">关键数据一览</h2><div class="kpi-grid">{kpi}</div></section>')

    # RADAR
    dr = "".join(f'''<div class="rdim"><div class="rdim-h"><span class="rdim-n">{esc(d["name"])}</span><span class="rdim-s" style="color:{sc(d["score"])}">{d["score"]}</span>{pbadge(d["priority"])}</div><div class="rdim-st">{esc(d["status"])}</div><div class="rdim-p">{esc(d["problem"])} → {esc(d["impact"])}</div></div>''' for d in D["dimensions"])
    B.append(f'<section class="page"><div class="kicker">READINESS</div><h2 class="h-title">画像就绪度 · 6 维诊断</h2><div class="radar-wrap"><div class="radar-box">{radar_svg(D["dimensions"])}</div><div class="rdim-list">{dr}</div></div></section>')

    # TAGS
    ly = "".join(f'<div class="layer"><div class="layer-n">{esc(l["layer"])}</div><div class="layer-p">{esc(l["purpose"])}</div><div class="layer-ex">{esc(l["example_tags"])}</div></div>' for l in D["tag_system"]["layers"])
    kt = "".join(f'<div class="kt">{pbadge(k["priority"])}<div class="kt-n">{esc(k["tag"])}</div><div class="kt-r">{esc(k["rule"])}</div></div>' for k in D["tag_system"]["key_tags"])
    B.append(f'<section class="page"><div class="kicker">TAXONOMY</div><h2 class="h-title">标签体系 · 六类分层</h2><div class="layer-grid">{ly}</div><div class="blk-h" style="margin-top:24px">优先级标签</div><div class="kt-grid">{kt}</div></section>')

    # SEGMENTS
    sg = "".join(f'''<div class="seg"><div class="seg-h"><span class="seg-n">{esc(s["name"])}</span><span class="seg-scale">{esc(s["scale_estimate"])}</span></div><div class="seg-rule">{esc(s["rule"])}</div><div class="seg-v">{esc(s["value"])}</div></div>''' for s in D["segments"])
    B.append(f'<section class="page"><div class="kicker">SEGMENTS</div><h2 class="h-title">用户分群模型</h2><div class="seg-grid">{sg}</div></section>')

    # PERSONAS
    ps = []
    for i, p in enumerate(D["personas"]):
        c = av_colors[i % len(av_colors)]
        ps.append(f'''<div class="persona"><div class="p-head" style="background:{c}"><div class="avatar">{esc(p["name"][0])}</div><div><div class="p-name">{esc(p["name"])}</div><div class="p-seg">关联分群 · {esc(p["linked_segment"])}</div></div></div><div class="p-snap">{esc(p["snapshot"])}</div><div class="p-body"><div class="p-row"><em>需求</em><span>{esc(p["needs"])}</span></div><div class="p-row"><em>痛点</em><span>{esc(p["pain_points"])}</span></div><div class="p-row"><em>行为</em><span>{esc(p["behaviors"])}</span></div><div class="p-row"><em>触点</em><span>{esc(p["touchpoints"])}</span></div><div class="p-row val"><em>价值</em><span>{esc(p["value_potential"])}</span></div></div></div>''')
    B.append(f'<section class="page"><div class="kicker">PERSONAS</div><h2 class="h-title">代表性用户画像</h2><div class="persona-grid">{"".join(ps)}</div></section>')

    # APPS
    aps = "".join(f'<div class="app"><div class="app-n">{esc(a["scenario"])}</div><div class="app-h">{esc(a["how_to_use"])}</div><div class="app-f"><span class="chip">{esc(a["target"])}</span><span class="app-m">指标 · {esc(a["metric"])}</span></div></div>' for a in D["applications"])
    B.append(f'<section class="page"><div class="kicker">APPLICATIONS</div><h2 class="h-title">画像应用场景</h2><div class="app-grid">{aps}</div></section>')

    # INSIGHTS（人群洞察与动作回路，核心增量）
    ins = D["insights"]
    om_rows = "".join(f'<tr><td class="pn">{esc(o["segment"])}</td><td><span class="hl">{esc(o["value_level"])}</span> / <span class="hl">{esc(o["growth_potential"])}</span></td><td>{esc(o["opportunity_type"])}</td><td class="muted">{esc(o["rationale"])}</td></tr>' for o in ins["opportunity_matrix"])
    am_rows = "".join(f'<tr><td class="pn">{esc(a["insight"])}</td><td><span class="chip">{esc(a["target_segment"])}</span></td><td>{esc(a["action"])}</td><td class="muted">{esc(a["channel"])}</td><td>{esc(a["expected_metric"])}</td><td>{pbadge(a["priority"])}</td></tr>' for a in ins["action_map"])
    ps_items = "".join(f'<div class="psco"><div class="pso-h"><span class="pso-n">{esc(p["opportunity"])}</span><span class="pso-s">{p["score"]}</span></div><div class="pso-r">{esc(p["reasoning"])}</div></div>' for p in ins["priority_scores"])
    B.append(f'''
    <section class="page"><div class="kicker">INSIGHTS</div><h2 class="h-title">人群洞察与动作回路</h2>
      <div class="blk-h">人群机会矩阵（价值 × 增长潜力）</div>
      <table class="tbl"><thead><tr><th>分群</th><th>价值 / 潜力</th><th>机会类型</th><th>理由</th></tr></thead><tbody>{om_rows}</tbody></table>
      <div class="blk-h" style="margin-top:24px">洞察 → 动作映射</div>
      <table class="tbl"><thead><tr><th>洞察</th><th>目标分群</th><th>动作</th><th>渠道</th><th>预期指标</th><th>优先级</th></tr></thead><tbody>{am_rows}</tbody></table>
      <div class="blk-h" style="margin-top:24px">机会优先级评分</div>
      <div class="pso-grid">{ps_items}</div>
    </section>''')

    # PROJECTS
    rows = "".join(f'<tr><td class="pn">{esc(p["name"])}</td><td>{pbadge(p["priority"])}</td><td>{esc(p["output"])}</td><td class="muted">{esc(p["owner_role"])}</td></tr>' for p in D["projects"])
    B.append(f'<section class="page"><div class="kicker">ROADMAP</div><h2 class="h-title">项目事项清单</h2><table class="tbl"><thead><tr><th>项目事项</th><th>优先级</th><th>预期产出</th><th>负责人</th></tr></thead><tbody>{rows}</tbody></table></section>')

    # CAVEATS
    asms = "".join(f"<li>{esc(a)}</li>" for a in D["assumptions"])
    miss = "".join(f"<li>{esc(m)}</li>" for m in D["missing_data"])
    B.append(f'<section class="page"><div class="kicker">CAVEATS</div><h2 class="h-title">缺失信息与假设</h2><div class="two-col"><div><div class="blk-h">假设</div><ul class="lst">{asms}</ul></div><div><div class="blk-h">待补数据</div><ul class="lst miss">{miss}</ul></div></div><p class="note">所有阈值/规模/预测分在补充真实数据前均标「待补/待验证」，不臆造数字。</p></section>')

    CSS = """
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:-apple-system,'PingFang SC','Segoe UI',sans-serif;background:#f6f3ec;color:#1c2331;line-height:1.7;font-size:15px}
    .wrap{max-width:940px;margin:0 auto;padding:0 0 60px}
    .h-title,.cover-title{font-family:'Songti SC','Source Han Serif SC','Noto Serif SC',Georgia,serif;font-weight:700;letter-spacing:-.005em}
    .cover{background:linear-gradient(160deg,#16223a 0%,#1f3050 60%,#2a3f63 100%);color:#f3ece0;padding:64px 56px 40px;position:relative;overflow:hidden}
    .cover:before{content:'';position:absolute;top:-60px;right:-60px;width:280px;height:280px;border-radius:50%;background:radial-gradient(circle,rgba(176,138,62,.22),transparent 70%)}
    .cover-inner{position:relative;max-width:680px}
    .cover-eyebrow{font-size:12px;letter-spacing:.22em;color:#b08a3e;font-weight:700;text-transform:uppercase;margin-bottom:18px}
    .cover-title{font-size:38px;line-height:1.22;color:#fff;margin-bottom:14px}
    .cover-sub{font-size:16px;color:#c9d4e8;max-width:600px;line-height:1.6}
    .cover-rule{width:64px;height:3px;background:#b08a3e;margin:26px 0}
    .cover-meta{display:grid;grid-template-columns:repeat(4,1fr);gap:18px;max-width:680px}
    .cover-meta div{display:flex;flex-direction:column;gap:3px}.cover-meta span{font-size:11px;color:#8ea0bd;letter-spacing:.05em}.cover-meta b{font-size:13.5px;color:#e8eef8;font-weight:600}
    .cover-foot{margin-top:40px;font-size:11.5px;color:#7d90b0;border-top:1px solid rgba(255,255,255,.12);padding-top:14px}
    .page{background:#fff;margin:24px 20px 0;padding:40px 48px;box-shadow:0 1px 3px rgba(28,35,49,.05);border-radius:2px}
    .page:first-of-type{margin-top:-30px;position:relative;z-index:2}
    .kicker{font-size:11px;letter-spacing:.2em;color:#b08a3e;font-weight:700;text-transform:uppercase;margin-bottom:8px}
    .h-title{font-size:26px;color:#16223a;margin-bottom:18px}
    .conclusion{font-size:16px;color:#2a3346;background:#f9f6ef;border-left:3px solid #b08a3e;padding:16px 20px;line-height:1.75;margin-bottom:28px}
    .blk-h{font-size:13px;font-weight:700;color:#16223a;letter-spacing:.04em;margin-bottom:14px;padding-bottom:8px;border-bottom:1px solid #ebe4d4}
    .exec-grid{display:grid;grid-template-columns:1.3fr 1fr;gap:32px}
    .finding{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid #f0eadb}.finding:last-child{border:none}
    .f-icon{font-size:22px;flex-shrink:0;width:34px;height:34px;display:flex;align-items:center;justify-content:center;background:#f9f6ef;border-radius:8px}
    .f-title{font-weight:700;color:#16223a;font-size:14.5px;margin-bottom:3px}.f-text{font-size:13px;color:#5a6275;line-height:1.6}
    .rec{display:flex;gap:10px;padding:11px 0;border-bottom:1px solid #f0eadb;align-items:flex-start}.rec:last-child{border:none}
    .r-title{font-weight:700;color:#16223a;font-size:14px;margin-bottom:2px}.r-text{font-size:12.5px;color:#5a6275}
    .kpi-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:#ebe4d4;border:1px solid #ebe4d4}
    .kpi{background:#fff;padding:26px 20px}.kpi-num{font-family:'Songti SC',Georgia,serif;font-size:30px;font-weight:700;color:#16223a;line-height:1.1}.kpi-lab{font-size:12px;color:#7a8294;margin-top:6px}
    .radar-wrap{display:grid;grid-template-columns:340px 1fr;gap:32px;align-items:center}
    .radar{width:100%;height:auto}.rlabel{font-size:11px;fill:#4a5160;font-weight:600}.rscore{font-size:12px;font-weight:700}
    .rdim{padding:10px 0;border-bottom:1px solid #f0eadb}.rdim-h{display:flex;align-items:center;gap:8px}.rdim-n{font-weight:700;color:#16223a;font-size:14px;flex:1}.rdim-s{font-family:Georgia,serif;font-size:18px;font-weight:700}.rdim-st{font-size:12px;color:#5a6275;margin:4px 0}.rdim-p{font-size:11.5px;color:#8a8f9c}
    .layer-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
    .layer{border:1px solid #ebe4d4;border-top:3px solid #b08a3e;padding:14px}.layer-n{font-weight:700;color:#16223a;font-size:14px}.layer-p{font-size:11.5px;color:#8a8f9c;margin:3px 0 8px}.layer-ex{font-size:11.5px;color:#3a4150;background:#faf7ef;padding:6px 8px;line-height:1.5}
    .kt-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.kt{border:1px solid #ebe4d4;padding:12px}.kt-n{font-weight:700;color:#16223a;margin:8px 0 4px;font-size:13.5px}.kt-r{font-size:11px;color:#7a8294}
    .seg-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
    .seg{border:1px solid #ebe4d4;border-left:3px solid #2f7d5b;padding:14px}.seg-h{display:flex;align-items:center;gap:8px;margin-bottom:8px}.seg-n{font-weight:700;color:#16223a;flex:1;font-size:14.5px}.seg-scale{font-size:11px;background:#eaf5ef;color:#2f7d5b;font-weight:700;padding:3px 8px;border-radius:4px}.seg-rule{font-size:11.5px;background:#faf7ef;color:#3a4150;padding:7px 9px;font-family:'SF Mono',Menlo,monospace;line-height:1.5}.seg-v{font-size:12.5px;color:#5a6275;margin-top:8px}
    .persona-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}
    .persona{border:1px solid #ebe4d4;overflow:hidden;border-radius:2px}.p-head{color:#fff;padding:14px 16px;display:flex;align-items:center;gap:12px}.avatar{width:42px;height:42px;border-radius:50%;background:rgba(255,255,255,.22);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:700;font-family:'Songti SC',serif;flex-shrink:0}.p-name{font-weight:700;font-size:15px}.p-seg{font-size:11px;opacity:.85;margin-top:2px}.p-snap{padding:8px 16px;font-size:11.5px;color:#8a8f9c;background:#faf7ef;border-bottom:1px solid #f0eadb}.p-body{padding:8px 16px 14px}.p-row{padding:6px 0;border-bottom:1px solid #f5f0e3;display:flex;gap:8px}.p-row:last-child{border:none}.p-row em{font-size:10.5px;color:#b08a3e;font-style:normal;font-weight:700;width:30px;flex-shrink:0;padding-top:2px}.p-row span{font-size:12.5px;color:#3a4150;flex:1}.p-row.val span{color:#16223a;font-weight:600}
    .app-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
    .app{border:1px solid #ebe4d4;border-top:3px solid #3d5a80;padding:14px}.app-n{font-weight:700;color:#16223a;font-size:14px}.app-h{font-size:12.5px;color:#5a6275;margin:6px 0 10px;line-height:1.55}.app-f{display:flex;align-items:center;gap:8px;justify-content:space-between}.chip{font-size:11px;background:#eef3fa;color:#3d5a80;padding:3px 9px;border-radius:4px;font-weight:600}.app-m{font-size:11px;color:#8a8f9c}
    .tbl{width:100%;border-collapse:collapse;font-size:13px}.tbl th{text-align:left;color:#8a8f9c;font-weight:700;padding:10px 12px;border-bottom:2px solid #ebe4d4;font-size:11.5px;letter-spacing:.03em}.tbl td{padding:11px 12px;border-bottom:1px solid #f5f0e3;vertical-align:top}.tbl .pn{font-weight:600;color:#16223a}.tbl .muted{color:#8a8f9c;font-size:12px}
    .pri{display:inline-block;font-size:10.5px;font-weight:700;padding:2px 7px;border-radius:3px}
    .two-col{display:grid;grid-template-columns:1fr 1fr;gap:32px}.lst{list-style:none}.lst li{font-size:13px;padding:9px 0 9px 18px;border-bottom:1px solid #f5f0e3;color:#3a4150;position:relative;line-height:1.55}.lst li:before{content:'';width:5px;height:5px;background:#b08a3e;border-radius:50%;position:absolute;left:0;top:15px}.lst.miss li:before{background:#a8324a}
    .note{font-size:12px;color:#8a8f9c;margin-top:20px;font-style:italic;text-align:center}
    .hl{display:inline-block;font-size:10.5px;font-weight:700;padding:1px 6px;border-radius:3px;background:#faf3df;color:#a8741e}
    .pso-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
    .psco{border:1px solid #ebe4d4;border-left:3px solid #b08a3e;padding:12px 14px}
    .pso-h{display:flex;align-items:center;gap:10px;margin-bottom:6px}
    .pso-n{font-weight:700;color:#16223a;font-size:13.5px;flex:1}
    .pso-s{font-family:'Songti SC',Georgia,serif;font-size:22px;font-weight:700;color:#b08a3e;line-height:1}
    .pso-r{font-size:11.5px;color:#5a6275;line-height:1.55}
    .foot{text-align:center;color:#8a8f9c;font-size:11.5px;padding:40px 20px 0}
    @media(max-width:760px){.cover-meta,.exec-grid,.kpi-grid,.radar-wrap,.layer-grid,.kt-grid,.seg-grid,.persona-grid,.app-grid,.two-col{grid-template-columns:1fr}.cover{padding:40px 28px}.cover-title{font-size:28px}.page{padding:28px 22px;margin:20px 14px 0}}
    """
    doc = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>{esc(title)}</title><style>{CSS}</style></head>
    <body><div class="wrap">{''.join(B)}<div class="foot">用户画像与人群洞察 skill · 报告由 render_report.py 渲染 · 数据请以业务真实口径校准</div></div></body></html>'''
    try:
        out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(doc, encoding="utf-8")
    except Exception as e:
        print(f"错误（exit 3）：写盘失败：{e}", file=sys.stderr); return 3
    print(f"已渲染：{out}（{len(doc)}字节）", file=sys.stderr); return 0


if __name__ == "__main__":
    sys.exit(main())
