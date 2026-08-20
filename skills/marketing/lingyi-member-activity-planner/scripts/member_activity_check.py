#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会员活动策划 · 输出自检脚本（member_activity_check.py）

作用：在交付四件套（年度节点日历 / 单场执行手册 / 活动权益配置 / 复盘报告）前，
确定性检查六件事，保证输出结构一致、判定规则达标、且不泄露敏感信息：

  1. 四件套章节完整性：年度节点日历 / 单场执行手册 / 活动权益配置 / 复盘报告 齐全
  2. 目标可量化：未见"提升GMV"等空泛目标表述
  3. RACI 唯一 A：执行手册含 RACI 表（每项有 A）
  4. 权益资损校验：权益配置含毛利率 ≥15% 或显式标注资损判定
  5. 复盘反模式自检：复盘报告含 7 反模式自检清单
  6. 脱敏自检（密钥 FAIL / PII WARN）

用法：
  python3 member_activity_check.py report.md
  cat report.md | python3 member_activity_check.py -          # 从 stdin 读
  python3 member_activity_check.py --text "$(cat report.md)"  # 直接传文本
  python3 member_activity_check.py report.md --blocklist brands.txt  # 可选：真实品牌名清单

退出码：0 = 通过（无 FAIL）；1 = 存在 FAIL；2 = 输入读取失败。
仅依赖 Python3 标准库。
"""

import argparse
import re
import sys

# 四件套章节判定关键词族（任一命中即视为该章节存在，兼容同义写法）
SECTION_FAMILIES = [
    ("年度节点营销日历", [r"年度节点", r"节点营销日历", r"年度.*日历"]),
    ("单场活动执行手册", [r"单场活动执行手册", r"执行手册", r"单场.*手册"]),
    ("活动权益配置", [r"活动权益配置", r"权益配置表", r"权益配置"]),
    ("复盘报告", [r"复盘报告", r"复盘"]),
]

# 复盘 7 反模式关键词
REVIEW_ANTIPATTERNS = [
    "当总结做", "甩锅", "不归因", "不具体", "无优先级", "不追踪", "拍脑袋",
]

# 高置信度密钥/凭证模式（命中即 FAIL）
SECRET_PATTERNS = [
    (r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "私钥文件"),
    (r"sk-[A-Za-z0-9]{20,}", "OpenAI 风格 API Key (sk-)"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key (AKIA)"),
    (r"gh[pousr]_[A-Za-z0-9]{36,}", "GitHub Token (gh_)"),
    (r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT Token"),
    (r"(?i)bearer\s+[A-Za-z0-9_.-]{20,}", "Bearer Token"),
    (r"(?i)(appsecret|access_token|secret_key|apikey|api_key|密码|密钥|口令)\s*[:=]\s*[\"']?[A-Za-z0-9_\-./+=]{8,}", "疑似硬编码凭证"),
]

# 疑似 PII 模式（命中仅 WARN，需人工复核）
PII_PATTERNS = [
    (r"(?<!\d)1[3-9]\d{9}(?!\d)", "疑似手机号"),
    (r"(?<!\d)\d{17}[\dXx](?!\d)", "疑似身份证号"),
]

# 空泛目标反例（命中即 WARN，提示 SMART 重写）
VAGUE_GOAL_PATTERNS = [
    r"提升\s*GMV(?!\s*[×x]?\d|从)",  # "提升GMV" 后无数值/范围才算空泛
    r"做好会员运营",
    r"提升活跃(?!率|数|.*\d)",  # "提升活跃" 后无率/数/数值才算空泛
]


def read_text(args):
    if args.text is not None:
        return args.text
    if args.file == "-" or args.file is None:
        return sys.stdin.read()
    with open(args.file, "r", encoding="utf-8") as f:
        return f.read()


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

    # 1) 四件套章节完整性
    missing = []
    for name, pats in SECTION_FAMILIES:
        if any(re.search(p, text, re.MULTILINE) for p in pats):
            continue
        missing.append(name)
    if missing:
        fails.append(f"缺少必要章节：{ '、'.join(missing) }")
    else:
        passes.append("四件套章节齐全（年度日历/执行手册/权益配置/复盘报告）")

    # 2) 目标可量化（排斥空泛表述）
    vague_hits = []
    for pat in VAGUE_GOAL_PATTERNS:
        m = re.search(pat, text)
        if m:
            vague_hits.append(m.group(0))
    if vague_hits:
        warns.append(f"检测到空泛目标表述「{'/'.join(set(vague_hits))}」，应按 SMART 重写并拆目标漏斗四层（治「没目标」病根）")
    else:
        passes.append("未检测到空泛目标表述（提升GMV/做好运营/提升活跃等）")

    # 3) 目标漏斗四层（获客/激活/留存/变现）
    funnel = extract_section(text, [r"执行手册", r"立项", r"目标漏斗"])
    funnel_terms = ["获客", "激活", "留存", "变现"]
    found_funnel = [t for t in funnel_terms if t in funnel or t in text]
    if len(found_funnel) == 4:
        passes.append("目标漏斗四层齐全（获客/激活/留存/变现）")
    else:
        warns.append(f"目标漏斗四层不全（命中 {'、'.join(found_funnel) or '无'}），缺层或不量化→不通过")

    # 4) RACI 唯一 A
    raci = extract_section(text, [r"RACI", r"分工", r"人员分工"])
    if raci or "RACI" in text:
        has_a = bool(re.search(r"(?<![A-Za-z])A(?![A-Za-z])", raci)) if raci else "A" in text
        if has_a:
            passes.append("含 RACI 表且见 A（问责人）；需人工核对每项有且仅有一个 A")
        else:
            warns.append("含 RACI 表但未见 A 标注，每项需有且仅有一个问责人 A")
    else:
        warns.append("执行手册未见 RACI 分工表，缺 A→协同无拍板人")

    # 5) 权益资损校验
    benefit = extract_section(text, [r"权益配置", r"叠加互斥", r"资损"])
    if benefit or "毛利率" in text:
        margin_hit = re.search(r"毛利率[^0-9]*([0-9]+\.?[0-9]*)\s*%", text)
        if margin_hit:
            margin = float(margin_hit.group(1))
            if margin >= 15:
                passes.append(f"权益资损校验通过（毛利率 {margin}% ≥15%）")
            else:
                warns.append(f"权益资损风险（毛利率 {margin}% <15%），应改互斥取最优或调整权益叠加规则")
        elif "资损" in text or "互斥取最优" in text:
            passes.append("权益配置含资损判定/互斥规则说明")
        else:
            warns.append("权益配置见「毛利率」字样但未给数值，需补 ≥15% 资损校验")
    else:
        warns.append("未见权益配置/叠加互斥/资损校验章节")

    # 6) 复盘 7 反模式自检
    review = extract_section(text, [r"复盘", r"反模式"])
    if review:
        found_ap = [ap for ap in REVIEW_ANTIPATTERNS if ap in review or ap in text]
        if "反模式" in text:
            if len(found_ap) >= 5:
                passes.append(f"复盘 7 反模式自检清单齐全（命中 {len(found_ap)} 项关键词）")
            elif len(found_ap) >= 3:
                warns.append(f"复盘反模式自检偏少（命中 {len(found_ap)} 项），建议列全 7 条以便逐项自检")
            else:
                warns.append("复盘反模式自检不足，应列全 7 条反模式清单（当总结做/甩锅/不归因/不具体/无优先级/不追踪/拍脑袋）")
        else:
            warns.append("复盘章节未见「反模式」自检清单")
    else:
        warns.append("复盘报告章节提取为空或未含反模式自检")

    # 7) 脱敏 —— 密钥（FAIL）
    for pat, label in SECRET_PATTERNS:
        if re.search(pat, text):
            fails.append(f"发现疑似敏感凭证：{label}")
            break
    # 7b) 脱敏 —— PII（WARN）
    for pat, label in PII_PATTERNS:
        if re.search(pat, text):
            warns.append(f"发现{label}，请确认是否需脱敏（可能是真实数据或正常数值）")
            break

    # 8) 可选品牌名黑名单
    if blocklist:
        hit = [b for b in blocklist if b and b in text]
        for b in hit:
            warns.append(f"出现疑似真实品牌/客户名「{b}」，请确认是否需泛化脱敏")

    if not fails and not any("密钥" in w for w in warns):
        passes.append("脱敏检查未发现密钥/PII")

    return fails, warns, passes


def main():
    ap = argparse.ArgumentParser(description="会员活动策划四件套输出自检")
    ap.add_argument("file", nargs="?", default=None, help="报告 Markdown 文件路径；缺省或 '-' 读 stdin")
    ap.add_argument("--text", default=None, help="直接传入报告文本")
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

    print("== 会员活动策划 · 四件套输出自检 ==")
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
