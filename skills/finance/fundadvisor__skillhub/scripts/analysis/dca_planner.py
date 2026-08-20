#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定投规划器 (v7.1 新增)

投顾高频场景："每月定投 X 元，怎么配 / 到期能有多少 / 何时止盈"。
纯标准库、离线可跑，复用 asset_allocator 的 SAA/下滑曲线。

输出三部分：
1. 月定投金额的资产类别拆分（含核心-卫星建议）
2. 到期测算：累计投入 vs 悲观/中性/乐观三档终值（基于风险等级假设收益/波动，
   属情景假设而非预测，输出中如实标注）
3. 定投纪律建议（止盈目标/扣款节奏/检视频率）
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from analysis.asset_allocator import (  # noqa: E402
    score_risk_questionnaire, saa_for_profile, glide_path, core_satellite,
    RISK_LEVEL_DESC,
)

# 各风险等级假设年化收益/年化波动（长期历史经验的粗略中枢，仅作情景假设）
ASSUMPTIONS = {
    "保守型": {"mu": 0.030, "sigma": 0.03},
    "稳健型": {"mu": 0.040, "sigma": 0.06},
    "平衡型": {"mu": 0.060, "sigma": 0.12},
    "成长型": {"mu": 0.080, "sigma": 0.18},
    "进取型": {"mu": 0.095, "sigma": 0.22},
}

# 各风险等级建议止盈目标（累计收益率）与检视频率
PROFIT_TARGET = {"保守型": 0.10, "稳健型": 0.15, "平衡型": 0.25, "成长型": 0.30, "进取型": 0.40}
REVIEW_FREQ = {"保守型": "每半年", "稳健型": "每季度", "平衡型": "每季度", "成长型": "每月", "进取型": "每月"}


def _fv_of_dca(monthly: float, annual_return: float, months: int) -> float:
    """月定投终值（月初扣款近似按月末复利，差异可忽略）"""
    if months <= 0:
        return 0.0
    r = (1 + annual_return) ** (1 / 12) - 1
    if abs(r) < 1e-9:
        return monthly * months
    return monthly * ((1 + r) ** months - 1) / r


def project_dca(monthly_amount: float, years: float, risk_level: str) -> Dict:
    """三档情景测算：悲观(mu-sigma) / 中性(mu) / 乐观(mu+sigma)。

    返回每年末的 累计投入/三档终值。悲观档年化下限封 -10%（长期定投
    再差也很少连续多年 -10% 以下，避免输出吓人的不合理数字）。
    """
    a = ASSUMPTIONS.get(risk_level, ASSUMPTIONS["平衡型"])
    months_total = max(1, int(round(years * 12)))
    r_low = max(a["mu"] - a["sigma"], -0.10)
    rows = []
    for m in range(12, months_total + 1, 12):
        rows.append({
            "year": m // 12,
            "invested": round(monthly_amount * m, 2),
            "pessimistic": round(_fv_of_dca(monthly_amount, r_low, m), 2),
            "expected": round(_fv_of_dca(monthly_amount, a["mu"], m), 2),
            "optimistic": round(_fv_of_dca(monthly_amount, a["mu"] + a["sigma"], m), 2),
        })
    return {
        "assumed_annual_return": a["mu"],
        "assumed_annual_vol": a["sigma"],
        "scenarios": rows,
        "note": "三档终值基于假设年化收益 %.1f%% ± %.1f%%，属情景假设而非收益承诺" % (a["mu"] * 100, a["sigma"] * 100),
    }


