# -*- coding: utf-8 -*-
"""统一全资产量化分析入口（asset_quant.py，v8.0 新增 / v9.3 增强）

一个 API 量化任意金融产品：股票/基金/指数/债券/商品/期货/货币基金/可转债，
输出 绩效指标(QuantMetrics) + 场景模拟(蒙特卡洛) + 多周期涨跌预测
+ 历史形态匹配预测(v9.3) + 资产专属分析。

用法：
    from stock_researcher.quantitative.asset_quant import quant_analyze_asset

    r = quant_analyze_asset("600519")                    # 股票
    r = quant_analyze_asset("510300", asset_type="fund") # ETF
    r = quant_analyze_asset("128046", asset_type="convertible")
"""

import math
from dataclasses import asdict
from typing import Dict, List, Optional


# 资产类型特征表（code → 类型）
_TYPE_HINTS = {
    "gold": "commodity", "silver": "commodity", "crude": "commodity",
    "idx": "index", "bond": "bond", "mf": "money_fund",
}


def detect_asset_type(code: str, hint: Optional[str] = None) -> str:
    """识别资产类型（纯逻辑，不联网）。"""
    if hint and hint != "auto":
        return hint
    c = str(code).lower()
    for prefix, atype in _TYPE_HINTS.items():
        if c.startswith(prefix + ":") or c.startswith(prefix + "-") or c == prefix:
            return atype
    if c.startswith(("hk:", "r_hk")):
        return "stock"
    if c.startswith(("us:", "t_us")):
        return "stock"
    if c.isdigit() and len(c) == 6:
        # 可转债代码特征：11xxxx（沪）12xxxx（深）
        if c.startswith(("11", "12")):
            return "convertible"
        return "stock"
    return "fund"


def _safe_prices(prices: Optional[List[float]], ohlcv: Optional[Dict]) -> List[float]:
    if prices:
        return [float(p) for p in prices if p is not None]
    if ohlcv and ohlcv.get("closes"):
        return [float(p) for p in ohlcv["closes"] if p is not None]
    return []


def _fetch_prices(code: str, asset_type: str) -> List[float]:
    """按资产类型获取价格序列（失败返回空）。"""
    try:
        if asset_type == "stock":
            from stock_researcher.data.market import MarketData
            kline = MarketData().fetch_history(code, days=120) or {}
            return [float(p) for p in kline.get("closes", []) if p is not None]
        if asset_type in ("index", "commodity", "futures"):
            from stock_researcher.data.global_market import fetch_global_kline
            kl = fetch_global_kline(code, days=120) or []
            return [float(k["close"]) for k in kl if isinstance(k, dict)]
        if asset_type == "fund":
            try:
                from pkg.fund_analyzer import fetch_fund_nav
                nav = fetch_fund_nav(code) or []
                return [float(x) for x in nav if x is not None]
            except Exception:
                return []
    except Exception:
        return []
    return []


def _compute_metrics(prices: List[float], code: str) -> Dict:
    """通用绩效/风险指标（QuantMetrics）。"""
    if len(prices) < 3:
        return {}
    try:
        from stock_researcher.quantitative.metrics import compute_quant_metrics
        m = compute_quant_metrics(prices, symbol=str(code))
        return asdict(m) if hasattr(m, "__dataclass_fields__") else {}
    except Exception:
        return {}


def _compute_scenario(prices: List[float]) -> Dict:
    """场景模拟（蒙特卡洛）。"""
    if len(prices) < 20:
        return {}
    try:
        from stock_researcher.quantitative.scenario_simulator import quick_scenario_forecast
        return quick_scenario_forecast(prices, current_score=50, horizon_days=20,
                                       n_simulations=1000)
    except Exception:
        return {}


