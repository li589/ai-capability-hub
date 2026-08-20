# -*- coding: utf-8 -*-
"""
图表生成工具：将查询结果（cols+rows）渲染为 PNG 图表，自动选型。

自动选型规则：
  - 首列是日期/时间 → 折线趋势图（多数值列则多线）
  - 单数值列且行数 <= 10 → 饼图（占比，取 Top 10）
  - 单数值列且行数 > 10 → 水平柱状图（Top 15）
  - 多数值列 → 分组柱状图
  - --type 可强制指定: line/pie/bar/barh

用法（必须用 venv python 跑，含 matplotlib）：
  python chart_tool.py --title "今日产量趋势" --data '{"cols":["日期","产量"],"rows":[["08-01",120],["08-02",150]]}'
  python chart_tool.py --title "设备状态占比" --type pie --data '{"cols":["状态","数量"],"rows":[["闲置",161],["加工",11]]}'
  python chart_tool.py --json result.json --title "..."   # 从 query_tool 输出文件读取

输出：reports/charts/<title>.png，打印绝对路径。
"""
import sys, os, json, re, datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE, "reports", "charts")

# 中文字体（Windows）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

_FONT_SET = False


def _setup_font():
    global _FONT_SET
    if _FONT_SET:
        return
    for name in ("Microsoft YaHei", "SimHei", "SimSun", "KaiTi"):
        try:
            font_manager.findfont(name, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [name]
            break
        except Exception:
            continue
    plt.rcParams["axes.unicode_minus"] = False
    _FONT_SET = True


def _is_time_col(col):
    s = str(col).lower()
    return any(k in s for k in ("日期", "时间", "date", "time", "day", "月份", "周", "年")) \
        or re.match(r"^\d{4}-\d{2}(-\d{2})?$", str(col))


def _parse_rows(rows):
    """数值列尽量转 float，日期列规范为 MM-DD"""
    out = []
    for r in rows:
        row = []
        for v in r:
            if isinstance(v, (int, float)):
                row.append(v)
            elif isinstance(v, str):
                sv = v.strip()
                m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", sv)
                if m:
                    row.append(f"{m.group(2)}-{m.group(3)}")
                elif re.match(r"^-?\d+\.?\d*$", sv):
                    row.append(float(sv))
                else:
                    row.append(sv)
            else:
                row.append(str(v))
        out.append(row)
    return out


def _auto_type(cols, parsed):
    if len(parsed) == 0:
        return "bar"
    if _is_time_col(cols[0]):
        return "line"
    num_cols = sum(1 for c in cols[1:] if all(isinstance(r[i], (int, float)) for r in parsed for i in range(1, len(cols))))
    if num_cols <= 1 and len(parsed) <= 10:
        return "pie"
    if num_cols <= 1:
        return "barh"
    return "bar"


def make_chart(cols, rows, title="", chart_type="auto", out_name=None):
    _setup_font()
    os.makedirs(OUT_DIR, exist_ok=True)
    cols = [str(c) for c in cols]
    parsed = _parse_rows(rows)
    if not parsed:
        raise ValueError("无数据可绘图")
    ctype = chart_type if chart_type != "auto" else _auto_type(cols, parsed)

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=130)
    x = [r[0] for r in parsed]

    if ctype == "pie":
        vals = [r[1] for r in parsed]
        labels = x
        total = sum(v for v in vals if isinstance(v, (int, float)))
        sizes = [v if isinstance(v, (int, float)) else 0 for v in vals]
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct=lambda p: f"{p:.1f}%" if p >= 3 else "",
            startangle=90, counterclock=False, pctdistance=0.78,
            textprops={"fontsize": 9})
        ax.set_title(title, fontsize=13, pad=14)
        if total:
            ax.text(0, -1.28, f"合计: {total:g}", ha="center", fontsize=10, color="#555")
    elif ctype == "line":
        for i in range(1, len(cols)):
            vals = [r[i] if isinstance(r[i], (int, float)) else 0 for r in parsed]
            ax.plot(range(len(x)), vals, marker="o", linewidth=2, label=cols[i])
        ax.set_xticks(range(len(x)))
        ax.set_xticklabels(x, rotation=30, ha="right", fontsize=9)
        ax.legend(fontsize=9)
        ax.set_title(title, fontsize=13, pad=12)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
    elif ctype == "barh":
        vals = [r[1] if isinstance(r[1], (int, float)) else 0 for r in parsed][:15]
        labels = x[:15]
        ypos = range(len(vals))
        ax.barh(list(ypos), vals, color="#4C78A8")
        ax.set_yticks(list(ypos))
        ax.set_yticklabels(labels, fontsize=9)
        for i, v in enumerate(vals):
            ax.text(v, i, f" {v:g}", va="center", fontsize=8)
        ax.set_title(title, fontsize=13, pad=12)
        ax.grid(axis="x", linestyle="--", alpha=0.4)
    else:  # bar
        n = len(parsed)
        nser = len(cols) - 1
        width = 0.8 / max(nser, 1)
        for i in range(1, len(cols)):
            vals = [r[i] if isinstance(r[i], (int, float)) else 0 for r in parsed]
            xs = [j + (i - 1) * width for j in range(n)]
            ax.bar(xs, vals, width=width, label=cols[i])
        ax.set_xticks(range(n))
        ax.set_xticklabels(x, rotation=30, ha="right", fontsize=9)
        if nser > 1:
            ax.legend(fontsize=9)
        ax.set_title(title, fontsize=13, pad=12)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    fig.tight_layout()
    fname = out_name or re.sub(r"[\\/:*?\"<>|\s]+", "_", title)[:40]
    fpath = os.path.join(OUT_DIR, f"{fname}.png")
    fig.savefig(fpath, bbox_inches="tight")
    plt.close(fig)
    return fpath


def main():
    args = sys.argv[1:]
    data = None
    title = "图表"
    ctype = "auto"
    for i, a in enumerate(args):
        if a == "--title" and i + 1 < len(args):
            title = args[i + 1]
        elif a == "--type" and i + 1 < len(args):
            ctype = args[i + 1]
        elif a == "--data" and i + 1 < len(args):
            data = json.loads(args[i + 1])
        elif a == "--json" and i + 1 < len(args):
            with open(args[i + 1], "r", encoding="utf-8") as f:
                data = json.load(f)
    if not data or not data.get("cols"):
        print("❌ 需要 --data '{\"cols\":[...],\"rows\":[[...]]}' 或 --json 文件")
        print(__doc__)
        return
    try:
        path = make_chart(data["cols"], data.get("rows", []), title, ctype)
        print(path)
    except Exception as e:
        print(f"❌ 图表生成失败: {e}")


if __name__ == "__main__":
    main()
