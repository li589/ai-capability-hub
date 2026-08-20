#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一量化绩效与风险指标（纯标准库）

适用对象：股票 / 基金 / 指数 / 商品期货等任何价格序列。
不依赖 numpy / pandas / scipy，保证零依赖核心可用。

主要指标：
  - 收益：累计收益、年化收益、年化波动率
  - 风险调整：Sharpe、Sortino、Calmar、最大回撤
  - 尾部风险：95% VaR、95% CVaR
  - 交易统计：胜率、盈亏比、最好/最差单日
  - 基准对比：Beta、Alpha、相关系数、跟踪误差、信息比率
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from statistics import mean, pstdev, stdev
from typing import Dict, List, Optional, Sequence


TRADING_DAYS = 252


def _to_float(value) -> Optional[float]:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def clean_values(values: Sequence) -> List[float]:
    """清洗输入序列，仅保留有限数值。"""
    out = []
    for v in values:
        f = _to_float(v)
        if f is not None:
            out.append(f)
    return out


def daily_returns(prices: Sequence[float]) -> List[float]:
    """由价格序列计算日收益率（跳过无效价格）。"""
    cleaned = clean_values(prices)
    out = []
    for i in range(1, len(cleaned)):
        prev = cleaned[i - 1]
        cur = cleaned[i]
        if prev > 0 and cur >= 0:
            out.append(cur / prev - 1.0)
    return out


def _std(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    return stdev(values)


def annualized_return(returns: List[float], periods: int = TRADING_DAYS) -> Optional[float]:
    """几何年化收益。"""
    if not returns:
        return None
    total = 1.0
    for r in returns:
        if r <= -1.0:
            return -1.0
        total *= 1.0 + r
    n = len(returns)
    if total <= 0:
        return -1.0
    return (total ** (periods / n)) - 1.0


def annualized_volatility(returns: List[float], periods: int = TRADING_DAYS) -> float:
    return _std(returns) * math.sqrt(periods)


def sharpe_ratio(returns: List[float], risk_free: float = 0.02,
                 periods: int = TRADING_DAYS) -> Optional[float]:
    vol = annualized_volatility(returns, periods)
    ann = annualized_return(returns, periods)
    if vol <= 1e-12 or ann is None:
        return None
    return (ann - risk_free) / vol


def downside_deviation(returns: List[float], risk_free: float = 0.02,
                       periods: int = TRADING_DAYS) -> float:
    rf_daily = (1.0 + risk_free) ** (1.0 / periods) - 1.0
    negative = [min(r - rf_daily, 0.0) ** 2 for r in returns]
    return math.sqrt(mean(negative)) if negative else 0.0


def sortino_ratio(returns: List[float], risk_free: float = 0.02,
                  periods: int = TRADING_DAYS) -> Optional[float]:
    ann = annualized_return(returns, periods)
    dd = downside_deviation(returns, risk_free, periods) * math.sqrt(periods)
    if ann is None or dd <= 1e-12:
        return None
    return (ann - risk_free) / dd


def max_drawdown(prices: Sequence[float]) -> float:
    """由价格序列计算最大回撤（正数，如 0.23 表示 -23%）。"""
    cleaned = clean_values(prices)
    if len(cleaned) < 2:
        return 0.0
    peak = cleaned[0]
    mdd = 0.0
    for price in cleaned[1:]:
        if price > peak:
            peak = price
        if peak > 0:
            dd = (price - peak) / peak
            if dd < mdd:
                mdd = dd
    return abs(mdd)


def calmar_ratio(returns: List[float], prices: Sequence[float],
                 periods: int = TRADING_DAYS) -> Optional[float]:
    ann = annualized_return(returns, periods)
    mdd = max_drawdown(prices)
    if ann is None or mdd <= 1e-12:
        return None
    return ann / mdd


def empirical_var_cvar(returns: List[float], alpha: float = 0.05) -> Dict:
    """经验 VaR / CVaR（返回正数损失；样本不足时返回 None）。"""
    if len(returns) < 10:
        return {"var": None, "cvar": None, "method": "empirical", "samples": len(returns)}
    k = max(1, min(len(returns), int(len(returns) * alpha)))
    sorted_returns = sorted(returns)
    var = -sorted_returns[k - 1]
    cvar = -mean(sorted_returns[:k])
    return {"var": var, "cvar": cvar, "method": "empirical", "samples": len(returns)}


def win_loss_metrics(returns: List[float]) -> Dict:
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r < 0]
    nonzero = len(wins) + len(losses)
    win_rate = len(wins) / nonzero if nonzero else None
    gross_loss = abs(sum(losses))
    profit_factor = None
    if gross_loss > 1e-12:
        profit_factor = sum(wins) / gross_loss
    return {
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "wins": len(wins),
        "losses": len(losses),
        "avg_win": mean(wins) if wins else None,
        "avg_loss": mean(losses) if losses else None,
    }


