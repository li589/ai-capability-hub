#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOC 批量笔记「同质化 + 合规」发布前自检工具
================================================
用途：多个 KOC 同期推广同一产品时，在【发布前】本地自查，
     模拟平台的相似度检测逻辑，把风险笔记拦在发布之前。

检测项：
  1. 正文语义相似度   —— 字符 3-gram Jaccard + TF-IDF 余弦（双算法交叉）
  2. 标题结构相似度   —— 句式骨架比对（数字/产品名归一化后）
  3. 标签组合重复率   —— 话题标签 Jaccard
  4. 开头句式雷同     —— 前 20 字比对
  5. 违禁词/极限词    —— 广告法 + 小红书 2026 规则词库
  6. 信息密度         —— CES 3.0 要求图文正文 ≥ 400 字
  7. 发布节奏         —— 同日同品牌笔记数告警

零依赖：仅使用 Python 标准库，无需 pip install。

用法：
  python koc_dedup_check.py ./notes            # 扫描目录下所有 .md/.txt
  python koc_dedup_check.py ./notes --th 0.55  # 自定义相似度告警阈值
  python koc_dedup_check.py ./notes --json     # 输出 JSON（三级兜底写盘）

退出码：
  0  成功（结论：可发布 / 需调整）
  1  输入异常（未找到文案文件）

JSON 输出（--json 开关，不给则只打印报告不写盘）：
  三级兜底写盘，优先级 --out 指定 > 当前工作目录 > /tmp
  写盘后向 stdout 输出协议行 `KOC_DEDUP_JSON_FILE=<绝对路径>` 供 agent 解析。

文案文件格式（.md 或 .txt，UTF-8）：
  可选在文件头写元信息，用于排期与标签检测：
      ---
      koc: 熬夜产品经理小林
      date: 2026-08-15
      ---
      标题：白是白了，但我脸怎么松了？
      正文第一行...
      正文第二行...
      #珀莱雅蕴白 #熬夜肌自救 #提亮暗沉
"""

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from itertools import combinations
from math import sqrt

# ---------------------------------------------------------------- 词库配置

# 广告法极限词 —— 分两级处理
#
# 【硬极限词】任何上下文都违规，不接受豁免
BANNED_ABSOLUTE_HARD = [
    "最有效", "最强", "最便宜", "最顶级", "顶级", "顶尖", "极致",
    "百分百", "100%", "全网最", "国家级", "世界级", "独一无二",
    "永久", "永远有效", "无效退款", "保证有效", "彻底解决", "一劳永逸",
    "史无前例", "前所未有", "销量第一", "排名第一", "第一品牌", "第一名",
]

# 【软极限词】存在合法日常用法，须看上下文。
#   key   = 触发词
#   value = 豁免短语列表（命中任一即视为日常用法，降级为提示）
#           空列表 = 无任何豁免，等同硬违规
BANNED_ABSOLUTE_SOFT = {
    "第一": ["第一件", "第一次", "第一天", "第一步", "第一遍", "第一瓶", "第一个",
             "第一年", "第一周", "第一层", "第一时间", "第一反应", "第一眼", "第一条"],
    "最好": ["最好先", "最好别", "最好不要", "最好是", "最好在", "最好等",
             "得最好", "的最好", "最好能"],
    "最佳": ["最佳时间", "最佳时机", "最佳状态"],
    "唯一": [],      # 描述产品差异时几乎必然被判绝对化，一律拦截
    "绝对": ["绝对不", "绝对没", "绝对别"],
}

# 医疗化 / 超出化妆品功效范围（美妆个护品类高危）
BANNED_MEDICAL = [
    "根治", "治疗", "治愈", "药效", "特效", "医美级", "替代医美", "换肤",
    "祛斑", "去斑", "消除色斑", "抗炎", "消炎", "修复屏障损伤", "细胞再生",
    "抑制黑色素生成"  # 属机理宣称，需谨慎，标为告警
]

# 「永不豁免」词——本身即构成违规功效宣称，任何上下文都拦截
NEVER_EXEMPT = {
    "医美级", "替代医美", "根治", "治愈", "药效", "特效",
    "祛斑", "去斑", "消除色斑", "抑制黑色素生成",
    "修复屏障损伤", "细胞再生",
}

# 医疗词上下文豁免：描述就医经历 ≠ 宣称产品功效
# 例「做治疗的医生说…」是陈述事实，不构成化妆品功效宣称
# 注意：豁免词中不含「医美」，否则「医美级」会自我豁免
MEDICAL_CONTEXT_EXEMPT = [
    "医生", "医院", "术后", "主诊", "皮肤科", "面诊", "机构", "做完",
    "不能", "不可", "不是", "别拿", "无法", "并非", "不作", "别当",
]
EXEMPT_WINDOW = 12  # 前后各检查 N 个字符

# 站外导流
BANNED_DIVERT = ["加微信", "微信号", "vx", "V❤", "私我", "加v", "扣扣", "QQ", "淘宝搜", "外链"]

# 诱导互动（评论区绑定数据）
BANNED_INDUCE = ["点赞收藏私我", "关注抽奖", "转发得", "评论送"]

# 应主动声明但常被漏标
NEED_DECLARE = ["AI生成", "AI绘制", "剧情", "演绎", "情景再现"]

# 需在文中出现的合规标记（报备笔记）
REQUIRED_TAGS = ["#广告", "#品牌合作", "#合作"]


# ---------------------------------------------------------------- 文本处理

def normalize(text: str) -> str:
    """归一化：去空白、去标点、统一大小写，保留中英数字。"""
    text = text.lower()
    return re.sub(r"[^\u4e00-\u9fa5a-z0-9]", "", text)


def skeleton(text: str) -> str:
    """提取句式骨架：数字→#、连续英文→@，用于识别'只改数字'的模板化标题。"""
    t = normalize(text)
    t = re.sub(r"\d+", "#", t)
    t = re.sub(r"[a-z]+", "@", t)
    return t


