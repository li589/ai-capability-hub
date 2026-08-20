#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号爆款短视频拆解（体验版）【零一数科·出品】【零一数科·出品】 v0.3.0 —— 报告本地结构硬门禁

纯标准库、**不上网**。在 agent 写完 Markdown 报告后调用，直接读磁盘上的
report.md 做本地结构判定：六节是否齐全且顺序正确、各表表头列是否齐全、
六维评分六个维度是否齐、结构拆解「段落」列有无「中段N」占位、是否误带
「脚本类型与中段段落功能对照」参考表、各节是否非空。

**与 archive_report.py 的区别**：那个是把报告正文提交到服务端登记的旁路步骤
（报告正文送至零一数科提交端点）、失败不阻塞报告交付（退出码恒 0 但报告已交付）；
本脚本是 **硬门禁**——结构不达标时退出码 12，agent 必须据此
补写缺漏章节后重跑，**未通过不得宣布完成**。本脚本只判定结构，不评判内容质量。

用法:
    python3 verify_report_structure.py <report_md_path>
    # 或从 stdin 读：
    cat report.md | python3 verify_report_structure.py -

stdout 输出（始终输出，供 agent 解析）:
    === WX_REPORT_STRUCTURE_START ===
    { "ok": true|false, "section_count": N, "missing_sections": [...],
      "missing_columns": {"结构拆解": [...], ...},
      "missing_dimensions": [...], "issues": [...] }
    === WX_REPORT_STRUCTURE_END ===

退出码:
    0   结构达标（ok=true）
    12  结构不达标（ok=false）——agent 须按 missing_*/issues 补写后重跑
    2   输入错误 / 文件不存在 / 读取失败
"""

import argparse
import json
import re
import sys
from pathlib import Path

RESULT_START = "=== WX_REPORT_STRUCTURE_START ==="
RESULT_END = "=== WX_REPORT_STRUCTURE_END ==="

# 六节固定标题（## 级、文字本身，不带 Part 前缀），顺序固定。
SECTION_TITLES = [
    "基本信息",
    "结构拆解",
    "内容归因分析",
    "六维评分",
    "总体评估",
    "标签",
]

# 各表格表头必须包含的列（归一化后匹配，见 _norm）。
EXPECTED_COLUMNS = {
    "结构拆解": ["序号", "段落", "起始秒", "结束秒", "段落功能",
               "hook/cta类型", "台词/画面", "备注"],
    "内容归因分析": ["排序", "层", "因素", "详细描述", "贡献度"],
    "六维评分": ["维度", "评分", "节奏证据", "评分理由", "改进建议"],
}

# 六维评分「维度」列必须出现的六行（归一化后匹配）。
EXPECTED_DIMENSIONS = [
    "hook强度", "信息密度", "节奏控制", "产品展示", "情绪曲线", "转化引导",
]

# 禁止出现在报告中的参考表标题（模板注明「不输出到报告」）。
FORBIDDEN_REFERENCE_HEADING = "脚本类型与中段段落功能对照"

# 「段落」列禁止的占位：中段1 / 中段2 / 中段N …
MIDFRAME_PLACEHOLDER_RE = re.compile(r"中段\s*[0-9一二三四五六七八九十Nn]")


def log(msg: str) -> None:
    print(f"[verify_report_structure] {msg}", file=sys.stderr, flush=True)


def emit(payload: dict) -> None:
    print(RESULT_START, flush=True)
    print(json.dumps(payload, ensure_ascii=False, indent=2), flush=True)
    print(RESULT_END, flush=True)


def _norm(s: str) -> str:
    """归一化单元格/标题文本用于匹配：去空白、转小写、统一分隔符。

    把 `·` `/` `／` 都标准化为 `/`，并把所有空白去掉，这样
    `Hook/CTA 类型` / `Hook·CTA 类型` / `Hook / CTA 类型` 都能命中
    预期 `hook/cta类型`；`Hook 强度` / `Hook强度` 都能命中 `hook强度`。
    """
    if not s:
        return ""
    s = s.replace("·", "/").replace("／", "/")
    s = s.lower()
    s = re.sub(r"\s+", "", s)
    return s


def read_content(src: str) -> "str | None":
    if src == "-":
        try:
            return sys.stdin.read()
        except Exception as e:  # noqa: BLE001
            log(f"读取 stdin 失败：{e}")
            return None
    p = Path(src).expanduser()
    if not p.exists() or not p.is_file():
        log(f"报告文件不存在：{p}")
        return None
    try:
        return p.read_text("utf-8")
    except Exception as e:  # noqa: BLE001
        log(f"读取报告文件失败：{e}")
        return None


def _section_heading_re(title: str) -> re.Pattern:
    # 匹配 `## 基本信息` 这样的二级标题行（行首可有空格，行尾可有空白）。
    # 用 [^\S\n]* 而非 \s*：避免空白跨越换行，导致 .start() 指向标题前的 \n。
    return re.compile(rf"^[^\S\n]*##[^\S\n]+{re.escape(title)}[^\S\n]*$", re.MULTILINE)


def _split_table_rows(block: str) -> list[list[str]]:
    """从一节文本里抽出所有表格行的单元格列表（已 strip）。

    跳过分隔行（|---|）。返回行列表，每行是单元格文本列表。
    """
    rows = []
    for line in block.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.rstrip().endswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # 分隔行：所有单元格只含 -、:、空格
        if all(re.fullmatch(r"[\s:\-]*", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def _find_sections(content: str) -> dict:
    """返回 {标题: 起始位置}；同时返回全文按二级标题切分的内容块。"""
    positions = {}
    for title in SECTION_TITLES:
        m = _section_heading_re(title).search(content)
        if m:
            positions[title] = m.start()
    return positions


def _section_block(content: str, positions: dict, title: str) -> str:
    """取某节标题之后到下一个 ## 标题之前的文本。"""
    start = positions[title]
    # 跳过标题行本身
    after = content[start:]
    nl = after.find("\n")
    body = after[nl + 1:] if nl != -1 else ""
    # 找下一个 ## 标题（[^\S\n]* 限制不跨行）
    m = re.search(r"^[^\S\n]*##[^\S\n]+\S", body, re.MULTILINE)
    if m:
        body = body[:m.start()]
    return body


