"""Inject an analysis JSON into the HTML template -> a standalone report.

Usage:
    build_report.py <analysis.json> [output.html]

The analysis JSON is produced by the AI agent. Schema is documented in
SKILL.md Appendix B (inline template with concrete examples).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "assets", "report_template.html")

# 必需的 top-level keys（缺失会警告但不会阻止生成）
REQUIRED_KEYS = {"system", "green", "yellow", "red", "summary"}


def validate(data):
    """检查 JSON 结构，返回警告列表。"""
    warnings = []
    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        warnings.append(f"缺少必需的 top-level 键: {', '.join(sorted(missing))}")

    # 检查 amber/yellow 歧义
    if "amber" in data and "yellow" not in data:
        warnings.append("使用了 'amber' 而非 'yellow'，模板会自动兼容但建议统一用 'yellow'")

    # 检查 green 项是否有 size_estimate
    for i, g in enumerate(data.get("green", [])):
        if not g.get("size_estimate") and not g.get("size") and not g.get("size_h"):
            warnings.append(f"green[{i}] '{g.get('name', '?')}' 缺少 size_estimate/size 字段")

    # 检查 yellow 项必填字段
    for i, y in enumerate(data.get("yellow", [])):
        for fld in ("content_profile", "why_manual", "disposal", "risk"):
            if not y.get(fld):
                warnings.append(f"yellow[{i}] '{y.get('name', '?')}' 缺少 {fld}")

    # 检查 red 项必填字段
    for i, r in enumerate(data.get("red", [])):
        for fld in ("why_keep", "indirect_release"):
            if not r.get(fld):
                warnings.append(f"red[{i}] '{r.get('name', '?')}' 缺少 {fld}")

    # 检查 summary
    sm = data.get("summary", {})
    for k in ("overview", "tier_stats", "priority"):
        if not sm.get(k):
            warnings.append(f"summary 缺少 '{k}'")

    return warnings


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser(
        os.path.join(os.environ.get("USERPROFILE", "~"), "Desktop",
                     "storage-report.html"))

    with open(src, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TEMPLATE, "r", encoding="utf-8") as f:
        tpl = f.read()

    # 结构验证
    warnings = validate(data)
    if warnings:
        print("⚠️  JSON 结构警告:")
        for w in warnings:
            print(f"   - {w}")
        # 将警告注入数据，让模板也能显示
        data["_warnings"] = warnings
    else:
        print("✅ JSON 结构检查通过")

    blob = json.dumps(data, ensure_ascii=False)

    # 安全转义：</script> 会关闭 HTML script 标签，需转义。
    # 注意：\u2028/\u2029 不再需要转义，因为 JSON 数据现在在
    # <script type="application/json"> 标签内，由 JSON.parse() 解析，
    # 不经过 JS 语法解析器，不会再导致 JS 语法错误。
    blob_safe = blob.replace("</script", "<\\/script")

    # Static report has no delete capability (DELETE=null).
    # Delete buttons only appear when served via server.py.
    html = tpl.replace("__REPORT_DATA__", blob_safe)\
              .replace("__DELETE_CONFIG__", "null")

    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Report generated: {out}")


if __name__ == "__main__":
    main()
