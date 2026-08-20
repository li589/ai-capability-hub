# logic_doctor.py: 运行时依赖脚本（技能运行调用）
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Logic Doctor — 输出品质核验脚本

对 Agent 生成的 Markdown 输出做“十六维核验”，返回核验报告与可信等级。
用法:
    python3 scripts/logic_doctor.py <output.md>
    cat output.md | python3 scripts/logic_doctor.py -

十六维维度（与 01-一审阶段辩护 等专家技能中定义的核验口径一致）:
    1. 事实与证据一致   2. 请求权与事实一致   3. 法律依据与请求权一致
    4. 程序与请求一致   5. 诉讼策略与事实一致   6. 攻防逻辑一致
    7. 文书结构与策略一致 8. 代理意见与庭审表现一致 9. 主体适格与管辖
    10. 脱敏与隐私合规  11. 风险提示完整性  12. 免责声明
    13. 律师目的确认    14. 证据补强建议    15. 案件方向建议
    16. 过程沉淀与去案情化

说明: 第 1-9、11 维为“结构/一致性”启发式检查（脚本能自动判定的给 PASS/WARN，
需人工/AI 语义判断的给 WARN 并附自查提示）；第 10 维做 PII 硬扫描（发现疑似
身份证号/手机号等真实敏感信息直接 FAIL）。最终可信等级 = 高 / 中 / 低。

v4.20.0 抗堆砌防线（响应 skill-evaluator V3.1 复测 D19）:
    - 单维度须命中 ≥2 个不同关键词才 PASS；仅 1 个关键词时须全文实质法律
      实体词 ≥2 兜底，否则 WARN（提示疑似堆砌/表述单薄）。
    - 十六维全部 PASS 但全文无实质法律实体词 → 追加“抗堆砌兜底”FAIL。
    - ≥3 个维度仅靠单一关键词支撑 → 最终可信等级强制为“低”。
    - SUBSTANTIVE 词表与十六维关键词零重叠（堆砌者无法借词绕过）。
