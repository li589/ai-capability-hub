#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用户画像与人群洞察 · 输出自检脚本（persona_check.py）

作用：在交付画像与洞察方案前，确定性检查两件事，保证输出在不同模型/不同人笔下
仍然结构一致、就绪度评分合规、且不泄露敏感信息：

  1. 结构完整性：9 个必要章节齐全、六维就绪度齐全、评分在 1–5、有 P0/P1/P2
  2. 脱敏自检：是否出现密钥/凭证（FAIL）或疑似 PII（WARN，需人工复核）

用法：
  python3 persona_check.py report.md
  cat report.md | python3 persona_check.py -
  python3 persona_check.py --text "$(cat report.md)"
  python3 persona_check.py report.md --blocklist brands.txt

退出码：0 = 通过（无 FAIL）；1 = 存在 FAIL。仅依赖 Python3 标准库。
"""

import argparse
import re
import sys

# 六维（顺序即 SKILL.md 评分表顺序）
DIMENSIONS = [
    "数据基础", "标签体系", "分群建模", "画像刻画", "应用落地", "治理迭代",
]

# 必要章节的判定关键词族（任一命中即视为该章节存在；pattern 用长串，禁宽词避免全文误命中）
SECTION_FAMILIES = [
    ("一句话结论", [r"一句话结论", r"^#.*结论"]),
    ("数据基础与画像就绪度", [r"数据基础与画像就绪度", r"画像就绪度", r"就绪度评分表", r"数据基础"]),
    ("标签体系设计", [r"标签体系设计", r"标签体系", r"标签分层"]),
    ("用户分群模型", [r"用户分群模型", r"分群模型", r"分群定义"]),
    ("代表性用户画像", [r"代表性用户画像", r"代表性画像", r"用户画像", r"persona"]),
    ("画像应用场景", [r"画像应用场景", r"应用场景", r"画像应用"]),
    ("人群洞察与动作回路", [r"人群洞察与动作回路", r"人群洞察", r"动作回路", r"机会矩阵", r"opportunity"]),
    ("项目事项清单", [r"项目事项", r"事项清单"]),
    ("缺失信息与假设", [r"缺失信息", r"假设"]),
]
NEEDED_SECTION_COUNT = len(SECTION_FAMILIES)

# 高置信度密钥/凭证模式（命中即 FAIL）
SECRET_PATTERNS = [
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "私钥文件"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI 风格 API Key (sk-)"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key (AKIA)"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "GitHub Token (gh_)"),
    (r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT Token"),
    (r"(?i)bearer\s+[A-Za-z0-9_.-]{20,}", "Bearer Token"),
    (r"(?i)(appsecret|access_token|secret_key|apikey|api_key|密码|密钥|口令)\s*[:=]\s*[\"\']?[A-Za-z0-9_\-./+=]{8,}", "疑似硬编码凭证"),
]

# 疑似 PII 模式（命中仅 WARN）
PII_PATTERNS = [
    (r"(?<!\d)1[3-9]\d{9}(?!\d)", "疑似手机号"),
    (r"(?<!\d)\d{17}[\dXx](?!\d)", "疑似身份证号"),
]


def read_text(args):
    if args.text is not None:
        return args.text
    if args.file == "-" or args.file is None:
        return sys.stdin.read()
    with open(args.file, "r", encoding="utf-8") as f:
        return f.read()


def parse_scores(text):
    """从就绪度评分表行提取 {维度: 分数}，捕获越界评分。仅认裸数字 1-5。"""
    scores = {}
    out_of_range = []
    for line in text.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        dim = cells[0]
        if dim not in DIMENSIONS:
            continue
        picked = False
        for c in cells[1:]:
            if re.fullmatch(r"[1-5]", c):
                scores[dim] = int(c)
                picked = True
                break
            elif re.fullmatch(r"\d+", c) and not c.startswith("0"):
                val = int(c)
                if val > 5:
                    out_of_range.append((dim, val))
        if not picked and any(d == dim for d, _ in out_of_range):
            pass
    return scores, out_of_range


def extract_section(text, heading_patterns):
    lines = text.splitlines()
    start = None
    level = 0
    for i, ln in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)", ln)
        if m and any(re.search(p, m.group(2)) for p in heading_patterns):
            start = i + 1
            level = len(m.group(1))
            break
    if start is None:
        return ""
    out = []
    for ln in lines[start:]:
        m = re.match(r"^(#{1,6})\s+", ln)
        if m and len(m.group(1)) <= level:
            break
        out.append(ln)
    return "\n".join(out)


def check(text, blocklist):
    fails, warns, passes = [], [], []

    # 1) 章节完整性
    missing_sections = []
    for name, pats in SECTION_FAMILIES:
        if any(re.search(p, text, re.MULTILINE) for p in pats):
            continue
        missing_sections.append(name)
    if missing_sections:
        fails.append(f"缺少必要章节：{ '、'.join(missing_sections) }")
    else:
        passes.append(f"{NEEDED_SECTION_COUNT} 个必要章节齐全")

    # 2) 六维齐全
    missing_dims = [d for d in DIMENSIONS if d not in text]
    if missing_dims:
        fails.append(f"缺少维度：{ '、'.join(missing_dims) }")
    else:
        passes.append("六维就绪度齐全")

    # 3) 就绪度评分
    scores, out_of_range = parse_scores(text)
    for dim, val in out_of_range:
        fails.append(f"维度「{dim}」评分 {val} 越界（就绪度评分应在 1–5）")
    if len(scores) < 6 and not out_of_range:
        warns.append(f"评分表只解析到 {len(scores)}/6 个维度分数，请确认评分列为「裸数字 1-5」")
    elif len(scores) == 6:
        passes.append(f"就绪度评分均在 1–5 范围（6 项，平均 {sum(scores.values())/6:.1f}）")
    m = re.search(r"就绪度[：:]\s*([0-5](?:\.\d)?)\s*/\s*5", text)
    if m and len(scores) == 6:
        declared = float(m.group(1))
        avg = sum(scores.values()) / 6
        if abs(declared - avg) > 0.2:
            warns.append(f"声明的整体就绪度 {declared} 与六维平均 {avg:.1f} 偏差较大，请核对")

    # 4) 项目事项取舍
    items = extract_section(text, [r"项目事项", r"事项清单"])
    item_p = {"P0": 0, "P1": 0, "P2": 0}
    for line in items.splitlines():
        if "|" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        for c in cells:
            if c in item_p:
                item_p[c] += 1
                break
    total_items = sum(item_p.values())
    p0, p1, p2 = item_p["P0"], item_p["P1"], item_p["P2"]
    if total_items == 0:
        warns.append("项目事项清单未解析到 P0/P1/P2 标记，请确认事项表格式")
    elif p0 == 0:
        warns.append("项目事项中未见 P0，通常应给出最高优先级事项")
    elif total_items >= 4 and (p1 + p2) == 0:
        warns.append(
            f"项目事项可能未做取舍：≥4 个事项全部标为 P0（P0={p0}/P1=0/P2=0）。"
            f"需把次要事项显式降级到 P1/P2")
    else:
        passes.append(f"项目事项已做取舍（P0={p0}/P1={p1}/P2={p2}）")

    # 5) 脱敏 —— 密钥（FAIL）
    for pat, label in SECRET_PATTERNS:
        if re.search(pat, text):
            fails.append(f"发现疑似敏感凭证：{label}")
            break
    # 5b) PII（WARN）
    for pat, label in PII_PATTERNS:
        if re.search(pat, text):
            warns.append(f"发现{label}，请确认是否需脱敏（可能是真实数据或正常数值）")

    # 6) 可选品牌名黑名单
    if blocklist:
        hit = [b for b in blocklist if b and b in text]
        for b in hit:
            warns.append(f"出现疑似真实品牌/客户名「{b}」，请确认是否需泛化脱敏")

    if not fails and not warns:
        passes.append("脱敏检查未发现密钥/PII")
    elif not fails:
        passes.append("脱敏检查未发现密钥（仅 PII 复核项，见 WARN）")

    return fails, warns, passes


def main():
    ap = argparse.ArgumentParser(description="用户画像与人群洞察方案输出自检")
    ap.add_argument("file", nargs="?", default=None, help="方案 Markdown 文件路径；缺省或 '-' 读 stdin")
    ap.add_argument("--text", default=None, help="直接传入方案文本")
    ap.add_argument("--blocklist", default=None, help="可选：真实品牌/客户名清单文件，每行一个")
    args = ap.parse_args()

    if args.file is None and args.text is None:
        args.file = "-"

    blocklist = []
    if args.blocklist:
        try:
            with open(args.blocklist, "r", encoding="utf-8") as f:
                blocklist = [ln.strip() for ln in f if ln.strip()]
        except OSError as e:
            print(f"读取 blocklist 失败：{e}", file=sys.stderr)

    try:
        text = read_text(args)
    except OSError as e:
        print(f"读取输入失败：{e}", file=sys.stderr)
        return 2

    if not text.strip():
        print("输入为空，无可检查内容。", file=sys.stderr)
        return 2

    fails, warns, passes = check(text, blocklist)

    print("== 用户画像与人群洞察 · 输出自检 ==")
    for p in passes:
        print(f"[PASS] {p}")
    for w in warns:
        print(f"[WARN] {w}")
    for f in fails:
        print(f"[FAIL] {f}")

    verdict = "PASS" if not fails else "FAIL"
    print(f"== 结果：{verdict}（{len(fails)} FAIL，{len(warns)} WARN）==")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
