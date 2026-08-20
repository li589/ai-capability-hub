#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WACC / CAPM 折现率计算（v5.0 新增）

提供 DCF 估值所需的加权平均资本成本（WACC）。

组件:
- 无风险利率 Rf: 10 年期国债收益率（东财宏观数据中心，缓存 1 天）
- 股权风险溢价 ERP: A 股默认 6%（可配置，依据学术研究 + A 股历史风险溢价中位数）
- Beta: 个股日收益率 vs 沪深 300，OLS 估计，窗口 60 交易日
- 股权成本 Ke: CAPM = Rf + β × ERP
- 债务成本 Kd: 利息支出 / 有息负债 × (1 - 税率)
- WACC = E/V × Ke + D/V × Kd × (1 - T)

所有外部调用都带降级路径：beta 数据不足返回 1.0；无风险利率获取失败返回 0.025。
"""
from __future__ import annotations

import json
import math
import urllib.request
from typing import Dict, List, Optional

from ..data.cache import TTL_FINANCIAL_SNAPSHOT, cached

# A 股股权风险溢价（学术研究 + 历史中位数）
# 参考: 麻省理工 D&P 2023 中国 ERP 估算 6.4%；国内学者普遍 5-7%
DEFAULT_ERP = 0.06
# 默认企业所得税率（中国一般企业 25%，高新技术企业 15%）
DEFAULT_TAX_RATE = 0.25
# 无风险利率兜底值（10Y 国债近 5 年中位数约 2.5-3%）
DEFAULT_RF = 0.0275


def _http_get(url: str, timeout: int = 8) -> Optional[dict]:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        return json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, OSError):
        return None


@cached(ttl=86400)  # 1 天
def calc_risk_free_rate() -> float:
    """
    10 年期国债到期收益率（东财宏观数据中心）。

    Returns:
        无风险利率（小数，如 0.0275 表示 2.75%）
    """
    # 东财中国国债收益率接口
    url = ("https://datacenter-web.eastmoney.com/api/data/v1/get"
           "?reportName=RPT_BOND_CN_TBYIELDS&columns=ALL"
           "&filter=(SOLAR_DATE%3E%3D%272024-01-01%27)"
           "&sortColumns=SOLAR_DATE&sortTypes=-1&pageSize=5&pageNumber=1")
    data = _http_get(url)
    if not isinstance(data, dict):
        return DEFAULT_RF
    result_obj = data.get("result") or {}
    if not isinstance(result_obj, dict):
        return DEFAULT_RF
    rows = result_obj.get("data") or []
    if not rows:
        return DEFAULT_RF
    # 找最近一条 10Y 国债收益率
    for row in rows:
        if not isinstance(row, dict):
            continue
        if str(row.get("ZQMC", "")).find("10") >= 0 or row.get("ZQLX") == 10:
            yield_val = row.get("YIELD")
            if yield_val and float(yield_val) > 0:
                return float(yield_val) / 100.0
    # 兜底：取最后一行的 10Y 字段（接口字段名可能为 'EMM00166466'）
    last = rows[0]
    if isinstance(last, dict):
        for k in ("EMM00166466", "YIELD_10Y", "YIELD"):
            if last.get(k):
                try:
                    val = float(last[k])
                    if val > 0:
                        return val / 100.0 if val > 0.1 else val  # 自动判断是百分比还是小数
                except (TypeError, ValueError):
                    continue
    return DEFAULT_RF


def calc_equity_risk_premium() -> float:
    """A 股股权风险溢价（默认 6%，可配置）"""
    return DEFAULT_ERP


def calc_beta(stock_returns: List[float],
              benchmark_returns: List[float],
              window: int = 60) -> float:
    """
    OLS Beta = Cov(R_stock, R_bench) / Var(R_bench)。

    Args:
        stock_returns: 个股日收益率序列
        benchmark_returns: 沪深 300 日收益率序列（需与 stock_returns 等长且对齐）
        window: 取最近 window 个交易日

    Returns:
        Beta（数据不足或方差为 0 时返回 1.0）
    """
    n = min(len(stock_returns), len(benchmark_returns), window)
    if n < 20:
        return 1.0  # 默认市场 beta

    rs = stock_returns[-n:]
    rb = benchmark_returns[-n:]
    mean_s = sum(rs) / n
    mean_b = sum(rb) / n
    cov = sum((rs[i] - mean_s) * (rb[i] - mean_b) for i in range(n)) / (n - 1)
    var_b = sum((rb[i] - mean_b) ** 2 for i in range(n)) / (n - 1)
    if var_b < 1e-12:
        return 1.0
    beta = cov / var_b
    # 合理区间 clip（A 股 beta 极少超过 3 或低于 0.3）
    return max(0.2, min(3.0, beta))


def calc_cost_of_equity(beta: float, rf: float, erp: float) -> float:
    """CAPM: Ke = Rf + β × ERP"""
    return rf + beta * erp


def calc_cost_of_debt(interest_expense: float,
                      total_debt: float,
                      tax_rate: float = DEFAULT_TAX_RATE) -> float:
    """
    税后债务成本 Kd × (1 - T)。

    Args:
        interest_expense: 财务费用（或更准确的利息支出）
        total_debt: 有息负债（短期借款 + 长期借款 + 应付债券 + 一年内到期非流动负债）
        tax_rate: 企业所得税率

    Returns:
        税后债务成本（小数）；total_debt <= 0 时返回 0
    """
    if total_debt <= 0 or interest_expense <= 0:
        return 0.0
    pre_tax = interest_expense / total_debt
    return pre_tax * (1 - tax_rate)


def calc_wacc(code: str,
              stock_returns: Optional[List[float]] = None,
              benchmark_returns: Optional[List[float]] = None,
              interest_expense: float = 0.0,
              total_debt: float = 0.0,
              market_cap: float = 0.0,
              tax_rate: float = DEFAULT_TAX_RATE,
              erp: Optional[float] = None) -> Dict:
    """
    计算 WACC。

    Args:
        code: 股票代码（仅用于标识，不主动获取数据）
        stock_returns / benchmark_returns: 用于计算 beta
        interest_expense: 财务费用（近似利息支出）
        total_debt: 有息负债总额
        market_cap: 股权市值（用于确定权重；缺失时按 100% 股权处理）
        tax_rate: 税率
        erp: 自定义 ERP；默认调用 calc_equity_risk_premium()

    Returns:
        {
            code, wacc, cost_of_equity, cost_of_debt,
            beta, rf, erp, tax_rate,
            equity_weight, debt_weight,
            market_cap, total_debt,
            assumptions: list[str],
            insufficient_data: bool
        }
    """
    rf = calc_risk_free_rate()
    erp_val = erp if erp is not None else calc_equity_risk_premium()

    # Beta
    if stock_returns and benchmark_returns:
        beta = calc_beta(stock_returns, benchmark_returns)
    else:
        beta = 1.0

    # 股权成本
    cost_of_equity = calc_cost_of_equity(beta, rf, erp_val)

    # 债务成本
    cost_of_debt = calc_cost_of_debt(interest_expense, total_debt, tax_rate)

    # 资本结构权重
    # v7.2: 市值不可得时默认1亿股权（估算值，标记来源）
    equity_value = market_cap if market_cap > 0 else 1e8
    equity_is_estimated = market_cap <= 0
    debt_value = total_debt if total_debt > 0 else 0
    total_value = equity_value + debt_value
    if total_value <= 0:
        return {"error": f"权益与债务均为 0，无法计算 WACC ({code})"}
    equity_weight = equity_value / total_value
    debt_weight = debt_value / total_value

    wacc = equity_weight * cost_of_equity + debt_weight * cost_of_debt

    # 限制到合理区间 [6%, 15%]
    wacc_clipped = max(0.06, min(0.15, wacc))
    clipped = abs(wacc_clipped - wacc) > 1e-6

    assumptions: List[str] = [
        f"无风险利率 Rf = {rf*100:.2f}%（10Y 国债收益率）",
        f"股权风险溢价 ERP = {erp_val*100:.2f}%（A 股历史中位数）",
        f"Beta = {beta:.2f}（{'用户提供' if stock_returns and benchmark_returns else '默认市场值 1.0，数据不足'}）",
        f"税率 T = {tax_rate*100:.0f}%",
    ]
    if clipped:
        assumptions.append(f"WACC 原始值 {wacc*100:.2f}% 已 clip 到 {wacc_clipped*100:.2f}%（合理区间 6%-15%）")

    return {
        "code": code,
        "wacc": wacc_clipped,
        "cost_of_equity": cost_of_equity,
        "cost_of_debt": cost_of_debt,
        "beta": beta,
        "rf": rf,
        "erp": erp_val,
        "tax_rate": tax_rate,
        "equity_weight": equity_weight,
        "debt_weight": debt_weight,
        "market_cap": market_cap,
        "total_debt": total_debt,
        "assumptions": assumptions,
        "insufficient_data": not (stock_returns and benchmark_returns and total_debt > 0 and market_cap > 0),
        "equity_is_estimated": equity_is_estimated,  # v7.2
        "data_quality": {                             # v7.2
            "market_cap": "estimated" if equity_is_estimated else "actual",
            "beta": "actual" if stock_returns and benchmark_returns else "estimated(default 1.0)",
        },
    }
