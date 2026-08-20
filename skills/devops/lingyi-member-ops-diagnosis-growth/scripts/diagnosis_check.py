#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会员运营诊断与增长建议 · 输出自检脚本（diagnosis_check.py）

作用：在交付诊断报告前，确定性检查两件事，保证输出在不同模型/不同人笔下
仍然结构一致、评分合规、且不泄露敏感信息：

  1. 结构完整性：诊断 8 部分 + 增长 4 部分齐全、八大维度齐全、成熟度评分在 1–5、有 P0/P1/P2、增长杠杆段存在、路线图含指标列
  2. 脱敏自检：是否出现密钥/凭证（FAIL）或疑似 PII（WARN，需人工复核）

用法：
  python3 diagnosis_check.py report.md
  cat report.md | python3 diagnosis_check.py -          # 从 stdin 读
  python3 diagnosis_check.py --text "$(cat report.md)"  # 直接传文本
  python3 diagnosis_check.py report.md --blocklist brands.txt   # 可选：真实品牌名清单，每行一个

退出码：0 = 通过（无 FAIL）；1 = 存在 FAIL。
仅依赖 Python3 标准库。
"""

import argparse
import re
import sys

# 八大维度（顺序即 SKILL.md 评分表顺序）
DIMENSIONS = [
    "用户资产", "生命周期", "权益体系", "触点链路",
    "内容活动", "转化复购", "数据标签", "组织SOP",
]

# 诊断 8 部分 + 增长 4 部分的判定关键词族（任一命中即视为该章节存在，兼容同义写法）
SECTION_FAMILIES = [
    # 诊断段 8 部分
    ("一句话结论", [r"一句话结论", r"^#.*结论"]),
    ("成熟度总览", [r"成熟度总览", r"成熟度"]),
    ("八维诊断表", [r"八维诊断", r"诊断表", r"现状判断"]),
    ("根因分析",   [r"根因分析", r"根因"]),
    ("机会优先级", [r"机会优先级", r"优先建议", r"优先级"]),
    ("项目事项清单", [r"项目事项", r"事项清单"]),
    ("缺失信息与假设", [r"缺失信息", r"假设"]),
    # 增长段 4 部分
    ("增长杠杆清单", [r"增长杠杆", r"增长杠杆清单"]),
    ("优化路线图", [r"优化路线", r"下一步路线", r"路线图", r"1[-–]2\s*周", r"3[-–]6\s*个月"]),
    ("增长假设与验证", [r"增长假设", r"增长假设与验证", r"If.{0,40}Then"]),
]

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

# 疑似 PII 模式（命中仅 WARN，需人工复核，避免对正常数值误报）
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
    """从八维评分表行里提取 {维度: 分数}，并捕获越界评分。
    仅认「裸数字」单元格，避免命中 90天/1-2周；越界（非 1-5）单独返回供报错。"""
    scores = {}
    out_of_range = []  # [(维度, 值)]
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
                # 裸整数但不在 1-5，记为越界（排除年份等以 0 开头或带单位的）
                val = int(c)
                if val > 5:
                    out_of_range.append((dim, val))
        if not picked and any(d == dim for d, _ in out_of_range):
            pass  # 已记越界
    return scores, out_of_range


def extract_section(text, heading_patterns):
    """返回第一个匹配某个标题正则的章节正文（到下一个同级或更高级标题前）。"""
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
        passes.append("诊断 8 部分 + 增长 4 部分齐全")

    # 2) 八大维度齐全
    missing_dims = [d for d in DIMENSIONS if d not in text]
    if missing_dims:
        fails.append(f"缺少维度：{ '、'.join(missing_dims) }")
    else:
        passes.append("八大维度齐全")

    # 3) 成熟度评分
    scores, out_of_range = parse_scores(text)
    for dim, val in out_of_range:
        fails.append(f"维度「{dim}」评分 {val} 越界（成熟度评分应在 1–5）")
    if len(scores) < 8 and not out_of_range:
        warns.append(f"评分表只解析到 {len(scores)}/8 个维度分数，请确认评分列格式为「裸数字 1-5」")
    elif len(scores) == 8:
        passes.append(f"成熟度评分均在 1–5 范围（{len(scores)} 项，平均 {sum(scores.values())/len(scores):.1f}）")
    # 与声明的整体分数一致性
    m = re.search(r"成熟度[：:]\s*([0-5](?:\.\d)?)\s*/\s*5", text)
    if m and len(scores) == 8:
        declared = float(m.group(1))
        avg = sum(scores.values()) / 8
        if abs(declared - avg) > 0.2:
            warns.append(f"声明的整体成熟度 {declared} 与八维平均 {avg:.1f} 偏差较大，请核对")

    # 4) 优先级：只看「项目事项清单」表格行，避免把诊断表里的 P0 标签也算进来。
    #    不卡 P0 比例（低成熟度业务本就可能有多项合理 P0），改测真正的失败模式——
    #    「有没有做过取舍」：事项 ≥4 时，必须显式存在至少 1 个 P1 和 1 个 P2。
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
        warns.append("项目事项中未见 P0，诊断通常应给出最高优先级行动")
    elif total_items >= 4 and (p1 + p2) == 0:
        warns.append(
            f"项目事项可能未做取舍：≥4 个事项全部标为 P0（P0={p0}/P1=0/P2=0）。"
            f"需把次要事项显式降级到 P1/P2，P0 才有意义"
        )
    else:
        passes.append(f"项目事项已做取舍（P0={p0}/P1={p1}/P2={p2}）")

    # 5) 增长杠杆段存在时，检查五要素表头是否齐全
    growth_section = extract_section(text, [r"增长杠杆", r"增长杠杆清单"])
    if growth_section:
        lever_cols = ["增长杠杆", "对应人群", "预期方向", "验证方式", "依赖条件"]
        missing_cols = []
        # 取该段第一个表格的表头行判定
        header_line = ""
        for line in growth_section.splitlines():
            if "|" in line and ("---" not in line.replace("|", "").replace(" ", "")):
                header_line = line
                break
        if header_line:
            for col in lever_cols:
                if col not in header_line:
                    # 允许近义（依赖/依赖条件）
                    if col == "依赖条件" and "依赖" in header_line:
                        continue
                    if col == "增长杠杆" and "杠杆" in header_line:
                        continue
                    missing_cols.append(col)
            if missing_cols:
                fails.append(f"增长杠杆清单表头缺要素：{ '、'.join(missing_cols) }（需含 增长杠杆/对应人群/预期方向/验证方式/依赖条件）")
            else:
                passes.append("增长杠杆清单五要素表头齐全")
        else:
            warns.append("增长杠杆段未检测到表格，请确认是否用表格列出五要素")
    else:
        fails.append("缺少增长段：未见「增长杠杆清单」（增长 4 部分缺一不可）")

    # 5b) 路线图"指标"列检查（重点修正项：现有产出常漏写指标列）
    #     （5=增长杠杆五要素；5b=路线图指标列；6=脱敏）
    roadmap_section = extract_section(text, [r"优化路线", r"下一步路线", r"路线图"])
    if roadmap_section:
        # 路线图段应含"指标"列
        has_metric_col = ("指标" in roadmap_section)
        # 且不应整段只有动作无指标（简单启发：表头含"指标"或出现"方向性"等词）
        has_directional = bool(re.search(r"方向性|预期|方向区间", roadmap_section))
        if not has_metric_col:
            fails.append("优化路线图缺「指标」列（每条路线必须含 动作/产出/指标（方向性预期）/依赖，这是重点修正项）")
        elif not has_directional:
            warns.append("优化路线图有「指标」列但未见方向性预期表述（如\"方向性提升\"\"方向区间\"），请确认指标给了方向区间而非空泛")
        else:
            passes.append("优化路线图含「指标」列且为方向性预期")

    # 6) 脱敏 —— 密钥（FAIL）
    for pat, label in SECRET_PATTERNS:
        for found in re.findall(pat, text):
            fails.append(f"发现疑似敏感凭证：{label}")
            break
    # 6b) 脱敏 —— PII（WARN）
    for pat, label in PII_PATTERNS:
        if re.search(pat, text):
            warns.append(f"发现{label}，请确认是否需脱敏（可能是真实数据或正常数值）")

    # 7) 可选品牌名黑名单
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
    ap = argparse.ArgumentParser(description="会员运营诊断与增长建议报告输出自检")
    ap.add_argument("file", nargs="?", default=None, help="报告 Markdown 文件路径；缺省或 '-' 读 stdin")
    ap.add_argument("--text", default=None, help="直接传入报告文本")
    ap.add_argument("--blocklist", default=None, help="可选：真实品牌/客户名清单文件，每行一个")
    args = ap.parse_args()

    if args.file is None and args.text is None:
        # 无参时默认读 stdin
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

    print("== 会员运营诊断与增长建议 · 输出自检 ==")
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