def verify(content: str) -> dict:
    missing_sections = []
    missing_columns = {}
    missing_dimensions = []
    issues = []

    positions = _find_sections(content)

    # 1) 六节齐全
    for title in SECTION_TITLES:
        if title not in positions:
            missing_sections.append(title)
    # 1b) 顺序正确（出现的标题在原文里的相对顺序须与 SECTION_TITLES 一致）
    present_in_order = [t for t in SECTION_TITLES if t in positions]
    if present_in_order != sorted(present_in_order, key=lambda t: positions[t]):
        issues.append("章节顺序与模板不一致（应为：基本信息→结构拆解→内容归因分析→六维评分→总体评估→标签）")

    section_count = len(positions)

    # 2) 各表表头列齐全
    for title, expected in EXPECTED_COLUMNS.items():
        if title not in positions:
            continue  # 缺节已在 missing_sections 记录
        block = _section_block(content, positions, title)
        rows = _split_table_rows(block)
        if not rows:
            missing_columns[title] = expected[:]  # 整张表缺失
            issues.append(f"「{title}」节缺少表格")
            continue
        header = rows[0]
        header_norm = {_norm(c) for c in header}
        missing = [e for e in expected if _norm(e) not in header_norm]
        if missing:
            # 把 hook/cta类型 这种归一化标签回译成人类可读提示
            missing_columns[title] = missing
            issues.append(f"「{title}」表头缺少列：{'、'.join(missing)}")

    # 3) 六维评分六个维度齐全
    if "六维评分" in positions:
        block = _section_block(content, positions, "六维评分")
        rows = _split_table_rows(block)
        dim_cells = []
        for r in rows[1:]:  # 跳过表头
            if r:
                dim_cells.append(_norm(r[0]))
        dim_set = set(dim_cells)
        for d in EXPECTED_DIMENSIONS:
            if d not in dim_set:
                missing_dimensions.append(d)
        if missing_dimensions:
            issues.append("六维评分缺少维度行：" + "、".join(missing_dimensions))

    # 4) 结构拆解「段落」列无「中段N」占位
    if "结构拆解" in positions:
        block = _section_block(content, positions, "结构拆解")
        rows = _split_table_rows(block)
        # 「段落」列是第 2 列（index 1）
        placeholders = []
        for r in rows[1:]:
            if len(r) >= 2 and MIDFRAME_PLACEHOLDER_RE.search(r[1]):
                placeholders.append(r[1])
        if placeholders:
            issues.append("结构拆解「段落」列含占位符（应为实际段落功能名）：" + "、".join(placeholders[:5]))

    # 5) 不得夹带参考表
    if FORBIDDEN_REFERENCE_HEADING in content:
        issues.append(f"报告中误带「{FORBIDDEN_REFERENCE_HEADING}」参考表（模板规定不输出到报告）")

    # 6) 各节非空 + 截断兜底
    for title in SECTION_TITLES:
        if title not in positions:
            continue
        block = _section_block(content, positions, title).strip()
        if not block:
            issues.append(f"「{title}」节内容为空")
        elif title == "标签":
            # 标签节是末节：若只剩半句（如以反引号开头未闭合、或仅一个孤立符号），提示可能截断。
            # 简化判定：去除空白与反引号后若不足 2 个字符，视为可疑截断。
            stripped = re.sub(r"[`\s·]", "", block)
            if len(stripped) < 2:
                issues.append("「标签」节内容疑似被截断")

    ok = not (missing_sections or missing_columns or missing_dimensions or issues)
    return {
        "ok": ok,
        "section_count": section_count,
        "missing_sections": missing_sections,
        "missing_columns": missing_columns,
        "missing_dimensions": missing_dimensions,
        "issues": issues,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="报告本地结构硬门禁（不达标退出码 12）")
    ap.add_argument("report", help="报告 Markdown 文件路径，或 '-' 从 stdin 读取")
    args = ap.parse_args()

    content = read_content(args.report)
    if content is None:
        emit({"ok": False, "section_count": 0, "missing_sections": SECTION_TITLES[:],
              "missing_columns": {}, "missing_dimensions": [],
              "issues": ["报告文件不存在或读取失败"]})
        return 2
    if not content.strip():
        emit({"ok": False, "section_count": 0, "missing_sections": SECTION_TITLES[:],
              "missing_columns": {}, "missing_dimensions": [],
              "issues": ["报告内容为空"]})
        return 12

    result = verify(content)
    emit(result)
    return 0 if result["ok"] else 12


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        log(f"内部异常：{e}")
        emit({"ok": False, "section_count": 0, "missing_sections": SECTION_TITLES[:],
              "missing_columns": {}, "missing_dimensions": [],
              "issues": [f"unexpected: {e}"]})
        sys.exit(12)
