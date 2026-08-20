#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""波动率体制分析 (v9.0.0 新增)
============================
波动率体制（Volatility Regime）—— 衡量市场恐慌/平静程度。

波动率本身有「聚集」与「均值回归」特性：低波动后常延续平静（多头友好），
波动率急剧扩张往往伴随下跌/恐慌。识别当前波动体制对择时与仓位至关重要。

本模块计算：
  - 已实现波动率（20d/60d 年化）
  - 体制标签：低波动 / 扩张 / 高波动 / 压缩
  - 波动率的波动（vol-of-vol）
  - 当前波动率相对历史的分位
  - 可选：接线 GarchForecaster 做波动率预测

纯函数离线可测 + 优雅降级。

用法:
    from stock_researcher.index_analysis.volatility_regime import VolatilityRegimeAnalyzer
    v = VolatilityRegimeAnalyzer().analyze("sh000001")
    print(v.regime, v.realized_vol_20d)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass, field


@dataclass
class VolatilityResult:
    """波动率体制结果"""
    code: str = ""
    realized_vol_20d: float = 0.0    # 年化已实现波动率(%)
    realized_vol_60d: float = 0.0
    vol_of_vol: float = 0.0         # 波动率的波动（20d vol 序列标准差）
    vol_percentile: float = 50.0     # 当前20d vol 在历史中的百分位 0-100
    regime: str = "未知"             # 低波动/扩张/高波动/压缩/未知
    bull_friendly: bool = False      # 低波动+未扩张 → 多头友好
    forecast_vol: Optional[float] = None  # GARCH 预测（可选）
    signals: Dict = field(default_factory=dict)
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层
# ════════════════════════════════════════════════════════════

def _clean(values: Sequence[float]) -> List[float]:
    out = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isfinite(f) and f > 0:
            out.append(f)
    return out


def log_returns(prices: Sequence[float]) -> List[float]:
    """日对数收益。"""
    s = _clean(prices)
    if len(s) < 2:
        return []
    return [math.log(s[i] / s[i - 1]) for i in range(1, len(s)) if s[i - 1] > 0]


def realized_vol(prices: Sequence[float], n: int = 20, annualize: int = 252) -> float:
    """末段 n 期日收益年化波动率（小数，如 0.18=18%）。"""
    r = log_returns(prices)
    if len(r) < n or n < 2:
        # 不足 n 时用全部可用
        if len(r) < 5:
            return 0.0
        window = r
    else:
        window = r[-n:]
    m = sum(window) / len(window)
    var = sum((x - m) ** 2 for x in window) / (len(window) - 1)
    return math.sqrt(var) * math.sqrt(annualize)


def vol_percentile(prices: Sequence[float], n: int = 20, anchor_n: int = 20) -> float:
    """当前 n 期已实现 vol 在「过去各滚动窗口 vol」中的百分位（0-100）。

    anchor_n: 用于历史比较的滚动 vol 序列长度（约近一年）。
    """
    r = log_returns(prices)
    if len(r) < n + anchor_n:
        return 50.0
    # 滚动 n 期 vol（年化）
    annual = math.sqrt(252)
    rolling = []
    for i in range(n, len(r) + 1):
        w = r[i - n:i]
        if len(w) >= 2:
            m = sum(w) / len(w)
            var = sum((x - m) ** 2 for x in w) / (len(w) - 1)
            rolling.append(math.sqrt(var) * annual)
    if len(rolling) < 5:
        return 50.0
    current = rolling[-1]
    history = rolling[-min(anchor_n * 5, len(rolling)):]
    less = sum(1 for v in history if v < current)
    equal = sum(1 for v in history if v == current)
    nn = len(history)
    if nn <= 1:
        return 50.0
    avg_pos = less + (equal - 1) / 2.0
    return avg_pos / (nn - 1) * 100.0


def vol_regime_label(
    rv20: float, rv60: float,
    low_threshold: float = 0.12, high_threshold: float = 0.25,
) -> str:
    """波动率体制标签。

    判定顺序（优先级）：
      1. 高波动：20d vol ≥ 25%（绝对高位优先）
      2. 压缩：20d 相对 60d 显著回落（ratio ≤ 0.70，波动收敛中）
      3. 扩张：20d 相对 60d 显著放大（ratio ≥ 1.30，波动放大中，常伴下跌）
      4. 低波动：20d vol ≤ 12%
      5. 中性

    「扩张/压缩」需强相对变化才触发，避免微小波动误判为体制转换。
    """
    if rv20 <= 0 or rv60 <= 0:
        return "未知"
    if rv20 >= high_threshold:
        return "高波动"
    ratio = rv20 / rv60
    if ratio <= 0.70:
        return "压缩"
    if ratio >= 1.30:
        return "扩张"
    if rv20 <= low_threshold:
        return "低波动"
    return "中性"


