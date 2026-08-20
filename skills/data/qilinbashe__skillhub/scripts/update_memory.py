# update_memory.py: 运行时依赖脚本（技能运行调用）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长期记忆写入与校验脚本（只记方法，不记案情）。

用法：
  python scripts/update_memory.py --check
  python scripts/update_memory.py --category 办案流程 --entry "可复用步骤：..."
  python scripts/update_memory.py --category 证据补强 --entry "..." --dry-run

规则：
  1. 禁止写入 PII（身份证/手机号/银行卡等）；
  2. 禁止写入可识别案情的案号、客户姓名、具体金额等事实；
  3. 每次写入后自动执行 --check，发现敏感内容则拒绝写入；
  4. v4.21.0：写入前经 fuzzify() 数字模糊化（金额→量级、日期→相对时点、
     姓名→关系标签），与 SKILL.md 声明对齐；
  5. v4.21.0：MEMORY.md 容量上限 MAX_ENTRIES（默认 500 条），超出按 FIFO
     淘汰最旧条目。
"""

import argparse
import os
import re
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_PATH = os.path.join(PKG_ROOT, "MEMORY.md")
CATEGORIES = ("办案流程", "证据补强", "发问规则", "质量闸门", "低分项整改", "方法论")
MAX_ENTRIES = 500
SECTION_MARKER = "## 最新迭代"
BS = chr(92)
D = BS + "d"

PII_PATTERNS = [
    (r"\b\d{17}[\dXx]\b", "疑似身份证号"),
    (r"\b1[3-9]\d{9}\b", "疑似手机号"),
    (r"\b\d{16,19}\b", "疑似长数字账号"),
]
FACT_PATTERNS = [
    (r"案号\s*[:：]?\s*[（(]?\d", "疑似具体案号"),
    (r"身份证号\s*[:：]?\s*\d{6,}", "疑似身份证字段"),
    (r"手机号\s*[:：]?\s*1[3-9]\d{9}", "疑似手机字段"),
    (r"银行卡\s*[:：]?\s*\d{6,}", "疑似银行卡字段"),
    (r"住址\s*[:：]?\s*[\u4e00-\u9fa5]{2,}", "疑似住址字段"),
    (r"(张|李|王|刘|陈|杨|赵|黄|周|吴|徐|孙|马|朱|胡|郭|何|罗|高|林)某", "疑似客户化名"),
]


def violations(text):
    bad = []
    for pattern, label in PII_PATTERNS + FACT_PATTERNS:
        if re.search(pattern, text):
            bad.append(label)
    return bad


def fuzzify(text):
    """数字模糊化（v4.21.0，与 SKILL.md“沉淀前必过 PII 硬过滤与数字模糊化”声明对齐）。

    金额→量级（10万元→十万级）、日期→相对时点（2026-03-05→近期）、
    姓名→关系标签（张某某→当事人）。仅处理明确可识别的模式，不做激进替换。
    """
    # 金额 → 量级
    def _amount(m):
        num = float(m.group(1))
        unit = m.group(2) or ""
        if unit == "亿":
            return "亿元级"
        if unit == "万":
            if num >= 10000:
                return "千万元级"
            if num >= 100:
                return "百万元级"
            return "万元级"
        if num >= 100000:
            return "十万级"
        if num >= 10000:
            return "万级"
        if num >= 1000:
            return "千元级"
        return "小额（千元以下）"

    text = re.sub(r"(" + D + r"+(?:\." + D + r"+)?)\s*(亿|万)?\s*元", _amount, text)
    # 日期 → 相对时点
    text = re.sub(r"20" + D + r"{2}[-/年]" + D + r"{1,2}[-/月]" + D + r"{1,2}日?", "近期（相对时点）", text)
    text = re.sub(r"20" + D + r"{2}[-/年]" + D + r"{1,2}[-/月]", "近期（相对时点）", text)
    text = re.sub(r"20" + D + r"{2}年", "近年", text)
    # 姓名 → 关系标签（明确化名/称谓模式）
    text = re.sub(r"(?:张|李|王|刘|陈|杨|赵|黄|周|吴|徐|孙|马|朱|胡|郭|何|罗|高|林)某+", "当事人", text)
    return text


def _enforce_capacity():
    """MEMORY.md 容量上限：超出 MAX_ENTRIES 按 FIFO 淘汰最旧条目（v4.21.0）。"""
    text = read_memory()
    if text is None:
        return 0
    lines = text.split("\n")
    try:
        idx = lines.index(SECTION_MARKER)
    except ValueError:
        return 0
    # 节尾 = 下一个 "## " 标题行
    end = len(lines)
    for i in range(idx + 1, len(lines)):
        if lines[i].startswith("## ") and lines[i] != SECTION_MARKER:
            end = i
            break
    sec = lines[idx:end]
    entry_idx = [i for i, l in enumerate(sec) if re.match(r"^- 20" + D + r"{2}-" + D + r"{2}-" + D + r"{2} ", l)]
    removed = 0
    while len(entry_idx) > MAX_ENTRIES:
        j = entry_idx[-1]  # 最新条目在前，最旧条目在节尾 → FIFO
        del sec[j]
        entry_idx.pop()
        removed += 1
    if removed:
        lines[idx:end] = sec
        with open(MEMORY_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print("[memory][OK] 容量上限触发，FIFO 淘汰最旧条目 %d 条" % removed)
    return removed


def read_memory():
    if not os.path.isfile(MEMORY_PATH):
        return None
    with open(MEMORY_PATH, "r", encoding="utf-8") as f:
        return f.read()


def check_memory():
    text = read_memory()
    if text is None:
        print("[memory][X] MEMORY.md 缺失")
        return False
    bad = violations(text)
    if "只记“怎么办案”" not in text and "只记" not in text:
        bad.append("缺少长期记忆边界声明")
    if bad:
        print("[memory][X] 校验未通过：%s" % "、".join(sorted(set(bad))))
        return False
    print("[memory][OK] MEMORY.md 无 PII / 具体案情标识")
    return True


def append_entry(category, entry, dry_run=False):
    if category not in CATEGORIES:
        print("[memory][X] category 必须是：%s" % " / ".join(CATEGORIES), file=sys.stderr)
        return False
    entry = entry.strip()
    if len(entry) < 10:
        print("[memory][X] entry 太短，请写成可复用的完整方法", file=sys.stderr)
        return False
    bad = violations(category + entry)
    if bad:
        print("[memory][X] 拒绝写入：%s" % "、".join(bad), file=sys.stderr)
        return False
    # v4.21.0：数字模糊化（金额→量级、日期→相对时点、姓名→关系标签）
    entry = fuzzify(entry)

    today = datetime.now().strftime("%Y-%m-%d")
    line = "- %s [%s] %s" % (today, category, entry)
    if dry_run:
        print("[memory][dry-run] 将追加：%s" % line)
        return True

    text = read_memory()
    if text is None:
        print("[memory][X] MEMORY.md 缺失，请先创建后再写入", file=sys.stderr)
        return False
    if line in text:
        print("[memory][OK] 该条目已存在，跳过")
        return True

    marker = "## 最新迭代"
    if marker in text:
        text = text.replace(marker, marker + "\n\n" + line, 1)
    else:
        text = text.rstrip() + "\n\n## 最新迭代\n\n" + line + "\n"
    with open(MEMORY_PATH, "w", encoding="utf-8") as f:
        f.write(text)

    # v4.21.0：容量上限 FIFO 淘汰
    _enforce_capacity()

    if not check_memory():
        print("[memory][X] 写入后校验失败，请检查内容", file=sys.stderr)
        return False
    print("[memory][OK] 已写入长期记忆：%s" % line)
    return True


def main():
    ap = argparse.ArgumentParser(description="律师助手长期记忆写入/校验")
    ap.add_argument("--check", action="store_true", help="校验 MEMORY.md")
    ap.add_argument("--category", choices=CATEGORIES, help="记忆分类")
    ap.add_argument("--entry", help="可复用的方法条目")
    ap.add_argument("--dry-run", action="store_true", help="仅预览，不写入")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if check_memory() else 1)
    if not args.category or not args.entry:
        ap.print_help()
        sys.exit(2)
    sys.exit(0 if append_entry(args.category, args.entry, args.dry_run) else 1)


if __name__ == "__main__":
    main()
