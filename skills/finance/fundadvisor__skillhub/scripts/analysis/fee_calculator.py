#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调仓成本测算器 (v7.1 新增)

调仓建议模板(§3.5)要求"考虑税务/费用影响"，本模块提供量化支撑：
- 赎回费阶梯（按持有天数，含 <7 天 1.5% 惩罚性费率——监管强制）
- 申购费（默认 1 折，互联网平台常态）
- 换仓总成本 + 回本周期（新基金需多跑赢多少才值得换）

纯标准库、离线可跑；费率为行业常见默认，具体基金以公告为准
（fund_products.json 含申购/赎回费字段时可按基金覆盖默认值）。
"""
from __future__ import annotations

from typing import Dict, List, Optional

# 赎回费阶梯: (持有天数上限, 费率)，超过最后一个上限按 0 计
DEFAULT_TIERS = {
    "股票型": [(7, 0.015), (30, 0.0075), (365, 0.005), (730, 0.0025)],
    "混合型": [(7, 0.015), (30, 0.0075), (365, 0.005), (730, 0.0025)],
    "指数型": [(7, 0.015), (30, 0.0075), (365, 0.005), (730, 0.0025)],
    "债券型": [(7, 0.015), (30, 0.001)],
    "货币型": [],
}

# 申购费默认值: 原费率 / 折扣（互联网平台 1 折为主流）
DEFAULT_SUBSCRIBE = {"rate": 0.015, "discount": 0.1}


def redemption_fee(amount: float, holding_days: int,
                   fund_type: str = "混合型",
                   tiers: Optional[List] = None) -> Dict:
    """赎回费测算。

    参数:
        amount: 赎回金额（元）
        holding_days: 持有天数
        fund_type: 股票型/混合型/指数型/债券型/货币型（决定默认阶梯）
        tiers: 自定义阶梯 [(天数上限, 费率), ...]，优先级高于 fund_type
    """
    if amount <= 0:
        return {"error": "amount 必须为正"}
    ladder = tiers if tiers is not None else DEFAULT_TIERS.get(fund_type, DEFAULT_TIERS["混合型"])
    rate = 0.0
    for cap, r in ladder:
        if holding_days < cap:
            rate = r
            break
    fee = round(amount * rate, 2)
    return {
        "amount": amount,
        "holding_days": holding_days,
        "fund_type": fund_type,
        "rate": rate,
        "fee": fee,
        "punitive": rate >= 0.015,
    }


def subscription_fee(amount: float, rate: float = None, discount: float = None) -> Dict:
    """申购费测算（默认 1.5% 原费率、1 折）"""
    if amount <= 0:
        return {"error": "amount 必须为正"}
    rate = DEFAULT_SUBSCRIBE["rate"] if rate is None else rate
    discount = DEFAULT_SUBSCRIBE["discount"] if discount is None else discount
    effective = rate * discount
    return {
        "amount": amount,
        "original_rate": rate,
        "discount": discount,
        "effective_rate": effective,
        "fee": round(amount * effective, 2),
    }


def estimate_rebalance_cost(sells: List[Dict], buys: List[Dict]) -> Dict:
    """换仓总成本测算。

    参数:
        sells: [{"name":..., "amount":..., "holding_days":..., "fund_type":可选, "tiers":可选}]
        buys:  [{"name":..., "amount":..., "rate":可选, "discount":可选}]

    返回总成本、成本占比、逐只明细与执行建议（如"持有<30天建议等待"）。
    """
    sell_total = buy_total = 0.0
    sell_fee = buy_fee = 0.0
    details = []
    advice = []
    for s in sells:
        r = redemption_fee(s.get("amount", 0), int(s.get("holding_days", 0)),
                           s.get("fund_type", "混合型"), s.get("tiers"))
        if "error" in r:
            return r
        sell_total += r["amount"]
        sell_fee += r["fee"]
        details.append({"side": "卖出", "name": s.get("name", ""), **r})
        if r["punitive"]:
            advice.append(f"⚠️ {s.get('name','该基金')}持有仅 {r['holding_days']} 天，赎回费 {r['rate']:.1%} "
                          f"属惩罚性费率，强烈建议持有满 7 天后再操作")
        elif r["rate"] >= 0.005 and r["holding_days"] < 365:
            advice.append(f"{s.get('name','该基金')}持有 {r['holding_days']} 天赎回费 {r['rate']:.2%}，"
                          f"若不急可持有满 1 年降至 0.25% 档")
    for b in buys:
        r = subscription_fee(b.get("amount", 0), b.get("rate"), b.get("discount"))
        if "error" in r:
            return r
        buy_total += r["amount"]
        buy_fee += r["fee"]
        details.append({"side": "买入", "name": b.get("name", ""), **r})

    total_fee = round(sell_fee + buy_fee, 2)
    base = max(sell_total, buy_total, 1.0)
    cost_pct = round(total_fee / base * 100, 3)
    return {
        "sell_amount": round(sell_total, 2),
        "buy_amount": round(buy_total, 2),
        "sell_fee": round(sell_fee, 2),
        "buy_fee": round(buy_fee, 2),
        "total_fee": total_fee,
        "cost_pct": cost_pct,
        "details": details,
        "advice": advice or ["费率成本在合理范围，可按计划调仓"],
        "note": "费率为行业常见默认值，具体基金以基金公司公告为准",
    }


def breakeven_months(cost_pct: float, annual_excess_return: float) -> Dict:
    """换仓回本周期：新基金年化超额收益需多久覆盖换仓成本。

    参数:
        cost_pct: 换仓成本占本金 %（estimate_rebalance_cost 的输出）
        annual_excess_return: 新基金相对旧基金的预期年化超额收益 %
    返回回本所需月数；超额<=0 时明示"永远回不了本"。
    """
    if annual_excess_return <= 0:
        return {"breakeven_months": None,
                "verdict": "新基金预期超额收益≤0，换仓成本无法回收，不建议仅因短期业绩换仓"}
    months = cost_pct / annual_excess_return * 12
    verdict = ("回本周期约 %.1f 个月，" % months) + (
        "成本可接受" if months <= 6 else ("回本偏慢，建议分批换仓摊薄" if months <= 12 else "回本周期过长，换仓性价比低"))
    return {"breakeven_months": round(months, 1), "verdict": verdict}


if __name__ == "__main__":
    demo = estimate_rebalance_cost(
        sells=[{"name": "A基金", "amount": 50000, "holding_days": 200},
               {"name": "B基金", "amount": 30000, "holding_days": 5}],
        buys=[{"name": "C基金", "amount": 80000}],
    )
    import json
    print(json.dumps(demo, ensure_ascii=False, indent=2))
    print(breakeven_months(demo["cost_pct"], 3.0)["verdict"])