def is_bull_friendly(rv20: float, rv60: float, regime: str) -> bool:
    """低波动且未扩张 → 多头友好（趋势延续概率高）。"""
    return regime in ("低波动", "压缩") and rv20 > 0 and rv20 < 0.20


def rolling_vol_series(prices: Sequence[float], n: int = 20) -> List[float]:
    """滚动 n 期年化波动率序列（用于 vol-of-vol）。"""
    r = log_returns(prices)
    annual = math.sqrt(252)
    out = []
    for i in range(n, len(r) + 1):
        w = r[i - n:i]
        if len(w) >= 2:
            m = sum(w) / len(w)
            var = sum((x - m) ** 2 for x in w) / (len(w) - 1)
            out.append(math.sqrt(var) * annual)
    return out


def vol_of_vol(prices: Sequence[float], n: int = 20) -> float:
    """波动率的波动（滚动 vol 序列的标准差）。"""
    series = rolling_vol_series(prices, n)
    if len(series) < 2:
        return 0.0
    m = sum(series) / len(series)
    var = sum((x - m) ** 2 for x in series) / (len(series) - 1)
    return math.sqrt(var)


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class VolatilityRegimeAnalyzer:
    """波动率体制分析器。"""

    def analyze(self, code: str, days: int = 260) -> VolatilityResult:
        prices = self._fetch_prices(code, days)
        if not prices or len(prices) < 30:
            return VolatilityResult(code=code, note="行情数据不足")
        return self.analyze_from_prices(code, prices)

    def analyze_from_prices(self, code: str, prices: Sequence[float]) -> VolatilityResult:
        """从已有价格序列分析（便于复用 / 测试）。"""
        rv20 = realized_vol(prices, 20)
        rv60 = realized_vol(prices, 60)
        vov = vol_of_vol(prices, 20)
        pct = vol_percentile(prices, 20)
        regime = vol_regime_label(rv20, rv60)
        bull = is_bull_friendly(rv20, rv60, regime)

        # 可选 GARCH 预测（缺失自动跳过）
        forecast = None
        try:
            from stock_researcher.quantitative.garch_model import GarchForecaster
            gf = GarchForecaster()
            res = gf.analyze_volatility_regime(list(prices))
            # 不同实现返回字段不一，尽力取
            if isinstance(res, dict):
                forecast = res.get("forecast_vol") or res.get("next_vol")
        except Exception:
            pass

        return VolatilityResult(
            code=code,
            realized_vol_20d=round(rv20 * 100, 2),
            realized_vol_60d=round(rv60 * 100, 2),
            vol_of_vol=round(vov * 100, 4),
            vol_percentile=round(pct, 1),
            regime=regime,
            bull_friendly=bull,
            forecast_vol=round(forecast * 100, 2) if forecast else None,
            signals={"rv20": round(rv20, 4), "rv60": round(rv60, 4),
                     "ratio_20_60": round(rv20 / rv60, 3) if rv60 else 0},
            note="基于20/60日已实现波动率",
        )

    def _fetch_prices(self, code: str, days: int) -> List[float]:
        try:
            c = str(code).lower()
            if c.startswith(("100.", "idx:")):
                from stock_researcher.data.global_market import fetch_global_kline
                kl = fetch_global_kline(f"idx:{code}", days=days) or []
                return [float(k.get("close", 0)) for k in kl
                        if isinstance(k, dict) and k.get("close")]
            from stock_researcher.data.market import MarketData
            md = MarketData()
            if c.startswith("sh") or c.startswith("sz"):
                k = md.fetch_history(c[2:], days=days, prefix=c[:2]) or {}
            else:
                k = md.fetch_history(code, days=days) or {}
            return [float(p) for p in k.get("closes", []) if p is not None]
        except Exception:
            return []

    @staticmethod
    def format(v: VolatilityResult) -> str:
        fc = f" 预测{v.forecast_vol:.1f}%" if v.forecast_vol else ""
        return (
            f"波动率体制: {v.regime}{'(多头友好)' if v.bull_friendly else ''} | "
            f"20d年化{v.realized_vol_20d:.1f}% 60d{v.realized_vol_60d:.1f}% "
            f"历史分位{v.vol_percentile:.0f}% vol-of-vol{v.vol_of_vol:.2f}{fc}"
        )


def analyze_volatility(code: str) -> VolatilityResult:
    """便捷函数：波动率体制。"""
    return VolatilityRegimeAnalyzer().analyze(code)
