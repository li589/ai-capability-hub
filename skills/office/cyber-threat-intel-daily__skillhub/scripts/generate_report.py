#!/usr/bin/env python3
"""
generate_report.py - 网络安全威胁情报日报生成脚本
将 fetch_intel.py 抓取的原始数据结构化，
输出供 AI 分析使用的 Markdown 上下文文档
"""

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# ─── 情报分类关键词 ────────────────────────────────────────────────
CATEGORIES = {
    "漏洞披露与补丁": [
        "CVE", "漏洞", "vulnerability", "patch", "补丁", "exploit",
        "RCE", "远程代码执行", "zero-day", "0day", "POC", "proof of concept",
        "arbitrary code", "privilege escalation", "提权", "bypass", "绕过",
    ],
    "勒索软件与APT": [
        "ransomware", "勒索", "APT", "nation-state", "国家级", "advanced persistent",
        "LockBit", "BlackCat", "Clop", "RansomHub", "Play", "Akira",
        "ALPHV", "BlackMatter", "Conti", "DarkSide", "REvil",
    ],
    "数据泄露与隐私": [
        "data breach", "数据泄露", "leak", "泄漏", "exposure", "暴露",
        "stolen", "credentials", "credential stuffing", "personal data",
        "隐私", "privacy", "GDPR", "PII",
    ],
    "供应链与软件安全": [
        "supply chain", "供应链", "dependency", "npm", "PyPI", "malware",
        "backdoor", "后门", "open source", "开源", "package", "库",
        "SolarWinds", "XZ utils", "typosquat",
    ],
    "网络基础设施威胁": [
        "DDoS", "botnet", "僵尸网络", "phishing", "钓鱼", "DNS",
        "BGP", "routing", "infrastructure", "基础设施", "cloud",
        "AWS", "Azure", "GCP", "firewall", "ICS", "SCADA", "OT",
    ],
    "AI与新兴威胁": [
        "AI", "人工智能", "LLM", "ChatGPT", "deepfake", "深度伪造",
        "prompt injection", "jailbreak", "machine learning",
        "generative", "生成式",
    ],
    "执法与政策动态": [
        "arrest", "逮捕", "indictment", "起诉", "law enforcement",
        "FBI", "NSA", "CISA", "Europol", "Interpol", "policy",
        "regulation", "监管", "legislation", "法规", "sanction", "制裁",
    ],
}


def classify_article(article: dict) -> list[str]:
    """根据标题+摘要关键词对文章进行多标签分类"""
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    matched = []
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw.lower() in text:
                matched.append(category)
                break
    return matched if matched else ["其他安全资讯"]


def format_date_cn(date_str: str) -> str:
    """将 YYYYMMDD 转为中文友好格式"""
    try:
        dt = datetime.strptime(date_str, "%Y%m%d")
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        wd = weekdays[dt.weekday()]
        return dt.strftime(f"%Y年%m月%d日 {wd}")
    except Exception:
        return date_str


def build_context_document(data: dict) -> str:
    """
    将原始抓取数据转换为结构化的情报上下文文档（Markdown）
    供 AI 进一步分析并生成最终报告
    """
    date_str = data.get("date", "")
    date_cn = format_date_cn(date_str)
    rss_articles = data.get("rss_articles", [])
    ransomware_items = data.get("ransomware_intel", [])
    stats = data.get("stats", {})

    lines = [
        f"# 网络安全威胁情报原始数据 — {date_cn}",
        "",
        f"> 抓取时间: {data.get('fetched_at', 'N/A')}  ",
        f"> RSS 文章总数: {stats.get('rss_count', 0)}  ",
        f"> 勒索情报条数: {stats.get('ransomware_count', 0)}  ",
        "",
        "---",
        "",
    ]

    # ── 按分类整理 RSS 文章 ─────────────────────────────────────
    lines.append("## 一、安全媒体资讯（按分类）")
    lines.append("")

    categorized: dict[str, list[dict]] = {cat: [] for cat in CATEGORIES}
    categorized["其他安全资讯"] = []

    for art in rss_articles:
        cats = classify_article(art)
        for cat in cats:
            if cat in categorized:
                categorized[cat].append(art)
            else:
                categorized["其他安全资讯"].append(art)

    for cat_name, items in categorized.items():
        if not items:
            continue
        lines.append(f"### {cat_name}（{len(items)} 条）")
        lines.append("")
        for art in items:
            title = art.get("title", "（无标题）")
            link = art.get("link", "")
            source = art.get("source", "")
            pub = art.get("pub_date", "")[:10] if art.get("pub_date") else ""
            summary = art.get("summary", "")

            lines.append(f"**{title}**")
            if link:
                lines.append(f"- 来源: [{source}]({link})")
            else:
                lines.append(f"- 来源: {source}")
            if pub:
                lines.append(f"- 日期: {pub}")
            if summary:
                lines.append(f"- 摘要: {summary[:300]}")
            lines.append("")

    # ── 勒索情报 ───────────────────────────────────────────────
    lines.append("---")
    lines.append("")
    lines.append(f"## 二、勒索软件情报（0.zone · {date_cn}）")
    lines.append("")

    if ransomware_items:
        for item in ransomware_items:
            title = item.get("title", "（无标题）")
            link = item.get("link", "")
            summary = item.get("summary", "")

            lines.append(f"- **{title}**")
            if link and link != f"https://0.zone/article/{date_str}":
                lines.append(f"  - 链接: {link}")
            if summary:
                lines.append(f"  - 详情: {summary[:200]}")
    else:
        lines.append("_今日暂无勒索情报数据，可能受网络限制影响。_")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*以上为原始情报数据，请 AI 基于此进行专业分析并生成威胁情报日报。*")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="生成情报分析上下文文档")
    parser.add_argument(
        "input",
        nargs="?",
        default="-",
        help="fetch_intel.py 输出的 JSON 文件路径，默认 stdin（-）",
    )
    parser.add_argument(
        "--output",
        default="-",
        help="输出 Markdown 文件路径，默认 stdout（-）",
    )
    args = parser.parse_args()

    # 读取输入
    if args.input == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(args.input).read_text(encoding="utf-8")

    data = json.loads(raw)
    doc = build_context_document(data)

    # 写出
    if args.output == "-":
        print(doc)
    else:
        Path(args.output).write_text(doc, encoding="utf-8")
        print(f"[generate_report] 已保存至 {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