def _compute_forecast(code: str, asset_type: str, prices: List[float]) -> Dict:
    """多周期涨跌预测（MultiHorizonForecaster，含 ML overlay）。"""
    try:
        from stock_researcher.fusion.multi_horizon_forecaster import MultiHorizonForecaster
        kline = {"closes": prices}
        mhf = MultiHorizonForecaster()
        f = mhf.forecast_asset(code, asset_type=asset_type, prices=prices)
        out = {}
        for h, fr in (f.horizons or {}).items():
            out[h] = {
                "direction": fr.direction,
                "predicted_pct": fr.predicted_pct,
                "prob_up": fr.prob_up,
                "confidence": fr.confidence,
                "p10": getattr(fr, "p10", None),
                "p90": getattr(fr, "p90", None),
            }
        return out
    except Exception:
        return {}


def _compute_pattern_forecast(prices: List[float]) -> Dict:
    """历史形态匹配预测（v9.3，纯离线，股票/基金/期货通用）。"""
    if len(prices) < 60:
        return {}
    try:
        from stock_researcher.quantitative.pattern_predictor import (
            quick_pattern_forecast, pattern_direction_label)
        out = {}
        for key, horizon in (("short", 5), ("medium", 20)):
            fc = quick_pattern_forecast(prices, horizon=horizon)
            fc["direction_label"] = pattern_direction_label(fc)
            out[key] = fc
        return out
    except Exception:
        return {}


def _asset_specific_analysis(code: str, asset_type: str, prices: List[float]) -> Dict:
    """资产专属分析（债券/货基/可转债有专门模块，其余为空）。"""
    try:
        if asset_type == "bond":
            from stock_researcher.quantitative.bond_analyzer import analyze_bond
            return analyze_bond(code=code)
        if asset_type == "money_fund":
            from stock_researcher.quantitative.money_fund_analyzer import MoneyFundAnalyzer
            return MoneyFundAnalyzer().analyze(nav_series=prices)
        if asset_type == "convertible":
            return {"note": "可转债需行情参数，请用 ConvertibleBondAnalyzer.analyze 或 quick_convertible_score"}
    except Exception:
        pass
    return {}


def quant_analyze_asset(code: str, asset_type: Optional[str] = None,
                        prices: Optional[List[float]] = None,
                        ohlcv: Optional[Dict] = None,
                        horizons: Optional[List[str]] = None,
                        **kw) -> Dict:
    """统一全资产量化分析入口。

    Args:
        code: 资产代码（股票 6 位 / 基金 / 债券 / 商品前缀等）
        asset_type: 显式类型（stock/fund/index/commodity/futures/bond/money_fund/convertible）
        prices: 历史价格序列（可选，未提供时按类型自动获取）
        ohlcv: K线 dict（可选，含 closes）
        horizons: 预测周期（默认全部）

    Returns:
        {code, asset_type, name, metrics, scenario, forecast, pattern_forecast,
         asset_specific, data_quality}
    """
    asset_type = detect_asset_type(code, asset_type)
    prices = _safe_prices(prices, ohlcv)

    result: Dict = {
        "code": code,
        "asset_type": asset_type,
        "name": kw.get("name", ""),
        "metrics": _compute_metrics(prices, code) if prices else {},
        "scenario": _compute_scenario(prices) if prices else {},
        "forecast": _compute_forecast(code, asset_type, prices) if prices else {},
        "pattern_forecast": _compute_pattern_forecast(prices) if prices else {},
        "asset_specific": _asset_specific_analysis(code, asset_type, prices),
        "data_quality": "actual" if prices else "unavailable",
    }
    if not prices:
        result["note"] = "未获取到价格序列（离线或数据源不可用），metrics/scenario/forecast 为空"
    return result


if __name__ == "__main__":
    import json
    demo = [100 + i * 0.5 + (i % 7) * 0.2 for i in range(120)]
    r = quant_analyze_asset("600519", prices=demo)
    print(json.dumps({k: v for k, v in r.items() if k != "forecast"},
                     ensure_ascii=False, indent=2, default=str))