def char_ngrams(text: str, n: int = 2):
    s = normalize(text)
    if len(s) < n:
        return set([s]) if s else set()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def sent_lengths(text: str) -> list:
    """句长序列——内容的『结构骨架』。
    伪原创能改词，改不掉段落节奏，这是识别模板化笔记最强的信号。"""
    parts = re.split(r"[\n。！？!?]", text)
    return [len(normalize(p)) for p in parts if len(normalize(p)) >= 4]


def struct_similarity(a: str, b: str) -> float:
    """结构指纹相似度：句子数接近 + 逐句长度吻合 → 判定为同一模板产出。"""
    la, lb = sent_lengths(a), sent_lengths(b)
    if not la or not lb:
        return 0.0
    # 句子数量差异惩罚
    cnt_sim = min(len(la), len(lb)) / max(len(la), len(lb))
    # 逐句长度吻合度（按较短的对齐）
    n = min(len(la), len(lb))
    diffs = []
    for i in range(n):
        m = max(la[i], lb[i]) or 1
        diffs.append(1 - abs(la[i] - lb[i]) / m)
    len_sim = sum(diffs) / n if diffs else 0.0
    return cnt_sim * len_sim


def freq_similarity(a: str, b: str, k: int = 40) -> float:
    """高频字集合重合——反映用词习惯与话题聚集度。"""
    ta = {w for w, _ in Counter(normalize(a)).most_common(k)}
    tb = {w for w, _ in Counter(normalize(b)).most_common(k)}
    return jaccard(ta, tb)


def tfidf_cosine(docs_tokens, i, j, idf):
    """基于字符 3-gram 的 TF-IDF 余弦相似度。"""
    a, b = docs_tokens[i], docs_tokens[j]
    if not a or not b:
        return 0.0
    va = {g: (c / len(a)) * idf.get(g, 0.0) for g, c in Counter(a).items()}
    vb = {g: (c / len(b)) * idf.get(g, 0.0) for g, c in Counter(b).items()}
    common = set(va) & set(vb)
    num = sum(va[g] * vb[g] for g in common)
    na = sqrt(sum(v * v for v in va.values()))
    nb = sqrt(sum(v * v for v in vb.values()))
    return num / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------- 解析

def parse_note(path: str) -> dict:
    raw = open(path, encoding="utf-8", errors="ignore").read()

    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", raw, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        raw = raw[m.end():]

    tags = re.findall(r"#([^\s#，,。]+)", raw)
    body = re.sub(r"#[^\s#，,。]+", "", raw).strip()

    lines = [l.strip() for l in body.splitlines() if l.strip()]
    title = ""
    if lines:
        title = re.sub(r"^(标题|title)[:：]\s*", "", lines[0], flags=re.I)
        if title != lines[0]:
            lines = lines[1:]
        else:
            title = lines[0]
    content = "\n".join(lines)

    return {
        "file": os.path.basename(path),
        "koc": meta.get("koc", os.path.splitext(os.path.basename(path))[0]),
        "date": meta.get("date", ""),
        "title": title,
        "content": content,
        "tags": tags,
        "raw": raw,
        "length": len(normalize(content)),
        # meta 中写 `报备: 蒲公英` / `报备: 已报备` 即视为已走平台商单流程
        # （蒲公英报备后平台自动挂"赞助"标识，博主无需自行加 #广告）
        "declared": bool(meta.get("报备") or meta.get("declared")),
    }