"""

import os
import re
import sys


def _load(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# ---- 抗堆砌防线（v4.20.0）----
# 实质法律实体词：须与下方十六维检查关键词零重叠（堆砌者可借重叠词绕过）。
# v4.21.0：词表与 case_gate.py 统一为同一 12 词核心表（评测 D26 跨脚本一致），
#          已校验与十六维关键词及 GATES/DEPTH_CHECKS 全部零重叠。
SUBSTANTIVE = ("合同", "赔偿", "案由", "罪名", "量刑", "判决", "责任", "标的", "违约金", "利息", "债权", "工伤")


def _has(t, *kw):
    return any(k in t for k in kw)


def _gate_hits(t, *kw):
    """返回命中的关键词列表（去重保序）。"""
    return [k for k in kw if k in t]


def _substantive_count(t):
    """全文实质法律实体词命中数（独立实体词，与十六维关键词零重叠）。"""
    return sum(1 for k in SUBSTANTIVE if k in t)


# ---- 单维检查：返回 (status, note) status ∈ PASS/WARN/FAIL ----
def d_fact_evidence(t):
    ev = _gate_hits(t, "证据", "书证", "证言", "物证", "鉴定意见")
    if len(ev) >= 2 and "事实" in t:
        return "PASS", "存在事实主张且配套证据表述"
    if len(ev) >= 1 and "事实" in t:
        if _substantive_count(t) >= 2:
            return "PASS", "存在事实主张且配套证据表述（实质内容充实）"
        return "WARN", "“事实—证据”仅靠“%s/事实”支撑，疑似堆砌或表述单薄，请充实证据类型与证明对象" % ev[0]
    return "WARN", "建议补充“事实—证据”对应表述，便于核验"


def d_claim_fact(t):
    cl = _gate_hits(t, "请求权", "诉请", "诉讼请求", "请求")
    if len(cl) >= 2 and "事实" in t:
        return "PASS", "请求权/诉请与事实均有呈现"
    if len(cl) >= 1 and "事实" in t:
        if _substantive_count(t) >= 2:
            return "PASS", "请求权/诉请与事实均有呈现（实质内容充实）"
        return "WARN", "请求权与事实对应仅靠“%s/事实”支撑，疑似堆砌或表述单薄，请充实" % cl[0]
    return "WARN", "请求权基础与事实对应不明显"


def d_law_claim(t):
    hits = _gate_hits(t, "法条", "法律依据", "民法典", "刑法", "民事诉讼法", "刑事诉讼法", "条例", "司法解释")
    if len(hits) >= 2:
        return "PASS", "已引用法律/法条依据"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已引用法律/法条依据（实质内容充实）"
        return "WARN", "法律依据仅“%s”单一关键词，疑似堆砌或引用单薄，请补充具体法条" % hits[0]
    return "FAIL", "未发现任何法条/法律依据引用，必须补充"


def d_procedure(t):
    hits = _gate_hits(t, "管辖", "时效", "程序", "送达", "举证期限")
    if len(hits) >= 2:
        return "PASS", "已涉及程序/管辖/时效要素"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已涉及程序/管辖/时效要素（实质内容充实）"
        return "WARN", "程序要素仅“%s”单一关键词，疑似堆砌或表述单薄，请补充管辖/时效/程序说明" % hits[0]
    return "WARN", "建议补充管辖、时效或程序合规说明"


def d_strategy_fact(t):
    if "策略" in t and "事实" in t:
        if _substantive_count(t) >= 2:
            return "PASS", "策略基于事实展开"
        return "WARN", "“策略/事实”仅两词支撑，疑似堆砌或表述单薄，请充实策略论证"
    return "WARN", "诉讼策略与事实关联不显，建议点明"


def d_attack_defense(t):
    me = _gate_hits(t, "我方", "己方")
    op = _gate_hits(t, "对方", "抗辩", "反驳", "质证")
    if len(me) >= 1 and len(op) >= 1:
        if _substantive_count(t) >= 2:
            return "PASS", "攻防两端均有呈现，推理链较完整"
        return "WARN", "攻防表述仅靠“%s/%s”类词支撑，疑似堆砌或表述单薄，请充实" % (me[0], op[0])
    return "WARN", "建议同时呈现我方主张与对方可能的抗辩/质证"


def d_doc_structure(t):
    hits = _gate_hits(t, "文书", "起诉状", "答辩状", "申请书", "代理词", "法律意见书")
    if len(hits) >= 2:
        return "PASS", "已生成对应文书结构"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已生成对应文书结构（实质内容充实）"
        return "WARN", "文书结构仅“%s”单一关键词，疑似堆砌或表述单薄，请明确文书类型与结构" % hits[0]
    return "WARN", "建议明确产出文书及其结构"


def d_opinion_court(t):
    hits = _gate_hits(t, "代理意见", "庭审", "陈述", "法庭")
    if len(hits) >= 2:
        return "PASS", "含代理意见/庭审陈述维度"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "含代理意见/庭审陈述维度（实质内容充实）"
        return "WARN", "庭审/代理意见仅“%s”单一关键词，疑似堆砌或表述单薄，请充实" % hits[0]
    return "WARN", "建议补充庭审表现与书面意见的一致性说明"


def d_standing(t):
    subj = _gate_hits(t, "原告", "被告", "申请人", "被申请人", "当事人", "委托人")
    org = _gate_hits(t, "管辖", "法院", "仲裁")
    if len(subj) >= 1 and len(org) >= 1:
        if _substantive_count(t) >= 2:
            return "PASS", "主体与管辖/受理机关均有标识"
        return "WARN", "主体与管辖仅靠“%s/%s”类词支撑，疑似堆砌或表述单薄，请充实" % (subj[0], org[0])
    return "WARN", "建议明确当事人主体资格与管辖/受理机关"


def d_pii(t):
    notes = []
    # 18 位身份证
    if re.search(r"\b\d{17}[\dXx]\b", t):
        notes.append("疑似身份证号")
    # 11 位手机号
    if re.search(r"\b1[3-9]\d{9}\b", t):
        notes.append("疑似手机号")
    #  bank card
    if re.search(r"\b\d{16,19}\b", t):
        notes.append("疑似长数字账号(银行/证件)")
    if notes:
        return "FAIL", "发现可能泄露的敏感信息：" + "、".join(notes) + "，请脱敏后输出"
    hits = _gate_hits(t, "脱敏", "化名", "张三", "李四", "某甲", "某某")
    if len(hits) >= 2:
        return "PASS", "已做脱敏/化名处理"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已做脱敏/化名处理（实质内容充实）"
        return "WARN", "脱敏声明仅“%s”单一关键词，疑似堆砌或未实际脱敏，请补充化名示例" % hits[0]
    return "WARN", "未发现明显 PII，但仍请确认无真实姓名/证件泄露"


def d_risk(t):
    hits = _gate_hits(t, "风险", "时效", "执行风险", "败诉", "举证不能")
    if len(hits) >= 2:
        return "PASS", "已包含风险提示"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已包含风险提示（实质内容充实）"
        return "WARN", "风险提示仅“%s”单一关键词，疑似堆砌或表述单薄，请补充时效/证据/执行风险提醒" % hits[0]
    return "WARN", "建议补充诉讼时效、证据与执行风险提醒"


def d_disclaimer(t):
    """免责声明核验：交付物必须声明 AI 初稿属性与律师审查义务。"""
    hits = _gate_hits(t, "初稿", "AI生成", "AI 生成", "不得直接使用", "实质审查", "以法院", "以裁判")
    if len(hits) >= 2:
        return "PASS", "已声明初稿属性与审查义务"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已声明初稿属性与审查义务（实质内容充实）"
        return "WARN", "免责声明仅“%s”单一关键词，疑似堆砌或声明不完整，请补全“AI生成初稿，不得直接使用，须经主办律师实质审查”" % hits[0]
    return "FAIL", "未发现免责声明（须标注“AI生成初稿，不得直接使用，须经主办律师实质审查”）"


def d_purpose(t):
    """律师目的确认：交付物应能看出本次处理目标，避免默认写成另一种产出。"""
    hits = _gate_hits(t, "本次目标", "任务目标", "律师目的", "处理目标", "本次目的")
    if len(hits) >= 2:
        return "PASS", "已明确本次处理目标"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已明确本次处理目标（实质内容充实）"
        return "WARN", "目标表述仅“%s”单一关键词，疑似堆砌或表述单薄，请写明本次目标/律师目的" % hits[0]
    return "WARN", "建议写明“本次目标/律师目的”，明确是证据分析、案情分析、文书、程序还是接案评估"


def d_evidence_reinforce(t):
    """证据补强建议：每个证据缺口都应给出可执行的补强路径。"""
    hits = _gate_hits(t, "证据补强", "取证建议", "补充证据", "补强清单", "补强路径")
    if len(hits) >= 2:
        return "PASS", "已包含证据补强建议"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已包含证据补强建议（实质内容充实）"
        return "WARN", "补强建议仅“%s”单一关键词，疑似堆砌或表述单薄，请补充缺什么/为什么缺/怎么补" % hits[0]
    return "WARN", "建议增加证据补强建议：缺什么、为什么缺、怎么补、优先级与期限"


def d_direction(t):
    """案件方向建议：交付后应给出下一步方向，而不是停在分析本身。"""
    hits = _gate_hits(t, "案件方向", "下一步建议", "方向建议", "后续方案", "下一步")
    if len(hits) >= 2:
        return "PASS", "已包含案件方向建议"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已包含案件方向建议（实质内容充实）"
        return "WARN", "方向建议仅“%s”单一关键词，疑似堆砌或表述单薄，请给出具体下一步" % hits[0]
    return "WARN", "建议增加案件方向建议：诉讼、调解、继续补证、执行或观望，并说明触发条件"


def d_process_memory(t):
    """过程沉淀与去案情化：只沉淀可复用方法，不写具体案情。"""
    hits = _gate_hits(t, "过程沉淀", "可复用方法", "方法沉淀", "经验总结", "办案步骤")
    if len(hits) >= 2:
        return "PASS", "已包含过程沉淀/可复用方法"
    if len(hits) == 1:
        if _substantive_count(t) >= 2:
            return "PASS", "已包含过程沉淀/可复用方法（实质内容充实）"
        return "WARN", "沉淀表述仅“%s”单一关键词，疑似堆砌或表述单薄，请补充可复用方法" % hits[0]
    return "WARN", "建议结尾增加过程沉淀卡：本次步骤、可复用方法、改进点，不记录具体案情"


DIMENSIONS = [
    ("事实与证据一致", d_fact_evidence),
    ("请求权与事实一致", d_claim_fact),
    ("法律依据与请求权一致", d_law_claim),
    ("程序与请求一致", d_procedure),
    ("诉讼策略与事实一致", d_strategy_fact),
    ("攻防逻辑一致", d_attack_defense),
    ("文书结构与策略一致", d_doc_structure),
    ("代理意见与庭审表现一致", d_opinion_court),
    ("主体适格与管辖", d_standing),
    ("脱敏与隐私合规", d_pii),
    ("风险提示完整性", d_risk),
    ("免责声明", d_disclaimer),
    ("律师目的确认", d_purpose),
    ("证据补强建议", d_evidence_reinforce),
    ("案件方向建议", d_direction),
    ("过程沉淀与去案情化", d_process_memory),
]


def verify(text):
    rows = []
    for name, fn in DIMENSIONS:
        status, note = fn(text)
        rows.append((name, status, note))
    # v4.20.0 抗堆砌兜底：绝大多数维度通过（≥80%，13/16）但全文无实质法律实体词 → 疑似关键词堆砌
    # v5.0.1 P3-02：阈值表述统一为“命中率≥80%”，与 case_gate.py 同口径（消除 100% vs 81.25% 差）
    pass_cnt = sum(1 for _, s, _ in rows if s == "PASS")
    if pass_cnt / len(DIMENSIONS) >= 0.8 and _substantive_count(text) == 0:
        rows.append(("抗堆砌兜底", "FAIL",
                     "十六维关键词大面积命中但全文无实质法律实体词（合同/赔偿/案由/罪名/量刑/判决/责任等），"
                     "疑似关键词堆砌，须补充实质法律内容后重跑"))
    # 单关键词堆砌特征：≥3 个维度仅靠单一关键词支撑 → 整体降级
    thin = sum(1 for _, s, note in rows if s == "WARN" and "单一关键词" in note)
    fails = sum(1 for _, s, _ in rows if s == "FAIL")
    warns = sum(1 for _, s, _ in rows if s == "WARN")
    if fails >= 2:
        conf = "低"
    elif fails == 1:
        conf = "中"
    else:
        conf = "高" if warns <= 3 else "中"
    # 堆砌信号（≥3 维单关键词 或 抗堆砌兜底 FAIL）→ 强制降为“低”
    if thin >= 3 or any(n == "抗堆砌兜底" for n, _, _ in rows):
        conf = "低"
    return rows, conf


def report(path, text):
    rows, conf = verify(text)
    print(f"# Logic Doctor 十六维核验报告")
    print(f"- 目标文件: {path}")
    print(f"- 维度总数: {len(rows)}")
    print()
    print("| # | 维度 | 结果 | 说明 |")
    print("|:--:|:-----|:----:|:-----|")
    for i, (name, status, note) in enumerate(rows, 1):
        print(f"| {i} | {name} | **{status}** | {note} |")
    print()
    thin = sum(1 for _, s, note in rows if s == "WARN" and "单一关键词" in note)
    if thin:
        print(f"> ⚠ 检测到 {thin} 个维度仅靠单一关键词支撑，已按疑似关键词堆砌降级处理（防堆砌防线 v4.20.0）。")
    print(f"**最终可信等级: {conf}** （FAIL={sum(1 for _,s,_ in rows if s=='FAIL')}, WARN={sum(1 for _,s,_ in rows if s=='WARN')}）")
    print()
    print("> 注：结构/一致性维度为启发式检查，WARN 项需主办律师或 AI 复核；")
    print("> 仅 PII 维度做硬扫描，FAIL 必须脱敏后重新生成。所有文书均为初稿，须经执业律师实质审查。")


def main():
    if len(sys.argv) < 2:
        print("用法: python3 scripts/logic_doctor.py <output.md|->", file=sys.stderr)
        sys.exit(2)
    path = sys.argv[1]
    try:
        text = _load(path)
    except Exception as e:
        print(f"读取失败: {e}", file=sys.stderr)
        sys.exit(1)
    report(path, text)


if __name__ == "__main__":
    main()