def _aligned_pairs(returns: List[float], benchmark_returns: List[float]) -> List:
    n = min(len(returns), len(benchmark_returns))
    return list(zip(returns[-n:], benchmark_returns[-n:]))


def beta_alpha(returns: List[float], benchmark_returns: List[float],
               risk_free: float = 0.02, periods: int = TRADING_DAYS) -> Dict:
    pairs = _aligned_pairs(returns, benchmark_returns)
    if len(pairs) < 20:
        return {"beta": None, "alpha_annual": None, "correlation": None,
                "tracking_error": None, "information_ratio": None,
                "samples": len(pairs)}
    r = [x[0] for x in pairs]
    b = [x[1] for x in pairs]
    mean_r = mean(r)
    mean_b = mean(b)
    var_b = sum((x - mean_b) ** 2 for x in b) / len(b)
    cov = sum((r[i] - mean_r) * (b[i] - mean_b) for i in range(len(r))) / len(r)
    beta = cov / var_b if var_b > 1e-12 else None
    corr = None
    std_r = pstdev(r)
    std_b = pstdev(b)
    if std_r > 1e-12 and std_b > 1e-12:
        corr = cov / (std_r * std_b)
    rf_daily = (1.0 + risk_free) ** (1.0 / periods) - 1.0
    ann_r = annualized_return(r, periods)
    ann_b = annualized_return(b, periods)
    alpha = None
    if ann_r is not None and ann_b is not None and beta is not None:
        alpha = (ann_r - risk_free) - beta * (ann_b - risk_free)
    diff = [r[i] - b[i] for i in range(len(r))]
    tracking_error = _std(diff) * math.sqrt(periods)
    info_ratio = None
    if tracking_error > 1e-12:
        info_ratio = mean(diff) * periods / tracking_error
    return {
        "beta": round(beta, 4) if beta is not None else None,
        "alpha_annual": round(alpha, 4) if alpha is not None else None,
        "correlation": round(corr, 4) if corr is not None else None,
        "tracking_error": round(tracking_error, 4),
        "information_ratio": round(info_ratio, 4) if info_ratio is not None else None,
        "samples": len(pairs),
    }


@dataclass
class QuantMetrics:
    """统一量化绩效指标结果。"""
    symbol: str = ""
    data_points: int = 0
    total_return_pct: Optional[float] = None
    annualized_return_pct: Optional[float] = None
    annualized_volatility_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None
    var_95_pct: Optional[float] = None
    cvar_95_pct: Optional[float] = None
    win_rate_pct: Optional[float] = None
    profit_factor: Optional[float] = None
    beta: Optional[float] = None
    alpha_annual_pct: Optional[float] = None
    correlation: Optional[float] = None
    tracking_error_pct: Optional[float] = None
    information_ratio: Optional[float] = None
    best_day_pct: Optional[float] = None
    worst_day_pct: Optional[float] = None
    positive_days: int = 0
    negative_days: int = 0

    def to_dict(self) -> Dict:
        return asdict(self)


