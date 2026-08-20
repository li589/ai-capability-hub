#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""市场体制分类器 (v9.0.0 新增)
============================
识别指数所处的市场体制：牛市 / 熊市 / 震荡，并给出概率。

体制是所有技术信号解读的「背景」—— 同一个 RSI 超买，在牛市是强势延续，
在熊市是反弹卖点。本模块把体制检测从「散落在各处」收口为单一可信源，
供预测融合层（regime overlay）与自上而下报告复用。

分类依据（纯价格 + 可选 VIX）：
  - 价格相对 MA200（200 日均线是牛熊分水岭）
  - MA200 斜率（上升=多头基底）
  - 自高点回撤（drawdown）：小回撤=多头；深回撤=空头
  - 距 52 周高/低的位置
  - 可选：已实现波动率体制、VIX

输出 regime_score(-100..+100) + 三体制概率 + 切换信号。

注意：基于公开价格信号的启发式综合，非精确预测。

用法:
    from stock_researcher.index_analysis.market_regime import MarketRegimeClassifier
    reg = MarketRegimeClassifier().classify("sh000001")
    print(reg.regime, reg.probability)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass, field


@dataclass
class RegimeResult:
    """市场体制分类结果"""
    code: str = ""
    regime: str = "震荡"            # 牛市/熊市/震荡
    probability: float = 0.0        # 主体制概率 0-1
    probabilities: Dict[str, float] = field(default_factory=dict)
    regime_score: float = 0.0       # -100(极熊)..+100(极牛)
    drawdown_from_high: float = 0.0  # 自高点回撤(小数, 0.2=20%)
    price_vs_ma200: str = "数据不足" # 上方/下方/数据不足
    ma200_slope: str = "未知"        # 上升/下降/走平
    distance_52w_high: float = 0.0   # 距52周高(% 负值)
    distance_52w_low: float = 0.0    # 距52周低(% 正值)
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


def sma(values: Sequence[float], n: int) -> Optional[float]:
    s = _clean(values)
    if n <= 0 or len(s) < n:
        return None
    return sum(s[-n:]) / n


def sma_series(values: Sequence[float], n: int) -> List[float]:
    """逐点 SMA（从第 n 个点起）。"""
    s = _clean(values)
    if len(s) < n or n <= 0:
        return []
    out = []
    for i in range(n, len(s) + 1):
        out.append(sum(s[i - n:i]) / n)
    return out


def max_drawdown(prices: Sequence[float]) -> float:
    """自历史最高点的最大回撤（小数，0.25=25%）。"""
    s = _clean(prices)
    if len(s) < 2:
        return 0.0
    peak = s[0]
    max_dd = 0.0
    for p in s:
        if p > peak:
            peak = p
        if peak > 0:
            dd = 1.0 - p / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def drawdown_from_high(prices: Sequence[float]) -> float:
    """当前价相对历史最高的回撤（小数）。"""
    s = _clean(prices)
    if not s:
        return 0.0
    peak = max(s)
    if peak <= 0:
        return 0.0
    return max(0.0, 1.0 - s[-1] / peak)


def slope_pct(series: Sequence[float], n: int = 20) -> float:
    """末段 n 期的日均斜率百分比（>0 上升）。用首末线性近似。"""
    s = _clean(series)
    if n < 2 or len(s) < 2:
        return 0.0
    seg = s[-min(n, len(s)):]
    if len(seg) < 2 or seg[0] <= 0:
        return 0.0
    return (seg[-1] / seg[0] - 1.0) / (len(seg) - 1)  # 每期变化率


