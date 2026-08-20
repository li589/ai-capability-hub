#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""业绩指标库 (v7.0 新增)

投资分析 / 投后检视共用的纯计算指标库：
- 年化收益 / 年化波动 / Sharpe / Sortino / 最大回撤 / Calmar
- 信息比率 / 跟踪误差 / Beta / Alpha
- 滚动指标（滚动年化、滚动回撤等）
- compute_all_metrics 一键汇总

约定：
- 输入均为 list[float] 净值序列（按时间升序，至少 2 个点才有意义）
- 收益率、波动率、回撤等"百分比类"返回值单位为 %（如 -16.67 表示 -16.67%）
- Sharpe/Sortino/Calmar/IR/Beta 为无量纲比值
- 无风险利率 rf 为小数（默认 0.02 即 2%）
- 纯标准库、无网络；长度 < 2 的输入安全返回 None 或空结构
"""
from __future__ import annotations

import sys
import math
from pathlib import Path
from typing import Dict, List, Optional

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))

TRADING_DAYS = 252  # 年化基准：一年按 252 个交易日


# ─── 工具函数 ─────────────────────────────────────────────
def _to_returns(series: List[float]) -> List[float]:
    """净值序列 -> 区间简单收益率序列（长度 n-1）

    非法值（None/非正数）会被跳过；任何输入异常返回空列表。
    """
    try:
        vals = [float(x) for x in series if x is not None and float(x) > 0]
    except (TypeError, ValueError):
        return []
    if len(vals) < 2:
        return []
    return [vals[i] / vals[i - 1] - 1.0 for i in range(1, len(vals))]


def _clean_series(series: List[float]) -> List[float]:
    """清洗净值序列：去 None/非正数，转 float"""
    try:
        return [float(x) for x in series if x is not None and float(x) > 0]
    except (TypeError, ValueError):
        return []


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _std(xs: List[float], ddof: int = 1) -> float:
    """样本标准差"""
    n = len(xs)
    if n <= ddof:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (n - ddof))


# ─── 单序列指标 ───────────────────────────────────────────
def annualized_return(nav_series: List[float], periods_per_year: int = TRADING_DAYS) -> Optional[float]:
    """年化收益率（%）。几何年化：(end/start)^(ppy/(n-1)) - 1。

    输入不足 2 个点返回 None。
    """
    vals = _clean_series(nav_series)
    if len(vals) < 2:
        return None
    total = vals[-1] / vals[0]
    if total <= 0:
        return None
    years = (len(vals) - 1) / periods_per_year
    if years <= 0:
        return None
    return (total ** (1.0 / years) - 1.0) * 100.0


def annualized_volatility(nav_series: List[float], periods_per_year: int = TRADING_DAYS) -> Optional[float]:
    """年化波动率（%）。日收益标准差 × sqrt(periods_per_year)。"""
    rets = _to_returns(nav_series)
    if len(rets) < 2:
        return None
    return _std(rets) * math.sqrt(periods_per_year) * 100.0


def sharpe(nav_series: List[float], rf: float = 0.02) -> Optional[float]:
    """夏普比率 = (年化收益 - rf) / 年化波动（无量纲）"""
    ann = annualized_return(nav_series)
    vol = annualized_volatility(nav_series)
    if ann is None or vol is None or vol <= 0:
        return None
    return (ann / 100.0 - rf) / (vol / 100.0)


def sortino(nav_series: List[float], rf: float = 0.02) -> Optional[float]:
    """索提诺比率 = (年化收益 - rf) / 年化下行波动（仅统计负收益）"""
    rets = _to_returns(nav_series)
    if len(rets) < 2:
        return None
    ann = annualized_return(nav_series)
    if ann is None:
        return None
    downside = [r for r in rets if r < 0]
    if not downside:
        return None  # 无下行波动，无法定义
    down_vol = math.sqrt(_mean([r ** 2 for r in downside])) * math.sqrt(TRADING_DAYS)
    if down_vol <= 0:
        return None
    return (ann / 100.0 - rf) / down_vol


def max_drawdown(nav_series: List[float]) -> Optional[Dict]:
    """最大回撤

    返回 dict：
      mdd           最大回撤（%，负数，如 -16.67）
      peak_idx      峰值下标（相对清洗后序列）
      trough_idx    谷值下标
      duration_days 峰值到谷值的区间数（约等于交易日数）
    输入不足 2 个点返回 None。
    """
    vals = _clean_series(nav_series)
    if len(vals) < 2:
        return None
    peak = vals[0]
    peak_idx = 0
    mdd = 0.0
    mdd_peak = mdd_trough = 0
    for i, v in enumerate(vals):
        if v > peak:
            peak = v
            peak_idx = i
        dd = (v - peak) / peak * 100.0
        if dd < mdd:
            mdd = dd
            mdd_peak = peak_idx
            mdd_trough = i
    return {
        "mdd": round(mdd, 4),
        "peak_idx": mdd_peak,
        "trough_idx": mdd_trough,
        "duration_days": mdd_trough - mdd_peak,
    }


def calmar(nav_series: List[float]) -> Optional[float]:
    """卡玛比率 = 年化收益 / |最大回撤|（小数/小数，无量纲）"""
    ann = annualized_return(nav_series)
    dd = max_drawdown(nav_series)
    if ann is None or dd is None or dd["mdd"] >= 0:
        return None
    return (ann / 100.0) / abs(dd["mdd"] / 100.0)


# ─── 双序列指标（组合 vs 基准）─────────────────────────────
def _aligned_returns(portfolio_series: List[float], benchmark_series: List[float]):
    """对齐两条净值序列（截短到等长）并返回各自收益序列"""
    p = _clean_series(portfolio_series)
    b = _clean_series(benchmark_series)
    n = min(len(p), len(b))
    if n < 2:
        return [], []
    return _to_returns(p[-n:]), _to_returns(b[-n:])


def tracking_error(portfolio_series: List[float], benchmark_series: List[float]) -> Optional[float]:
    """跟踪误差（%）= 超额收益序列标准差 × sqrt(252)"""
    pr, br = _aligned_returns(portfolio_series, benchmark_series)
    if len(pr) < 2:
        return None
    diff = [a - b for a, b in zip(pr, br)]
    return _std(diff) * math.sqrt(TRADING_DAYS) * 100.0


def information_ratio(portfolio_series: List[float], benchmark_series: List[float]) -> Optional[float]:
    """信息比率 = 年化超额收益 / 跟踪误差（无量纲）"""
    pr, br = _aligned_returns(portfolio_series, benchmark_series)
    if len(pr) < 2:
        return None
    diff = [a - b for a, b in zip(pr, br)]
    te = _std(diff) * math.sqrt(TRADING_DAYS)
    if te <= 0:
        return None
    ann_excess = _mean(diff) * TRADING_DAYS
    return ann_excess / te


def beta_alpha(portfolio_series: List[float], benchmark_series: List[float]) -> Optional[Dict]:
    """Beta / Alpha（CAPM）

    返回 dict：
      beta   组合对基准的回归斜率
      alpha  年化 alpha（%，几何近似：组合年化 - beta × 基准年化）
    """
    pr, br = _aligned_returns(portfolio_series, benchmark_series)
    if len(pr) < 2:
        return None
    mb = _mean(br)
    var_b = sum((x - mb) ** 2 for x in br)
    if var_b <= 0:
        return None
    mp = _mean(pr)
    cov = sum((a - mp) * (b - mb) for a, b in zip(pr, br))
    beta = cov / var_b
    # 年化 alpha（%）：日 alpha × 252
    alpha_ann = (mp - beta * mb) * TRADING_DAYS * 100.0
    return {"beta": round(beta, 4), "alpha": round(alpha_ann, 4)}


# ─── 汇总 / 滚动 ──────────────────────────────────────────
def compute_all_metrics(portfolio_series: List[float],
                        benchmark_series: Optional[List[float]] = None,
                        rf: float = 0.02) -> Dict:
    """一键汇总组合业绩指标

    返回 dict（样本不足时相应字段为 None）：
      total_return / annualized / volatility / sharpe / sortino /
      max_drawdown(%) / calmar
    传入 benchmark 时额外给出：
      benchmark_return / excess_return / information_ratio /
      tracking_error / beta / alpha
    """
    vals = _clean_series(portfolio_series)
    result: Dict = {"samples": len(vals)}
    if len(vals) < 2:
        result.update({"total_return": None, "annualized": None, "volatility": None,
                       "sharpe": None, "sortino": None, "max_drawdown": None, "calmar": None})
    else:
        total = (vals[-1] / vals[0] - 1.0) * 100.0
        dd = max_drawdown(vals)
        result.update({
            "total_return": round(total, 4),
            "annualized": _round(annualized_return(vals)),
            "volatility": _round(annualized_volatility(vals)),
            "sharpe": _round(sharpe(vals, rf)),
            "sortino": _round(sortino(vals, rf)),
            "max_drawdown": dd["mdd"] if dd else None,
            "max_drawdown_detail": dd,
            "calmar": _round(calmar(vals)),
        })
    if benchmark_series:
        bvals = _clean_series(benchmark_series)
        if len(bvals) >= 2 and len(vals) >= 2:
            n = min(len(vals), len(bvals))
            pwin, bwin = vals[-n:], bvals[-n:]
            ptot = (pwin[-1] / pwin[0] - 1.0) * 100.0
            btot = (bwin[-1] / bwin[0] - 1.0) * 100.0
            ba = beta_alpha(pwin, bwin)
            result.update({
                "benchmark_return": round(btot, 4),
                "excess_return": round(ptot - btot, 4),
                "information_ratio": _round(information_ratio(pwin, bwin)),
                "tracking_error": _round(tracking_error(pwin, bwin)),
                "beta": ba["beta"] if ba else None,
                "alpha": ba["alpha"] if ba else None,
            })
    return result


def rolling_metric(nav_series: List[float], window: int, metric: str = "annualized") -> List[Optional[float]]:
    """滚动指标序列（长度与输入一致，前 window-1 个为 None）

    metric 可选：annualized(年化收益%) / volatility(年化波动%) /
                 sharpe / mdd(区间内最大回撤%)
    """
    vals = _clean_series(nav_series)
    if window < 2 or len(vals) < window:
        return [None] * len(vals)
    fn_map = {
        "annualized": annualized_return,
        "volatility": annualized_volatility,
        "sharpe": sharpe,
        "mdd": lambda s: (max_drawdown(s) or {}).get("mdd"),
    }
    fn = fn_map.get(metric, annualized_return)
    out: List[Optional[float]] = [None] * (window - 1)
    for i in range(window - 1, len(vals)):
        v = fn(vals[i - window + 1: i + 1])
        out.append(_round(v))
    return out


def _round(v: Optional[float], nd: int = 4) -> Optional[float]:
    return round(v, nd) if v is not None else None


if __name__ == "__main__":
    # 简单自演示（离线）
    demo = [1, 1.01, 0.99, 1.02, 1.05, 1.03, 1.08]
    bench = [1, 1.005, 1.0, 1.01, 1.02, 1.01, 1.03]
    import json
    print(json.dumps(compute_all_metrics(demo, bench), ensure_ascii=False, indent=2))
    print("滚动年化(window=3):", rolling_metric(demo, 3, "annualized"))