# ---------------------------------------------------------------- 检测

def _is_exempt(raw: str, word: str) -> bool:
    """医疗词上下文豁免判断：窗口内出现就医语境词则不算功效宣称。"""
    if word in NEVER_EXEMPT:
        return False  # 硬违规词，不接受任何上下文豁免
    for m in re.finditer(re.escape(word), raw):
        lo = max(0, m.start() - EXEMPT_WINDOW)
        hi = min(len(raw), m.end() + EXEMPT_WINDOW)
        window = raw[lo:hi]
        if not any(e in window for e in MEDICAL_CONTEXT_EXEMPT):
            return False  # 存在一处无豁免语境 → 仍需拦截
    return True


def _soft_absolute_hits(raw: str, word: str, exempts: list) -> list:
    """软极限词上下文判断。返回所有『未被豁免』的出现片段；空列表 = 全部为日常用法。"""
    bad = []
    for m in re.finditer(re.escape(word), raw):
        lo = max(0, m.start() - 4)
        hi = min(len(raw), m.end() + 6)
        window = raw[lo:hi]
        if not any(e in window for e in exempts):
            bad.append(window.replace("\n", ""))
    return bad


def scan_compliance(note: dict) -> list:
    issues = []
    raw = note["raw"]
    raw_low = raw.lower()

    for w in BANNED_ABSOLUTE_HARD:
        if w.lower() in raw_low:
            issues.append(("P0", f"极限词/绝对化用语「{w}」——违反广告法，发布即限流"))
    for w, exempts in BANNED_ABSOLUTE_SOFT.items():
        if w in raw:
            hits = _soft_absolute_hits(raw, w, exempts)
            if hits:
                issues.append(("P0", f"极限词/绝对化用语「{w}」——违反广告法（如：…{hits[0]}…）"))
            else:
                issues.append(("P2", f"出现「{w}」，但均为日常/序数用法（非绝对化宣称）——可放行"))
    for w in BANNED_MEDICAL:
        if w.lower() in raw_low:
            if _is_exempt(raw, w):
                issues.append(("P2", f"出现医疗相关词「{w}」，但处于就医语境（非功效宣称）——建议人工复核"))
            else:
                issues.append(("P0", f"医疗化/超范围功效词「{w}」——化妆品不得宣称"))
    for w in BANNED_DIVERT:
        if w.lower() in raw_low:
            issues.append(("P0", f"站外导流嫌疑「{w}」——重度违规，可致封号"))
    for w in BANNED_INDUCE:
        if w in note["raw"]:
            issues.append(("P1", f"诱导互动话术「{w}」——评论区数据绑定违规"))
    for w in NEED_DECLARE:
        if w in note["raw"]:
            issues.append(("P1", f"出现「{w}」——须在发布设置中勾选内容类型声明"))

    if not any(t in note["raw"] for t in REQUIRED_TAGS):
        if note.get("declared"):
            issues.append(("P2", "已声明走蒲公英报备（平台自动挂赞助标识）——发布时须核对后台已关联品牌"))
        else:
            issues.append(("P1", "未见 #广告/#品牌合作 标记——商业笔记须蒲公英报备并公开标注"))

    if note["length"] < 400:
        issues.append(("P2", f"正文仅 {note['length']} 字——CES 3.0 图文信息密度要求 ≥400 字，低于阈值影响初始推荐"))

    if len(note["tags"]) > 5:
        issues.append(("P2", f"话题标签 {len(note['tags'])} 个——建议 ≤5 个且强相关"))

    return issues