def classify_from_prices(
    prices: Sequence[float],
    ma_n: int = 200,
    dd_threshold_bull: float = 0.10,
    dd_threshold_bear: float = 0.20,
) -> Dict:
    """从价格序列推断体制（纯函数，离线可测）。

    返回 dict(regime, probability, probabilities, regime_score, drawdown_from_high,
              price_vs_ma200, ma200_slope, distance_52w_high, distance_52w_low, signals)
    """
    s = _clean(prices)
    if len(s) < max(ma_n, 60):
        return _neutral_result("数据不足（序列过短）")

    last = s[-1]
    ma = sma(s, ma_n)
    ma_series = sma_series(s, ma_n)
    dd = drawdown_from_high(s)

    # 1) 价格 vs MA200
    if ma is None or ma <= 0:
        return _neutral_result("MA 计算失败")
    above_ma = last > ma
    price_vs = "上方" if above_ma else "下方"

    # 2) MA200 斜率（上升/下降/走平）
    ma_slope = slope_pct(ma_series, n=min(20, len(ma_series))) if ma_series else 0.0
    if ma_slope > 1e-5:
        ma_slope_label = "上升"
    elif ma_slope < -1e-5:
        ma_slope_label = "下降"
    else:
        ma_slope_label = "走平"

    # 3) 距 52 周（约 252 日）高/低
    window = s[-min(252, len(s)):]
    high52, low52 = max(window), min(window)
    dist_high = (last / high52 - 1.0) * 100 if high52 > 0 else 0.0   # 负值
    dist_low = (last / low52 - 1.0) * 100 if low52 > 0 else 0.0      # 正值

    # ── 综合 regime_score（-100..+100）──
    score = 0.0
    # 价格 vs MA：±35
    score += 35 if above_ma else -35
    # MA 斜率：±25（走平 0）
    score += 25 if ma_slope > 1e-5 else (-25 if ma_slope < -1e-5 else 0)
    # 回撤：回撤越小越偏多。0 回撤→+30；回撤≥40%→-30
    dd_score = (0.40 - min(dd, 0.40)) / 0.40 * 60 - 30   # 映射到 -30..+30
    score += dd_score
    # 距 52 周高：贴近高点(+10)，贴近低点(-10)
    if dist_high > -5:
        score += 10
    if dist_low < 5:
        score -= 10

    score = max(-100.0, min(100.0, score))

    # ── 三体制概率 ──
    # 以 score 为中心，牛市=score>0 的强度，熊市=score<0，震荡=中间
    bull = max(0.0, score) / 100.0
    bear = max(0.0, -score) / 100.0
    sideways = 1.0 - bull - bear
    # 归一（保证和为 1，且各有最低 0.05）
    raw = {"牛市": bull + 0.05, "熊市": bear + 0.05, "震荡": sideways + 0.10}
    tot = sum(raw.values())
    probs = {k: round(v / tot, 3) for k, v in raw.items()}

    if score > 25:
        regime = "牛市"
    elif score < -25:
        regime = "熊市"
    else:
        regime = "震荡"

    return {
        "regime": regime,
        "probability": probs[regime],
        "probabilities": probs,
        "regime_score": round(score, 1),
        "drawdown_from_high": round(dd, 4),
        "price_vs_ma200": price_vs,
        "ma200_slope": ma_slope_label,
        "ma200_slope_value": round(ma_slope, 6),
        "distance_52w_high": round(dist_high, 2),
        "distance_52w_low": round(dist_low, 2),
        "signals": {"above_ma": above_ma, "ma": round(ma, 2), "last": round(last, 2)},
        "note": f"基于MA{ma_n}+回撤+52周位置综合",
    }


def _neutral_result(note: str) -> Dict:
    return {
        "regime": "震荡", "probability": 0.34,
        "probabilities": {"牛市": 0.33, "熊市": 0.33, "震荡": 0.34},
        "regime_score": 0.0, "drawdown_from_high": 0.0,
        "price_vs_ma200": "数据不足", "ma200_slope": "未知",
        "distance_52w_high": 0.0, "distance_52w_low": 0.0,
        "signals": {}, "note": note,
    }


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class MarketRegimeClassifier:
    """市场体制分类器（统一牛熊判定的可信源）。"""

    def classify(self, code: str, days: int = 280) -> RegimeResult:
        """对指数/标的做体制分类。

        Args:
            code: 指数代码（sh000001 / 100.SPX 等）或股票代码
            days: 拉取历史天数（需 ≥ MA200 + 余量）
        """
        prices = self._fetch_prices(code, days)
        if not prices:
            return RegimeResult(code=code, note="行情获取失败")
        d = classify_from_prices(prices)
        return RegimeResult(
            code=code,
            regime=d["regime"],
            probability=d["probability"],
            probabilities=d["probabilities"],
            regime_score=d["regime_score"],
            drawdown_from_high=d["drawdown_from_high"],
            price_vs_ma200=d["price_vs_ma200"],
            ma200_slope=d["ma200_slope"],
            distance_52w_high=d["distance_52w_high"],
            distance_52w_low=d["distance_52w_low"],
            signals=d["signals"],
            note=d["note"],
        )

    def _fetch_prices(self, code: str, days: int) -> List[float]:
        """A 股指数/股票走腾讯日K；全球指数走 global kline。"""
        try:
            c = str(code).lower()
            if c.startswith(("100.", "idx:")) or c in ("100.spx", "100.hsi"):
                from stock_researcher.data.global_market import fetch_global_kline
                kl = fetch_global_kline(f"idx:{code}", days=days) or []
                return [float(k.get("close", 0)) for k in kl
                        if isinstance(k, dict) and k.get("close")]
            # A 股：sh/sz 前缀或纯数字
            from stock_researcher.data.market import MarketData
            md = MarketData()
            if c.startswith("sh") or c.startswith("sz"):
                prefix = c[:2]
                num = c[2:]
                k = md.fetch_history(num, days=days, prefix=prefix) or {}
            else:
                k = md.fetch_history(code, days=days) or {}
            return [float(p) for p in k.get("closes", []) if p is not None]
        except Exception:
            return []

    @staticmethod
    def format(r: RegimeResult) -> str:
        probs = " ".join(f"{k}:{v:.0%}" for k, v in r.probabilities.items())
        return (
            f"市场体制: {r.regime} (置信{r.probability:.0%}) | {probs}\n"
            f"  体制分{r.regime_score:+.0f} | 价格在MA200{r.price_vs_ma200} "
            f"(MA斜率{r.ma200_slope}) | 回撤{r.drawdown_from_high:.1%}\n"
            f"  距52周高{r.distance_52w_high:+.1f}% 距52周低{r.distance_52w_low:+.1f}%"
        )


def classify_market_regime(code: str) -> RegimeResult:
    """便捷函数：市场体制分类。"""
    return MarketRegimeClassifier().classify(code)