def plan_dca(monthly_amount: float,
             answers: Optional[List[int]] = None,
             risk_level: str = "",
             horizon_years: float = 3.0,
             goal: str = "") -> Dict:
    """一站式定投规划。

    参数:
        monthly_amount: 每月定投金额（元）
        answers: 10 题问卷（0-4 分），优先于 risk_level
        risk_level: 保守型/稳健型/平衡型/成长型/进取型
        horizon_years: 定投年限
        goal: 目标场景（养老/教育/购房/现金/其他，影响 SAA 与下滑曲线）
    """
    if monthly_amount <= 0:
        return {"error": "monthly_amount 必须为正"}
    if answers:
        profile = score_risk_questionnaire(answers)
        level = profile["risk_level"]
    else:
        profile = {"risk_level": risk_level or "平衡型"}
        level = profile["risk_level"]
    if level not in ASSUMPTIONS:
        return {"error": f"无法识别风险等级: {level}"}

    saa = saa_for_profile(level, horizon_years, goal)
    split = {k: {"pct": v, "monthly": round(monthly_amount * v / 100, 2)}
             for k, v in saa.items() if v > 0}

    cs = core_satellite(monthly_amount, level)
    glide = glide_path(goal, int(horizon_years), level) if goal in ("养老", "教育") else None
    projection = project_dca(monthly_amount, horizon_years, level)

    target = PROFIT_TARGET[level]
    advice = [
        f"按{level}基准，每月 {monthly_amount:.0f} 元拆分为 {len(split)} 类资产；"
        f"核心仓（宽基/纯债/货基）约 {cs['core']['amount']:.0f} 元/月，卫星仓 ≤ {cs['satellite']['amount']:.0f} 元/月",
        f"建议止盈目标：组合累计收益达 {target:.0%} 时分批止盈（参考§3.3 阈值再平衡），"
        f"止盈后不清仓定投计划，仅锁定部分收益",
        f"检视频率：{REVIEW_FREQ[level]}一次即可，避免因短期波动中断定投",
    ]
    if goal in ("养老", "教育") and glide:
        advice.append(f"{goal}场景：权益占比按下滑曲线逐年下调（首年 {glide[0]['equity_pct']}% → "
                      f"末年 {glide[-1]['equity_pct']}%），到期前 1-2 年逐步转入货基/短债锁定")

    return {
        "monthly_amount": monthly_amount,
        "risk_profile": profile,
        "risk_level": level,
        "level_desc": RISK_LEVEL_DESC.get(level, ""),
        "horizon_years": horizon_years,
        "goal": goal or "未指定",
        "monthly_split": split,
        "core_satellite": cs,
        "glide_path": glide,
        "projection": projection,
        "advice": advice,
        "disclaimer": "定投测算为情景假设，不构成收益承诺或投资建议；基金有风险，投资需谨慎",
    }


def format_dca_plan(plan: Dict) -> str:
    """定投规划的可读文本输出"""
    if "error" in plan:
        return f"⚠️ {plan['error']}"
    L = [f"【定投规划】每月 {plan['monthly_amount']:.0f} 元 · {plan['risk_level']} · {plan['horizon_years']}年 · 目标:{plan['goal']}"]
    L.append("─" * 50)
    L.append("一、每月金额拆分")
    for k, v in plan["monthly_split"].items():
        L.append(f"  {k}: {v['monthly']:.0f} 元/月 ({v['pct']}%)")
    if plan.get("glide_path"):
        g = plan["glide_path"]
        L.append(f"  下滑曲线: 首年权益 {g[0]['equity_pct']}% → 末年 {g[-1]['equity_pct']}%")
    L.append("二、到期测算（情景假设）")
    L.append(f"  {'年末':<4}{'累计投入':>10}{'悲观':>10}{'中性':>10}{'乐观':>10}")
    for r in plan["projection"]["scenarios"]:
        L.append(f"  {r['year']:<4}{r['invested']:>10.0f}{r['pessimistic']:>10.0f}"
                 f"{r['expected']:>10.0f}{r['optimistic']:>10.0f}")
    L.append(f"  注: {plan['projection']['note']}")
    L.append("三、定投纪律")
    for a in plan["advice"]:
        L.append(f"  · {a}")
    L.append(plan["disclaimer"])
    return "\n".join(L)


if __name__ == "__main__":
    print(format_dca_plan(plan_dca(2000, risk_level="平衡型", horizon_years=5, goal="教育")))
