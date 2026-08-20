#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每周时政题 HTML 生成器
用法：python3 build_html.py <data.json> <template.html> <output.html>

功能：
1. 读取 data.json（纯文本数据，无需手动转义）
2. 读取 template.html（含占位符）
3. 自动生成热点卡片 HTML、筛选标签、题目 JSON
4. 写入 output.html（可直接用 present_files 呈现）

这样 AI 不需要手写 JSON/HTML，从根本上避免引号、尖括号等转义错误。
"""

import json
import html
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATE = SCRIPTS_DIR / "quiz_template.html"

# 分类配色与映射（与模板 CSS 对应）
CATEGORY_MAP = {
    "经济": ("economy", "#f39c12"),
    "政策": ("policy", "#3498db"),
    "科技": ("tech", "#9b59b6"),
    "外交": ("diplomacy", "#16a085"),
    "法律": ("law", "#e74c3c"),
    "民生": ("livelihood", "#27ae60"),
    "文化": ("culture", "#d35400"),
    "综合": ("general", "#7f8c8d"),
}


def escape_html(s):
    """转义 HTML 特殊字符。"""
    return html.escape(s) if s else ""


def build_filter_tags(topics):
    """根据实际热点类别生成筛选标签（只显示有数据的类别）。"""
    cats = []
    seen = set()
    for t in topics:
        cat = t.get("category", "综合")
        if cat not in seen:
            seen.add(cat)
            cats.append(cat)

    tags = ['<span class="filter-tag ft-all active" onclick="filterCards(\'all\')">全部</span>']
    for cat in cats:
        cid, _ = CATEGORY_MAP.get(cat, ("general", "#7f8c8d"))
        tags.append(
            f'<span class="filter-tag ft-{escape_html(cid)}" onclick="filterCards(\'{escape_html(cid)}\')">{escape_html(cat)}</span>'
        )
    return "\n    ".join(tags)


def build_cards(topics):
    """生成热点卡片 HTML 列表。"""
    cards = []
    for idx, t in enumerate(topics, 1):
        cat = t.get("category", "综合")
        cid, color = CATEGORY_MAP.get(cat, ("general", "#7f8c8d"))
        title = t.get("title", "")
        summary = t.get("summary", "")
        detail = t.get("detail", "")
        date = t.get("date", "")
        source = t.get("source", "")
        source_url = t.get("sourceUrl", "")

        cards.append(f'''<div class="card cat-{escape_html(cid)}" data-cat="{escape_html(cid)}">
      <div class="card-body">
        <div class="card-top">
          <span class="card-tag" style="background:{escape_html(color)}">{escape_html(cat)}</span>
          <span class="card-date">{escape_html(date)}</span>
        </div>
        <div class="card-title">{idx}. {escape_html(title)}</div>
        <div class="card-summary">{escape_html(summary)}</div>
        <div class="card-extra">
          <div class="card-detail">{escape_html(detail)}</div>
          <div class="card-source">
            📎 {escape_html(source)} · <a href="{escape_html(source_url)}" target="_blank" rel="noopener">查看原文 →</a>
          </div>
        </div>
        <span class="card-toggle" onclick="toggleCard(this)"><span>展开详情</span> <span class="arrow">&#9660;</span></span>
      </div>
    </div>''')
    return "\n\n    ".join(cards)


def build_qdata(questions):
    """生成题目 JSON 字符串（自动转义特殊字符）。"""
    return json.dumps(questions, ensure_ascii=False, separators=(",", ":"))


def build_from_dict(data, template_path=None, output_path=None):
    """从 Python dict 直接构建 HTML（推荐方式，避免 JSON 引号转义问题）。

    template_path 默认使用同目录 quiz_template.html；
    output_path 必填（一般为工作区 outputs/ 下相对或绝对路径）。
    """
    template_path = Path(template_path) if template_path else DEFAULT_TEMPLATE
    if output_path is None:
        raise ValueError("output_path 不能为空")
    output_path = Path(output_path)

    with template_path.open("r", encoding="utf-8") as f:
        template = f.read()

    topics = data.get("hotTopics", [])
    questions = data.get("questions", [])
    week_range = data.get("weekRange", "本周")

    # 动态统计
    hot_count = len(topics)
    cat_count = len(set(t.get("category", "综合") for t in topics))
    source_count = len(set(t.get("source", "") for t in topics if t.get("source")))
    question_count = len(questions)

    # 生成各片段
    filter_tags = build_filter_tags(topics)
    cards_html = build_cards(topics)
    qdata_json = build_qdata(questions)

    # 替换占位符
    html_out = template
    html_out = html_out.replace("{{WEEK_RANGE}}", escape_html(week_range))
    html_out = html_out.replace("{{HOT_COUNT}}", str(hot_count))
    html_out = html_out.replace("{{CAT_COUNT}}", str(cat_count))
    html_out = html_out.replace("{{SOURCE_COUNT}}", str(source_count))
    html_out = html_out.replace("{{FILTER_TAGS}}", filter_tags)
    html_out = html_out.replace("{{CARDS_HTML}}", cards_html)
    html_out = html_out.replace("{{QUESTION_COUNT}}", str(question_count))
    html_out = html_out.replace("{{QDATA_JSON}}", qdata_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"生成成功：{output_path}")
    print(f"  热点数：{hot_count}，类别数：{cat_count}，题目数：{question_count}")


def build_html(data_path, template_path, output_path):
    """从 JSON 文件构建 HTML（兼容旧用法）。"""
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    build_from_dict(data, template_path, output_path)


if __name__ == "__main__":
    # 用法1：python3 build_html.py <data.json> <output.html>
    # 用法2：python3 build_html.py <data.json> <template.html> <output.html>
    if len(sys.argv) == 3:
        build_html(sys.argv[1], DEFAULT_TEMPLATE, sys.argv[2])
    elif len(sys.argv) == 4:
        build_html(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        print("用法：python3 build_html.py <data.json> <output.html>")
        print("  或：python3 build_html.py <data.json> <template.html> <output.html>")
        sys.exit(1)
