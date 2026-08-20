#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""组合配置引擎 (v7.0 新增)

投前资产配置能力（纯标准库、离线可跑）：
- 风险问卷评分（10 题 -> 五轴 -> 五档风险等级）
- 战略资产配置 SAA（按风险等级 + 期限 + 目标场景微调）
- 目标日期下滑曲线（养老/教育等长期目标）
- 核心-卫星拆分
- 风险平价 / 均值方差（小矩阵纯 Python 近似）
- 适当性校验（客户风险等级 vs 基金风险等级）
- build_allocation_plan 一站式配置方案

风险等级：保守型 / 稳健型 / 平衡型 / 成长型 / 进取型
"""
from __future__ import annotations

import sys
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))


# ─── 常量表 ───────────────────────────────────────────────
RISK_LEVELS = ["保守型", "稳健型", "平衡型", "成长型", "进取型"]

RISK_LEVEL_DESC = {
    "保守型": "本金安全优先，只能接受很小波动，收益目标跑赢通胀即可",
    "稳健型": "偏好低波动，接受小幅亏损以换取稳健增值",
    "平衡型": "风险与收益并重，能接受中等波动与阶段性回撤",
    "成长型": "追求长期较高收益，能承受较大波动与回撤",
    "进取型": "追求最大化长期收益，能承受大幅波动甚至阶段性深亏",
}

# 战略资产配置基准表（%，键：资产类别）
SAA_BASE = {
    "保守型": {"货基/短债": 40, "纯债": 35, "固收+": 15, "混合": 5,  "股基": 5,  "海外/另类": 0},
    "稳健型": {"货基/短债": 15, "纯债": 30, "固收+": 25, "混合": 15, "股基": 10, "海外/另类": 5},
    "平衡型": {"货基/短债": 5,  "纯债": 15, "固收+": 20, "混合": 20, "股基": 30, "海外/另类": 10},
    "成长型": {"货基/短债": 0,  "纯债": 5,  "固收+": 10, "混合": 15, "股基": 55, "海外/另类": 15},
    "进取型": {"货基/短债": 0,  "纯债": 0,  "固收+": 5,  "混合": 10, "股基": 65, "海外/另类": 20},
}

# 五轴定义：每轴由 2 题组成（题号 1-based），每题 0-4 分，每轴 0-8 分
QUESTION_AXES = {
    "R1风险承受": [1, 2],
    "R2投资期限": [3, 4],
    "R3收益预期": [5, 6],
    "R4流动性需求": [7, 8],
    "R5投资经验": [9, 10],
}

# 各风险等级股基基准占比（下滑曲线起点用）
EQUITY_BASE = {"保守型": 5, "稳健型": 10, "平衡型": 30, "成长型": 55, "进取型": 65}

# 核心-卫星：各等级卫星占比上限
SATELLITE_CAP = {"保守型": 0.20, "稳健型": 0.25, "平衡型": 0.30, "成长型": 0.35, "进取型": 0.40}

CORE_TYPES = ["宽基指数基金(沪深300/中证500/中证A500)", "纯债基金", "同业存单/短债基金", "货币基金"]
SATELLITE_TYPES = ["行业主题基金(消费/医药/科技等)", "主动权益基金", "QDII/海外基金", "黄金/商品基金", "REITs"]

# 适当性映射：客户等级 -> 可承受最高基金风险档(1-5)
_CLIENT_RISK_MAP = {"保守型": 1, "稳健型": 2, "平衡型": 3, "成长型": 4, "进取型": 5,
                    "C1": 1, "C2": 2, "C3": 3, "C4": 4, "C5": 5}
_FUND_RISK_MAP = {"R1": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5,
                  "低": 1, "中低": 2, "中": 3, "中高": 4, "高": 5,
                  "低风险": 1, "中低风险": 2, "中风险": 3, "中高风险": 4, "高风险": 5}
_FUND_RISK_LABEL = {1: "R1(低)", 2: "R2(中低)", 3: "R3(中)", 4: "R4(中高)", 5: "R5(高)"}


# ─── 1. 风险问卷评分 ──────────────────────────────────────
def score_risk_questionnaire(answers: List[int]) -> Dict:
    """10 题风险问卷 -> 五轴得分 + 风险等级

    参数:
        answers: 10 个整数，每题 0-4 分（0=最保守，4=最激进）
    映射规则（docstring 约定）:
        - 五轴各由 2 题组成（题1-2->R1风险承受, 3-4->R2期限, 5-6->R3预期,
          7-8->R4流动性, 9-10->R5经验），每轴 0-8 分
        - 原始总分 0-40，等比映射到 5-25 区间: mapped = 5 + raw/40*20 = 5 + raw/2
        - 等级阈值（mapped）：5-8 保守型 / 9-13 稳健型 / 14-18 平衡型 /
          19-22 成长型 / 23-25 进取型
        - 全 0 答案 -> mapped=5 -> 保守型；全 4 答案 -> mapped=25 -> 进取型
    返回:
        dict: axes(五轴得分) / raw_score / mapped_score / risk_level / level_desc
    """
    ans = [int(a) for a in (answers or [])]
    if len(ans) != 10:
        return {"error": f"问卷需 10 题答案，实际 {len(ans)} 题"}
    if any(a < 0 or a > 4 for a in ans):
        return {"error": "每题答案须在 0-4 之间"}
    axes = {}
    for axis, qs in QUESTION_AXES.items():
        axes[axis] = sum(ans[q - 1] for q in qs)  # 每轴 0-8
    raw = sum(ans)                       # 0-40
    mapped = 5 + raw / 2.0               # 等比映射到 5-25
    if mapped <= 8:
        level = "保守型"
    elif mapped <= 13:
        level = "稳健型"
    elif mapped <= 18:
        level = "平衡型"
    elif mapped <= 22:
        level = "成长型"
    else:
        level = "进取型"
    return {
        "axes": axes,
        "raw_score": raw,
        "mapped_score": round(mapped, 1),
        "risk_level": level,
        "level_desc": RISK_LEVEL_DESC[level],
    }


# ─── 2. 战略资产配置 SAA ─────────────────────────────────
def _normalize_100(alloc: Dict[str, float]) -> Dict[str, float]:
    """归一到和为 100（整数化并把舍入差补给最大项）"""
    clipped = {k: max(0.0, float(v)) for k, v in alloc.items()}
    total = sum(clipped.values())
    if total <= 0:
        return {k: 0 for k in alloc}
    scaled = {k: v / total * 100.0 for k, v in clipped.items()}
    ints = {k: int(round(v)) for k, v in scaled.items()}
    diff = 100 - sum(ints.values())
    if diff != 0:
        biggest = max(scaled, key=lambda k: scaled[k])
        ints[biggest] += diff
    return ints


def _shift(alloc: Dict[str, float], frm: List[str], to: str, pct: float) -> None:
    """从 frm 各类别按比例挪出 pct 个百分点到 to（就地修改，逐项扣减不为负）"""
    remain = pct
    for k in frm:
        take = min(alloc.get(k, 0.0), remain)
        alloc[k] = alloc.get(k, 0.0) - take
        remain -= take
        if remain <= 0:
            break
    alloc[to] = alloc.get(to, 0.0) + (pct - remain)


def saa_for_profile(risk_level: str, horizon_years: float = 3.0, goal: str = "") -> Dict:
    """战略资产配置（百分比，和为 100）

    参数:
        risk_level: 保守型/稳健型/平衡型/成长型/进取型
        horizon_years: 投资期限（年）；<1 年向货基/短债倾斜 +8，>10 年向股基倾斜 +8
        goal: 目标场景（养老/教育/购房/现金/其他）
            现金 -> 直接给 货基/短债80 + 纯债20
            养老 -> 海外/另类 +5（长期抗通胀）
            教育 -> 固收+ +5（稳健为先）
            购房 -> 货基/短债 +8（首付确定性）
    """
    if goal == "现金":
        return {"货基/短债": 80, "纯债": 20, "固收+": 0, "混合": 0, "股基": 0, "海外/另类": 0,
                "note": "现金管理场景：流动性与安全性优先"}
    base = dict(SAA_BASE.get(risk_level, SAA_BASE["平衡型"]))
    # 期限微调
    if horizon_years < 1:
        _shift(base, ["股基", "混合", "海外/另类"], "货基/短债", 8)
    elif horizon_years > 10:
        _shift(base, ["货基/短债", "纯债", "固收+"], "股基", 8)
    # 目标场景微调
    if goal == "养老":
        _shift(base, ["纯债", "货基/短债"], "海外/另类", 5)
    elif goal == "教育":
        _shift(base, ["股基", "混合"], "固收+", 5)
    elif goal == "购房":
        _shift(base, ["股基", "混合", "海外/另类"], "货基/短债", 8)
    return _normalize_100(base)


# ─── 3. 目标日期下滑曲线 ─────────────────────────────────
def glide_path(goal: str, years_to_target: int, risk_level: str) -> List[Dict]:
    """目标日期下滑曲线（股基占比逐年递减，最后 3 年加速降权益）

    分段线性：起点 = 风险等级股基基准，距目标 3 年时降到 25%，目标年降到 10%。
    返回: [{year: 第i年(0=现在), years_left, equity_pct(股基占比%)}]
    """
    years = max(1, int(years_to_target))
    start = EQUITY_BASE.get(risk_level, 30)
    mid, end = 25, 10
    anchor = max(0, years - 3)  # 距目标3年对应的"已过年份"
    path = []
    for i in range(years + 1):
        if i <= anchor and anchor > 0:
            pct = start - (start - mid) * (i / anchor)
        elif anchor == 0:
            # 总期限 <=3 年：直接从 min(start,25) 线性到 10
            pct = min(start, mid) - (min(start, mid) - end) * (i / years)
        else:
            pct = mid - (mid - end) * ((i - anchor) / max(1, years - anchor))
        path.append({"year": i, "years_left": years - i,
                     "equity_pct": round(max(end, pct), 1)})
    return path


def _fix_sum_one(w: List[float]) -> List[float]:
    """权重四舍五入到 6 位后，把舍入差补到最大权重项，保证和恰为 1"""
    if not w:
        return w
    r = [round(x, 6) for x in w]
    diff = round(1.0 - sum(r), 6)
    if diff != 0.0:
        i = max(range(len(r)), key=lambda k: r[k])
        r[i] = round(r[i] + diff, 6)
    return r


# ─── 4. 核心-卫星拆分 ────────────────────────────────────
def core_satellite(total: float, risk_level: str, core_ratio: float = 0.6) -> Dict:
    """核心-卫星策略拆分

    核心 = 宽基指数/债基（压舱石）；卫星 = 行业/主题/海外（增强收益）。
    卫星占比 = min(1-core_ratio, 该风险等级上限20%-40%)。
    """
    cap = SATELLITE_CAP.get(risk_level, 0.30)
    sat_ratio = min(max(0.0, 1.0 - core_ratio), cap)
    core_r = 1.0 - sat_ratio
    return {
        "core": {
            "ratio": round(core_r, 2),
            "amount": round(total * core_r, 2),
            "建议类型": CORE_TYPES,
        },
        "satellite": {
            "ratio": round(sat_ratio, 2),
            "amount": round(total * sat_ratio, 2),
            "建议类型": SATELLITE_TYPES,
            "cap_note": f"{risk_level}卫星上限{int(cap*100)}%",
        },
    }


# ─── 5. 组合优化（小矩阵纯 Python）─────────────────────────
def optimize_equal_risk(vols: List[float], corr: Optional[List[List[float]]] = None) -> List[float]:
    """风险平价权重

    corr 为 None 时退化为 1/sigma 归一；
    有 corr 时用简化迭代 ERC：每轮按"当前风险贡献 vs 平均风险贡献"反向调权，
    最多 100 轮，收敛到各资产风险贡献近似相等。矩阵规模 <=10。
    """
    n = len(vols or [])
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    sig = [max(1e-8, float(v)) for v in vols]
    if corr is None:
        inv = [1.0 / s for s in sig]
        tot = sum(inv)
        return _fix_sum_one([w / tot for w in inv])
    # 协方差矩阵 C = D corr D
    C = [[corr[i][j] * sig[i] * sig[j] for j in range(n)] for i in range(n)]
    w = [1.0 / n] * n
    for _ in range(100):
        Cw = [sum(C[i][j] * w[j] for j in range(n)) for i in range(n)]
        var_p = sum(w[i] * Cw[i] for i in range(n))
        if var_p <= 0:
            break
        rc = [w[i] * Cw[i] / math.sqrt(var_p) for i in range(n)]  # 各资产风险贡献
        avg = sum(rc) / n
        new_w = [w[i] * (avg / rc[i] if rc[i] > 1e-12 else 2.0) for i in range(n)]
        tot = sum(new_w)
        new_w = [x / tot for x in new_w]
        if max(abs(new_w[i] - w[i]) for i in range(n)) < 1e-8:
            w = new_w
            break
        w = new_w
    return _fix_sum_one(w)


def optimize_mean_variance(expected_returns: List[float],
                           cov: List[List[float]],
                           target_return: Optional[float] = None,
                           max_weight: float = 0.4) -> List[float]:
    """均值-方差近似优化（小矩阵 <=6，网格搜索）

    权重步长 5%，非负、和为 1、单资产不超过 max_weight。
    target_return 为 None 时最大化 收益-0.5×方差（风险厌恶系数=1）；
    否则在 收益>=target_return 约束下最小化方差；无可行解时退化为
    不超过 max_weight 约束下收益最大的组合。
    """
    n = len(expected_returns or [])
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    step = 0.05
    units = int(round(1.0 / step))          # 20 份
    cap_units = int(round(max_weight / step))

    def gen_weights(k: int, left: int, cap: int):
        """递归生成 k 个非负整数、和为 left、每项 <= cap 的组合"""
        if k == 1:
            if 0 <= left <= cap:
                yield [left]
            return
        for u in range(min(cap, left) + 1):
            for rest in gen_weights(k - 1, left - u, cap):
                yield [u] + rest

    def port_ret(w):
        return sum(w[i] * expected_returns[i] for i in range(n))

    def port_var(w):
        return sum(w[i] * w[j] * cov[i][j] for i in range(n) for j in range(n))

    best_w, best_key = None, None
    fallback_w, fallback_ret = None, None  # target 不可行时的退路
    for units_w in gen_weights(n, units, cap_units):
        w = [u * step for u in units_w]
        r, v = port_ret(w), port_var(w)
        if fallback_ret is None or r > fallback_ret:
            fallback_w, fallback_ret = w, r
        if target_return is not None and r < target_return - 1e-12:
            continue
        key = -v if target_return is not None else (r - 0.5 * v)
        if best_key is None or key > best_key:
            best_key, best_w = key, w
    chosen = best_w if best_w is not None else (fallback_w or [1.0 / n] * n)
    return _fix_sum_one(chosen)


# ─── 6. 适当性校验 ───────────────────────────────────────
def suitability_check(client_risk_level: str, fund_risk_level: str) -> Dict:
    """客户风险等级 vs 基金风险等级 适当性校验

    基金风险不低于客户承受档即匹配；不匹配返回 warning 文案。
    """
    c = _CLIENT_RISK_MAP.get((client_risk_level or "").strip())
    f = _FUND_RISK_MAP.get((fund_risk_level or "").strip())
    if c is None:
        return {"match": False, "warning": f"无法识别客户风险等级: {client_risk_level}"}
    if f is None:
        return {"match": False, "warning": f"无法识别基金风险等级: {fund_risk_level}"}
    if f <= c:
        return {"match": True, "client_level": client_risk_level,
                "fund_level": _FUND_RISK_LABEL[f], "warning": ""}
    return {
        "match": False,
        "client_level": client_risk_level,
        "fund_level": _FUND_RISK_LABEL[f],
        "warning": (f"⚠️ 适当性不匹配：客户为{client_risk_level}(C{c})，"
                    f"基金风险等级{_FUND_RISK_LABEL[f]}超出其承受能力，"
                    f"按监管要求不应向客户主动推介，请更换为 R{c} 及以下产品"),
    }


# ─── 7. 一站式配置方案 ───────────────────────────────────
# 每资产类别建议基金只数
_FUND_SLOTS = {"货基/短债": (1, 2), "纯债": (1, 2), "固收+": (1, 2),
               "混合": (1, 2), "股基": (2, 4), "海外/另类": (1, 2)}


def build_allocation_plan(amount: float,
                          answers: Optional[List[int]] = None,
                          risk_level: str = "",
                          horizon_years: float = 3.0,
                          goal: str = "",
                          funds: Optional[List[Dict]] = None) -> Dict:
    """一站式资产配置方案

    优先级：answers 问卷 > 显式 risk_level > 默认平衡型。
    返回 dict:
      risk_profile   问卷评分结果（无问卷时为等级说明）
      saa            战略配置（含各类别金额）
      glide_path     goal 为养老/教育时给出，否则为 None
      core_satellite 核心-卫星拆分
      fund_slots     每资产类别 {建议只数, 金额, 单只金额区间}
      suitability    funds 传入时逐只校验适当性
      rebalancing_rule 再平衡规则说明
      generated_at / disclaimer
    """
    if answers:
        profile = score_risk_questionnaire(answers)
        if "error" in profile:
            return profile
        level = profile["risk_level"]
    else:
        level = risk_level if risk_level in RISK_LEVELS else "平衡型"
        profile = {"risk_level": level, "level_desc": RISK_LEVEL_DESC[level],
                   "note": "未做问卷，使用显式/默认风险等级"}
    saa_pct = saa_for_profile(level, horizon_years, goal)
    saa = {k: {"pct": v, "amount": round(amount * v / 100.0, 2)}
           for k, v in saa_pct.items()}
    gp = glide_path(goal, int(horizon_years) if horizon_years >= 1 else 1, level) \
        if goal in ("养老", "教育") else None
    cs = core_satellite(amount, level)
    slots = {}
    for k, v in saa_pct.items():
        lo, hi = _FUND_SLOTS.get(k, (1, 2))
        amt = round(amount * v / 100.0, 2)
        n = hi if amt >= 50000 else lo  # 小额少买几只
        slots[k] = {"pct": v, "amount": amt, "建议只数": n if v > 0 else 0,
                    "单只金额": round(amt / n, 2) if (v > 0 and n > 0) else 0}
    suitability = []
    for f in (funds or []):
        fr = f.get("risk_level", "")
        if fr:
            chk = suitability_check(level, fr)
            chk["fund_code"] = f.get("code", "")
            chk["fund_name"] = f.get("name", "")
            suitability.append(chk)
    return {
        "amount": amount,
        "risk_profile": profile,
        "saa": saa,
        "glide_path": gp,
        "core_satellite": cs,
        "fund_slots": slots,
        "suitability": suitability,
        "rebalancing_rule": "偏离目标配置 ±5% 触发再平衡；每季度定期检视一次；"
                            "目标日期型组合按下滑曲线每年调整一次权益中枢",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "disclaimer": "⚠️ 本方案为量化模型输出的参考建议，不构成投资指令；"
                      "基金有风险，投资须谨慎，请结合自身情况独立决策。",
    }


if __name__ == "__main__":
    import json
    # 演示：平衡型 10 万养老规划
    plan = build_allocation_plan(100000, risk_level="平衡型", horizon_years=20, goal="养老")
    print(json.dumps(plan, ensure_ascii=False, indent=2)[:2000])
    print("\n问卷全0:", score_risk_questionnaire([0] * 10)["risk_level"])
    print("问卷全4:", score_risk_questionnaire([4] * 10)["risk_level"])
    print("风险平价:", optimize_equal_risk([0.2, 0.1, 0.05]))
