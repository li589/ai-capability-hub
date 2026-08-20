# case_gate.py: 运行时依赖脚本（技能运行调用）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""case_gate.py — 办案状态机闸门校验（v4.5.1 交付；v4.19.0 防关键词堆砌升级）

用法：
  python scripts/case_gate.py <status_card.md>
  type status_card.md | python scripts/case_gate.py -
  python scripts/case_gate.py --template
  python scripts/case_gate.py --check
  python scripts/case_gate.py --depth-check <status_card.md>

闸门不过即退出码 1，禁止进入下一阶。

v4.19.0 防堆砌升级：
  - 七闸门（check_card）：单闸门须命中 ≥2 个不同关键词才 PASS（防单一关键词堆砌绕过）；
  - 内容充实度：全闸门关键词均被塞入（命中 ≥7 组）但无实质法律实体词 → 判 FAIL；
  - 深挖自检（check_depth）：保持单关键词命中兼容，新增“内容充实度”独立行。
"""

import argparse
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

GATES = [
    ("目的确认", ("本次目标", "意图", "目的", "I1", "I2", "I3", "I4", "I5", "I6")),
    ("案情确认", ("案情确认书", "事实时间线", "当事人", "争议焦点", "缺口清单")),
    ("证据精读", ("证据补强", "要件矩阵", "证据清单", "四件套", "矛盾风险")),
    ("深度分析", ("九步法", "案件方向", "方向建议", "攻防", "要件归入")),
    ("法条核验", ("法条核验", "已核验", "多源", "96", "权威案例")),
    ("文书交付", ("文书", "初稿", "十六维", "Logic Doctor", "免责声明")),
    ("过程沉淀", ("过程沉淀", "可复用", "MEMORY", "方法论", "playbook")),
]

PII_PATTERNS = [
    r"\b\d{17}[\dXx]\b",
    r"\b1[3-9]\d{9}\b",
    r"\b\d{16,19}\b",
]

DEPTH_CHECKS = [
    ("目的确认", ("本次目标", "意图", "目的", "I1", "I2", "I3", "I4", "I5", "I6")),
    ("案情确认", ("时间", "日期", "当事人", "争议焦点", "缺口清单")),
    ("证据精读", ("证据补强", "要件矩阵", "证据编号", "四件套", "待核实")),
    ("深度分析", ("九步法", "抗辩", "对方", "要件归入", "方向建议")),
    ("法条核验", ("法条核验", "已核验", "多源", "权威案例")),
    ("文书交付", ("文书", "十六维", "Logic Doctor", "免责声明")),
    ("过程沉淀", ("过程沉淀", "可复用", "MEMORY", "方法论", "复盘")),
]

# v4.19.0：实质法律实体词——关键词堆砌防线（堆满闸门词但无实质内容 → 判 FAIL）
# v4.21.0：词表与 logic_doctor.py 统一为同一 12 词核心表（评测 D26 跨脚本一致），
#          并校验与 GATES/DEPTH_CHECKS 及十六维关键词零重叠（堆砌者无法借词绕过）。
SUBSTANTIVE = ("合同", "赔偿", "案由", "罪名", "量刑", "判决", "责任", "标的", "违约金", "利息", "债权", "工伤")


def _thin_gates(text, checks):
    """统计仅靠单一关键词支撑的闸门数（v4.21.0 防堆砌：≥3 强制降级提示）。"""
    return sum(1 for _, kws in checks if len(_gate_hits(text, kws)) == 1)


def _gate_hits(text, keywords):
    """返回命中的关键词列表（去重保序）。"""
    return [k for k in keywords if k in text]


def _substantive_check(text, checks):
    """内容充实度：闸门关键词大面积命中（≥80% 组数）但无实质法律实体词 → 判 FAIL。

    防“关键词堆砌绕过”：攻击者把每个闸门的关键词各写一遍凑齐 PASS，但内容空洞。
    v5.0.1 P3-02：兜底阈值由“全部闸门命中(100%)”统一为“命中率≥80%”，
    与 logic_doctor.py 的 ≥13/16 维（81.25%）同一口径，消除跨脚本阈值差。
    """
    gate_hits = sum(1 for _, kws in checks if _gate_hits(text, kws))
    substantive = sum(1 for k in SUBSTANTIVE if k in text)
    if gate_hits / len(checks) >= 0.8 and substantive == 0:
        return "FAIL"
    return "PASS"


def load(path):
    if path == "-":
        data = sys.stdin.buffer.read()
        for enc in ("utf-8-sig", "utf-16", "gbk"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
        return data.decode("utf-8", errors="replace")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def check_card(text):
    rows = []
    thin = 0
    for name, keywords in GATES:
        hits = _gate_hits(text, keywords)
        if len(hits) == 1:
            thin += 1
        # v4.19.0 防关键词堆砌：单闸门须命中 ≥2 个不同关键词才 PASS
        rows.append((name, "PASS" if len(hits) >= 2 else "FAIL"))
    rows.append(("内容充实度", _substantive_check(text, GATES)))
    pii = [p for p in PII_PATTERNS if re.search(p, text)]
    if pii:
        rows.append(("PII脱敏", "FAIL"))
    else:
        rows.append(("PII脱敏", "PASS" if "脱敏" in text else "WARN"))
    # v5.0.1 防堆砌降级（统一口径）：≥3 个闸门仅靠单一关键词支撑 → FAIL 强制降级（与 logic_doctor 强制"低"同口径）
    if thin >= 3:
        rows.append(("抗堆砌降级", "FAIL"))
    return rows


def check_depth(text):
    rows = []
    thin = 0
    for name, keywords in DEPTH_CHECKS:
        hits = _gate_hits(text, keywords)
        if len(hits) == 1:
            thin += 1
        if any(k in text for k in keywords):
            rows.append((name, "PASS"))
        else:
            rows.append((name, "FAIL"))
    rows.append(("内容充实度", _substantive_check(text, DEPTH_CHECKS)))
    pii = [p for p in PII_PATTERNS if re.search(p, text)]
    rows.append(("PII脱敏", "FAIL" if pii else "PASS"))
    # v5.0.1 防堆砌降级（统一口径）：≥3 个闸门仅靠单一关键词支撑 → FAIL 强制降级（与 logic_doctor 强制"低"同口径）
    if thin >= 3:
        rows.append(("抗堆砌降级", "FAIL"))
    return rows


def check_pack():
    problems = []
    for rel in ("SKILL.md", os.path.join("agents", "31-总控路由.md")):
        p = os.path.join(PKG_ROOT, rel)
        if not os.path.isfile(p):
            problems.append("%s 缺失" % rel)
            continue
        text = open(p, encoding="utf-8").read()
        if "case_gate" not in text and "case_gate.py" not in text:
            problems.append("%s 未引用 case_gate.py" % rel)
    if problems:
        print("[case_gate][X] %s" % "；".join(problems), file=sys.stderr)
        return False
    print("[case_gate][OK] SKILL/31 已挂载办案状态机")
    return True


def main():
    ap = argparse.ArgumentParser(description="律师助手办案状态机闸门")
    ap.add_argument("path", nargs="?", help="状态卡/交付物 Markdown，- 表示 stdin")
    ap.add_argument("--template", action="store_true", help="输出状态卡模板")
    ap.add_argument("--check", action="store_true", help="检查 SKILL/31 是否挂载状态机")
    ap.add_argument("--depth-check", nargs="?", const="-", metavar="PATH",
                    help="按自检证明第八章深挖自检表校验状态卡")
    args = ap.parse_args()

    if args.check:
        sys.exit(0 if check_pack() else 1)
    if args.template:
        print("""━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 案件状态卡（七闸门）