def main():
    ap = argparse.ArgumentParser(description="KOC 批量笔记同质化与合规发布前自检")
    ap.add_argument("path", help="文案目录（含 .md / .txt）")
    ap.add_argument("--th", type=float, default=0.50, help="正文相似度告警阈值，默认 0.50")
    ap.add_argument("--th-title", type=float, default=0.60, help="标题骨架相似度阈值，默认 0.60")
    ap.add_argument("--th-tag", type=float, default=0.60, help="标签组合重复率阈值，默认 0.60")
    ap.add_argument("--json", action="store_true", help="输出 JSON 结果（三级兜底写盘 + stdout 协议行）")
    ap.add_argument("--out", help="JSON 输出路径；不给则兜底写当前目录或 /tmp")
    args = ap.parse_args()

    files = []
    for root, _, names in os.walk(args.path):
        for n in sorted(names):
            if n.lower().endswith((".md", ".txt")):
                files.append(os.path.join(root, n))

    if len(files) < 1:
        print(f"[!] 在 {args.path} 未找到 .md/.txt 文案文件")
        sys.exit(1)

    notes = [parse_note(f) for f in files]
    print("=" * 68)
    print(f"  KOC 批量笔记自检报告   共 {len(notes)} 篇")
    print("=" * 68)

    # ---------- 1. 合规扫描 ----------
    print("\n【一】合规红线扫描")
    total_p0 = 0
    for nt in notes:
        issues = scan_compliance(nt)
        p0 = [i for i in issues if i[0] == "P0"]
        total_p0 += len(p0)
        if issues:
            print(f"\n  ● {nt['koc']}  ({nt['file']})")
            for lv, msg in sorted(issues):
                icon = {"P0": "[X] 阻断", "P1": "[!] 警告", "P2": "[i] 提示"}[lv]
                print(f"      {icon}  {msg}")
        else:
            print(f"\n  ● {nt['koc']}  ({nt['file']})\n      [OK] 无风险项")

    # ---------- 2. 相似度矩阵（三信号融合） ----------
    N = len(notes)
    grams = [list(char_ngrams(n["content"], 2)) for n in notes]
    df = Counter()
    for g in grams:
        for t in set(g):
            df[t] += 1
    from math import log
    idf = {t: log((N + 1) / (c + 1)) + 1 for t, c in df.items()}

    print("\n" + "=" * 68)
    print("【二】正文相似度检测（词汇 × 结构 × 用词习惯 三信号融合）")
    print("=" * 68)
    print("  说明：平台用语义向量模型比对，同义词替换无效。本检测以")
    print("        『结构指纹』为核心信号——伪原创能改词，改不掉段落骨架。\n")
    alerts = []
    struct_alerts = []
    for i, j in combinations(range(N), 2):
        lex = max(jaccard(set(grams[i]), set(grams[j])),
                  tfidf_cosine(grams, i, j, idf))
        st = struct_similarity(notes[i]["content"], notes[j]["content"])
        fq = freq_similarity(notes[i]["content"], notes[j]["content"])
        score = 0.5 * lex + 0.3 * st + 0.2 * fq
        if score >= args.th:
            alerts.append((score, lex, st, fq, notes[i], notes[j]))
        # 独立的模板化告警：即便用词差异大，骨架吻合即视为同模板产出
        elif st >= 0.85 and lex >= 0.15:
            struct_alerts.append((st, lex, notes[i], notes[j]))

    if alerts:
        for score, lex, st, fq, a, b in sorted(alerts, reverse=True, key=lambda x: x[0]):
            print(f"  [X] 综合相似度 {score:.0%}   (词汇 {lex:.0%} / 结构 {st:.0%} / 用词 {fq:.0%})")
            print(f"      {a['koc']}  ×  {b['koc']}")
            if st >= 0.8:
                print(f"      → 判定：同一模板产出的伪原创。改写词句无效，必须更换")
                print(f"        【人群身份】或【触发场景】，让内容从源头长出不同的骨架。")
            else:
                print(f"      → 建议：更换其中一篇的落点卖点与叙事结构")
            print()
    else:
        print(f"  [OK] 全部两两组合综合相似度均低于 {args.th:.0%}\n")

    if struct_alerts:
        print("  ── 模板化结构专项告警 ──")
        for st, lex, a, b in sorted(struct_alerts, reverse=True, key=lambda x: x[0]):
            print(f"  [!] 结构吻合 {st:.0%}（词汇仅 {lex:.0%}）：{a['koc']} × {b['koc']}")
            print(f"      → 用词已差异化但段落节奏雷同，仍可能被『模板化笔记识别模型』捕获")
        print()

    # ---------- 3. 标题骨架 ----------
    print("\n" + "=" * 68)
    print("【三】标题句式骨架检测（识别「只改数字/产品名」的模板化标题）")
    print("=" * 68)
    t_alerts = []
    for i, j in combinations(range(N), 2):
        s = jaccard(char_ngrams(skeleton(notes[i]["title"]), 2),
                    char_ngrams(skeleton(notes[j]["title"]), 2))
        if s >= args.th_title:
            t_alerts.append((s, notes[i], notes[j]))
    if t_alerts:
        for s, a, b in sorted(t_alerts, reverse=True, key=lambda x: x[0]):
            print(f"\n  [X] 骨架相似 {s:.0%}")
            print(f"      「{a['title']}」")
            print(f"      「{b['title']}」")
            print(f"      → 建议：改变叙事结构（疑问开场 / 结论前置 / 场景白描 / 自嘲）")
    else:
        print(f"\n  [OK] 标题句式无雷同")

    # ---------- 4. 标签组合 ----------
    print("\n" + "=" * 68)
    print("【四】话题标签组合重复率")
    print("=" * 68)
    g_alerts = []
    for i, j in combinations(range(N), 2):
        s = jaccard(set(notes[i]["tags"]), set(notes[j]["tags"]))
        if s >= args.th_tag:
            g_alerts.append((s, notes[i], notes[j]))
    if g_alerts:
        for s, a, b in sorted(g_alerts, reverse=True, key=lambda x: x[0]):
            print(f"\n  [X] 标签重合 {s:.0%}：{a['koc']} × {b['koc']}")
            print(f"      {a['tags']}")
            print(f"      {b['tags']}")
            print(f"      → 建议：主话题保持统一，次/辅助话题必须按人群差异化")
    else:
        print(f"\n  [OK] 标签组合已充分差异化")

    # ---------- 5. 开头句 ----------
    print("\n" + "=" * 68)
    print("【五】开头 20 字雷同检测")
    print("=" * 68)
    o_alerts = []
    for i, j in combinations(range(N), 2):
        s = jaccard(char_ngrams(notes[i]["content"][:20], 2),
                    char_ngrams(notes[j]["content"][:20], 2))
        if s >= 0.5:
            o_alerts.append((s, notes[i], notes[j]))
    if o_alerts:
        for s, a, b in sorted(o_alerts, reverse=True, key=lambda x: x[0]):
            print(f"\n  [X] 开头相似 {s:.0%}：{a['koc']} × {b['koc']}")
    else:
        print("\n  [OK] 开头句式各不相同")

    # ---------- 6. 发布节奏 ----------
    print("\n" + "=" * 68)
    print("【六】发布节奏检测（规避「生态哨兵」时间窗内同质浓度告警）")
    print("=" * 68)
    by_date = defaultdict(list)
    for nt in notes:
        if nt["date"]:
            by_date[nt["date"]].append(nt["koc"])
    if not by_date:
        print("\n  [i] 文案未标注 date 字段，跳过节奏检测")
    else:
        ok = True
        for d in sorted(by_date):
            cnt = len(by_date[d])
            flag = "[X] 超限" if cnt > 3 else "[OK]"
            if cnt > 3:
                ok = False
            print(f"  {flag}  {d}   {cnt} 篇   {', '.join(by_date[d])}")
        if not ok:
            print("\n  → 建议：同一品牌单日笔记 ≤3 篇，分批投放，批次间隔 3-5 天")

    # ---------- 总结 ----------
    print("\n" + "=" * 68)
    risk = "不可发布" if total_p0 else ("需调整" if (alerts or t_alerts or g_alerts) else "可发布")
    print(f"  结论：{risk}    P0 阻断项 {total_p0} 个 | 正文相似告警 {len(alerts)} 对 | "
          f"标题雷同 {len(t_alerts)} 对 | 标签重合 {len(g_alerts)} 对")
    print("=" * 68)

    if args.json:
        out = {
            "total": N,
            "verdict": risk,
            "p0_count": total_p0,
            "content_alerts": [
                {"score": round(s, 4), "a": a["koc"], "b": b["koc"]} for s, _, _, _, a, b in alerts
            ],
            "title_alerts": [{"score": round(s, 4), "a": a["koc"], "b": b["koc"]} for s, a, b in t_alerts],
            "tag_alerts": [{"score": round(s, 4), "a": a["koc"], "b": b["koc"]} for s, a, b in g_alerts],
            "notes": [
                {"koc": n["koc"], "file": n["file"], "length": n["length"],
                 "tags": n["tags"], "issues": [list(i) for i in scan_compliance(n)]}
                for n in notes
            ],
        }
        # 三级兜底写盘：--out 指定 > 当前工作目录 > /tmp
        target = args.out or os.path.join(os.getcwd(), "koc_dedup_check.json")
        written = False
        for cand in (target,
                     os.path.join("/tmp", "koc_dedup_check.json")):
            try:
                with open(cand, "w", encoding="utf-8") as fh:
                    json.dump(out, fh, ensure_ascii=False, indent=2)
                json_path = os.path.abspath(cand)
                written = True
                break
            except OSError:
                continue
        if written:
            print(f"\n[i] JSON 结果已写入 {json_path}")
            print(f"KOC_DEDUP_JSON_FILE={json_path}")
        else:
            print("\n[!] JSON 写盘失败（所有兜底路径均不可写）")


if __name__ == "__main__":
    main()