def compute_quant_metrics(prices: Sequence[float],
                          benchmark_prices: Sequence[float] = None,
                          risk_free: float = 0.02,
                          symbol: str = "") -> QuantMetrics:
    """计算统一量化绩效与风险指标。

    Args:
        prices: 主资产价格序列
        benchmark_prices: 可选基准价格序列，用于 Beta/Alpha/相关性/跟踪误差
        risk_free: 年化无风险利率
        symbol: 资产标识

    Returns:
        QuantMetrics
    """
    cleaned = clean_values(prices)
    if len(cleaned) < 2:
        return QuantMetrics(symbol=symbol, data_points=len(cleaned))

    returns = daily_returns(cleaned)
    ann = annualized_return(returns)
    vol = annualized_volatility(returns)
    mdd = max_drawdown(cleaned)
    var_cvar = empirical_var_cvar(returns, 0.05)
    wl = win_loss_metrics(returns)
    best_day = max(returns) if returns else None
    worst_day = min(returns) if returns else None

    benchmark = {}
    if benchmark_prices is not None and len(clean_values(benchmark_prices)) >= 2:
        b_returns = daily_returns(benchmark_prices)
        benchmark = beta_alpha(returns, b_returns, risk_free)

    return QuantMetrics(
        symbol=symbol,
        data_points=len(cleaned),
        total_return_pct=round((math.prod(1.0 + r for r in returns) - 1.0) * 100, 2),
        annualized_return_pct=round(ann * 100, 2) if ann is not None else None,
        annualized_volatility_pct=round(vol * 100, 2),
        sharpe_ratio=round(sharpe_ratio(returns, risk_free), 4)
        if sharpe_ratio(returns, risk_free) is not None else None,
        sortino_ratio=round(sortino_ratio(returns, risk_free), 4)
        if sortino_ratio(returns, risk_free) is not None else None,
        calmar_ratio=round(calmar_ratio(returns, cleaned), 4)
        if calmar_ratio(returns, cleaned) is not None else None,
        max_drawdown_pct=round(mdd * 100, 2),
        var_95_pct=round(var_cvar["var"] * 100, 2) if var_cvar["var"] is not None else None,
        cvar_95_pct=round(var_cvar["cvar"] * 100, 2) if var_cvar["cvar"] is not None else None,
        win_rate_pct=round(wl["win_rate"] * 100, 2) if wl["win_rate"] is not None else None,
        profit_factor=round(wl["profit_factor"], 4) if wl["profit_factor"] is not None else None,
        beta=benchmark.get("beta"),
        alpha_annual_pct=round(benchmark["alpha_annual"] * 100, 2)
        if benchmark.get("alpha_annual") is not None else None,
        correlation=benchmark.get("correlation"),
        tracking_error_pct=round(benchmark["tracking_error"] * 100, 2)
        if benchmark.get("tracking_error") is not None else None,
        information_ratio=benchmark.get("information_ratio"),
        best_day_pct=round(best_day * 100, 2) if best_day is not None else None,
        worst_day_pct=round(worst_day * 100, 2) if worst_day is not None else None,
        positive_days=sum(1 for r in returns if r > 0),
        negative_days=sum(1 for r in returns if r < 0),
    )


def format_quant_metrics(metrics: QuantMetrics) -> str:
    """把 QuantMetrics 输出为简短可读文本。"""
    lines = [
        f"量化体检 {metrics.symbol or 'asset'}",
        f"样本 {metrics.data_points} 天 | 累计 {metrics.total_return_pct}% | 年化 {metrics.annualized_return_pct}%",
        f"年化波动 {metrics.annualized_volatility_pct}% | 最大回撤 {metrics.max_drawdown_pct}%",
        f"Sharpe {metrics.sharpe_ratio} | Sortino {metrics.sortino_ratio} | Calmar {metrics.calmar_ratio}",
        f"VaR95 {metrics.var_95_pct}% | CVaR95 {metrics.cvar_95_pct}% | 胜率 {metrics.win_rate_pct}%",
    ]
    if metrics.beta is not None:
        lines.append(
            f"Beta {metrics.beta} | Alpha {metrics.alpha_annual_pct}% | "
            f"相关 {metrics.correlation} | 信息比 {metrics.information_ratio}"
        )
    return "\n".join(lines)