━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 本次目标：I1-I6 / 自定义
📌 案由：
✅ 案情确认：案情确认书 / 缺口清单
✅ 证据精读：四件套 / 证据补强清单
✅ 深度分析：九步法 / 方向建议书
✅ 法条核验：多源 / 权威案例
✅ 文书交付：十六维核验 / 免责声明
✅ 过程沉淀：可复用方法 / MEMORY.md
⚠️ 脱敏声明：未使用真实姓名/证件/地址
━━━━━━━━━━━━━━━━━━━━━━━━━━""")
        sys.exit(0)
    if args.depth_check is not None:
        path = args.depth_check if args.depth_check != "-" else (args.path or "-")
        rows = check_depth(load(path))
        fails = [n for n, s in rows if s == "FAIL"]
        print("# case_gate 阶段深挖自检")
        for name, status in rows:
            print("- %s: %s" % (name, status))
        if fails:
            print("[X] 深挖未达标：%s" % "、".join(fails), file=sys.stderr)
            sys.exit(1)
        print("[OK] 阶段深挖自检通过")
        sys.exit(0)
    if not args.path:
        ap.print_help()
        sys.exit(2)

    rows = check_card(load(args.path))
    fails = [n for n, s in rows if s == "FAIL"]
    warns = [n for n, s in rows if s == "WARN"]
    print("# case_gate 七闸门核验")
    for name, status in rows:
        print("- %s: %s" % (name, status))
    if fails:
        print("[X] 未通过闸门：%s" % "、".join(fails), file=sys.stderr)
        sys.exit(1)
    print("[OK] 七闸门通过%s" % ("，WARN: %s" % "、".join(warns) if warns else ""))
    sys.exit(0)


if __name__ == "__main__":
    main()
