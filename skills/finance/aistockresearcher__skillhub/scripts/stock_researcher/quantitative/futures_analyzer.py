# -*- coding: utf-8 -*-
"""
期货量化分析模块 v2.0（v9.3 增强）
Futures Quantitative Analysis

功能：
  1. 主力合约连续价格分析
  2. 基差/升贴水结构分析
  3. 跨期套利信号
  4. 商品期货多因子（库存、开工率、季节性、资金流向）
  5. 期货趋势识别（ADX + 均线 + 波动率）
  6. v9.3 新增：波动率预测与置信区间预测、ATR 风险预算仓位建议、
     展期收益（roll yield）估算

支持品种：股指期货(IF/IC/IM)、国债期货(T/TF)、商品期货(螺纹钢/铁矿石/
          原油/沪铜/豆粕/PTA/黄金/白银等)

用法：
  from quantitative.futures_analyzer import FuturesAnalyzer
  fa = FuturesAnalyzer()
  result = fa.analyze_contract(prices, open_interest, basis_data)
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FuturesSignal:
    """期货分析信号"""
    symbol: str
    direction: str  # long / short / neutral
    strength: float  # 0~100
    trend: str  # trending / ranging
    volatility_regime: str  # low / normal / high
    basis_signal: str  # contango / backwardation / neutral
    spread_opportunity: bool
    entry_price: float
    stop_loss: float
    target_price: float
    risk_reward: float
    key_points: List[str] = field(default_factory=list)


class FuturesAnalyzer:
    """期货量化分析器

    核心因子：
      1. 价格趋势（ADX + 均线排列）
      2. 基差结构（Contango / Backwardation）
      3. 持仓量变化（资金流入流出）
      4. 波动率区间
      5. 跨期价差
    """

    def __init__(self):
        self._default_vol_window = 20

    def analyze_contract(self, symbol: str,
                         prices: List[float],
                         open_interest: List[float] = None,
                         spot_prices: List[float] = None,
                         volumes: List[float] = None) -> FuturesSignal:
        """综合期货合约分析。

        Args:
            symbol: 合约代码
            prices: 主力合约连续价格
            open_interest: 持仓量
            spot_prices: 现货价格（计算基差）
            volumes: 成交量
        """
        n = len(prices)
        if n < 20:
            return FuturesSignal(symbol, "neutral", 10, "unknown", "normal", "neutral",
                                 False, prices[-1], prices[-1], prices[-1], 0, ["数据不足"])

        current = prices[-1]
        vol = self._calc_volatility(prices)

        # 1. 趋势分析
        trend, trend_strength = self._trend_analysis(prices)

        # 2. 波动率区间
        vol_regime = self._vol_classify(vol)

        # 3. 基差分析
        basis_signal = "neutral"
        if spot_prices and len(spot_prices) >= 5:
            basis_signal = self._basis_analysis(spot_prices[-1], current)

        # 4. 持仓量分析
        oi_signal = 0
        if open_interest and len(open_interest) >= 5:
            oi_signal = self._oi_analysis(open_interest)

        # 5. 综合方向
        direction, strength = self._composite_direction(trend, trend_strength,
                                                        basis_signal, oi_signal)

        # 6. 风控设置
        atr = self._calc_atr(prices) if n >= 14 else current * 0.02
        stop_loss = current - atr * 2 if direction == "long" else current + atr * 2
        target = current + atr * 3 if direction == "long" else current - atr * 3
        rr = abs(target - current) / abs(stop_loss - current) if abs(stop_loss - current) > 0 else 0

        key_points = []
        if trend_strength > 50:
            key_points.append(f"{trend}趋势明确(强度{trend_strength:.0f})")
        if basis_signal == "backwardation":
            key_points.append("现货升水(Backwardation)")
        elif basis_signal == "contango":
            key_points.append("期货升水(Contango)")
        if vol_regime == "high":
            key_points.append(f"高波动率区间({vol*100:.1f}%)")
        if abs(oi_signal) > 0.05:
            key_points.append(f"持仓量{'增加' if oi_signal>0 else '减少'}({oi_signal*100:.1f}%)")

        return FuturesSignal(symbol, direction, round(strength, 1), trend,
                             vol_regime, basis_signal, False,
                             round(current, 2), round(stop_loss, 2),
                             round(target, 2), round(rr, 2), key_points)

    def _trend_analysis(self, prices: List[float]) -> Tuple[str, float]:
        """趋势分析：ADX + 均线"""
        n = len(prices)
        current = prices[-1]
        ma5 = sum(prices[-5:]) / 5
        ma20 = sum(prices[-20:]) / 20
        ma60 = sum(prices[-60:]) / 60 if n >= 60 else ma20

        # ADX 近似
        adx = self._calc_adx_approx(prices)

        # 方向
        if current > ma5 > ma20 > ma60:
            trend = "up"
        elif current < ma5 < ma20 < ma60:
            trend = "down"
        else:
            trend = "sideways"

        strength = adx * 100
        return trend, min(100, strength)

    def _calc_adx_approx(self, prices: List[float], period: int = 14) -> float:
        """近似 ADX 计算"""
        if len(prices) < period + 1:
            return 0.2
        trs, plus_dm, minus_dm = [], [], []
        for i in range(1, min(len(prices), period * 2 + 1)):
            h, l, prev_h, prev_l = prices[i], prices[i], prices[i - 1], prices[i - 1]
            tr = max(h - l, abs(h - prev_l), abs(l - prev_h))
            trs.append(tr)
            up = h - prev_h
            dn = prev_l - l
            plus_dm.append(up if up > 0 and up > dn else 0)
            minus_dm.append(dn if dn > 0 and dn > up else 0)

        atr = sum(trs[-period:]) / period
        pdi = sum(plus_dm[-period:]) / period / atr if atr > 0 else 0
        mdi = sum(minus_dm[-period:]) / period / atr if atr > 0 else 0
        dx = abs(pdi - mdi) / (pdi + mdi) if (pdi + mdi) > 0 else 0
        return dx

    def _calc_atr(self, prices: List[float], period: int = 14) -> float:
        """简化 ATR（使用收盘价近似）"""
        if len(prices) < period + 1:
            return prices[-1] * 0.02
        trs = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
        return sum(trs[-period:]) / period

    def _calc_volatility(self, prices: List[float]) -> float:
        """年化波动率"""
        if len(prices) < 5:
            return 0.2
        returns = [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]
        avg = sum(returns) / len(returns)
        variance = sum((r - avg) ** 2 for r in returns) / (len(returns) - 1)
        return math.sqrt(variance * 252)

    def _vol_classify(self, vol: float) -> str:
        if vol > 0.4:
            return "high"
        elif vol > 0.2:
            return "normal"
        return "low"

    def _basis_analysis(self, spot: float, futures: float) -> str:
        """基差分析"""
        basis_pct = (futures - spot) / spot
        if basis_pct > 0.02:
            return "contango"
        elif basis_pct < -0.02:
            return "backwardation"
        return "neutral"

    def _oi_analysis(self, oi: List[float]) -> float:
        """持仓量变化率"""
        if len(oi) < 2:
            return 0
        change = (oi[-1] - oi[0]) / oi[0]
        return max(-1, min(1, change * 10))

    def _composite_direction(self, trend: str, strength: float,
                             basis: str, oi_change: float) -> Tuple[str, float]:
        score = 0
        if trend == "up":
            score += strength * 0.6
        elif trend == "down":
            score -= strength * 0.6

        if basis == "backwardation":
            score += 10
        elif basis == "contango":
            score -= 10

        score += oi_change * 20

        direction = "long" if score > 10 else ("short" if score < -10 else "neutral")
        return direction, min(100, abs(score))

    def spread_analysis(self, near_prices: List[float],
                        far_prices: List[float]) -> Dict:
        """跨期价差分析"""
        if not near_prices or not far_prices:
            return {"signal": "data_insufficient"}

        n = min(len(near_prices), len(far_prices))
        spreads = [far_prices[i] - near_prices[i] for i in range(n)]
        current_spread = spreads[-1]
        avg_spread = sum(spreads) / n
        spread_std = (sum((s - avg_spread) ** 2 for s in spreads) / n) ** 0.5

        z = (current_spread - avg_spread) / spread_std if spread_std > 0 else 0

        signal = "neutral"
        if z > 2:
            signal = "short_spread"  # 价差过大，做空价差
        elif z < -2:
            signal = "long_spread"  # 价差过小，做多价差

        return {
            "current_spread": round(current_spread, 2),
            "avg_spread": round(avg_spread, 2),
            "z_score": round(z, 2),
            "signal": signal,
        }

    def predict_futures(self, symbol: str, prices: List[float],
                        horizon: str = "medium") -> Dict:
        """期货走势预测（v9.3：新增波动率置信区间 + 仓位建议 + 置信度）。"""
        signal = self.analyze_contract(symbol, prices)
        current = prices[-1]
        vol = self._calc_volatility(prices)

        days = {"short": 5, "medium": 20, "long": 60}.get(horizon, 20)
        drift = (signal.strength / 100 * 0.1 if signal.direction == "long"
                 else -signal.strength / 100 * 0.1)
        predicted = current * (1 + drift * days / 252)

        # v9.3：80% 波动率置信区间（±1.2816 σ√days）
        daily_vol = vol / math.sqrt(252)
        band = 1.2816 * daily_vol * math.sqrt(days)
        predicted_low = current * math.exp(math.log(predicted / current) - band)
        predicted_high = current * math.exp(math.log(predicted / current) + band)

        # v9.3：置信度 = 趋势强度 60% + 波动率体制 40%
        vol_score = {"low": 1.0, "normal": 0.6, "high": 0.3}.get(
            signal.volatility_regime, 0.5)
        confidence = round(signal.strength * 0.6 + vol_score * 40, 1)

        return {
            "symbol": symbol,
            "horizon": f"{days}日",
            "current": round(current, 2),
            "predicted": round(predicted, 2),
            "predicted_low": round(predicted_low, 2),      # v9.3
            "predicted_high": round(predicted_high, 2),    # v9.3
            "confidence": min(100.0, confidence),          # v9.3
            "direction": signal.direction,
            "strength": signal.strength,
            "volatility": round(vol * 100, 1),
            "trend": signal.trend,
            "basis_signal": signal.basis_signal,
            "position_suggestion": self.position_size(prices, signal.direction),  # v9.3
            "key_points": signal.key_points,
        }

    # ── v9.3 新增能力 ──────────────────────────────────
    def volatility_forecast(self, prices: List[float], horizon: int = 20) -> Dict:
        """波动率预测：近期已实现波动率 → 年化/区间期波动率估计。

        采用双窗口（20日 vs 60日）判断波动率趋势（扩张/压缩/平稳）。
        """
        horizon = max(1, int(horizon))
        if len(prices) < 25:
            return {"data_mode": "insufficient"}
        returns = [math.log(prices[i] / prices[i - 1])
                   for i in range(1, len(prices))]

        def _ann_vol(seg):
            if len(seg) < 2:
                return 0.0
            m = sum(seg) / len(seg)
            v = sum((r - m) ** 2 for r in seg) / (len(seg) - 1)
            return math.sqrt(v * 252)

        vol_20 = _ann_vol(returns[-20:])
        vol_60 = _ann_vol(returns[-60:]) if len(returns) >= 60 else vol_20
        if vol_60 > 0 and vol_20 / vol_60 > 1.2:
            vol_trend = "扩张"
        elif vol_60 > 0 and vol_20 / vol_60 < 0.8:
            vol_trend = "压缩"
        else:
            vol_trend = "平稳"
        period_vol = vol_20 * math.sqrt(horizon / 252)
        return {
            "data_mode": "ok",
            "annual_vol_pct": round(vol_20 * 100, 2),
            "long_annual_vol_pct": round(vol_60 * 100, 2),
            "vol_trend": vol_trend,
            "horizon_days": horizon,
            "period_vol_pct": round(period_vol * 100, 2),
        }

    def position_size(self, prices: List[float], direction: str,
                      risk_budget_pct: float = 2.0) -> Dict:
        """基于 ATR 的风险预算仓位建议（止损 = 2×ATR，单笔风险占资金 risk_budget_pct%）。"""
        if len(prices) < 14 or direction == "neutral":
            return {"position_pct": 0.0, "note": "无方向信号，建议空仓观望"}
        current = prices[-1]
        atr = self._calc_atr(prices)
        stop_dist = atr * 2
        risk_per_unit = stop_dist / current if current > 0 else 0.0
        if risk_per_unit <= 0:
            return {"position_pct": 0.0, "note": "ATR 异常，无法计算仓位"}
        pos = risk_budget_pct / 100 / risk_per_unit * 100
        pos = min(100.0, pos)
        return {
            "direction": direction,
            "position_pct": round(pos, 1),
            "stop_distance_pct": round(risk_per_unit * 100, 2),
            "risk_budget_pct": risk_budget_pct,
            "note": f"单笔风险{risk_budget_pct:.1f}%，止损 2×ATR 下的建议仓位",
        }

    def roll_yield_estimate(self, spot_prices: List[float],
                            futures_prices: List[float],
                            days_to_expiry: int = 30) -> Dict:
        """展期收益（roll yield）估算：期货向现货收敛带来的持有损益。

        升水（Contango）下多头展期为负收益，贴水（Backwardation）为正。
        """
        if (not spot_prices or not futures_prices
                or days_to_expiry <= 0):
            return {"data_mode": "insufficient"}
        basis_pct = (futures_prices[-1] - spot_prices[-1]) / spot_prices[-1]
        annualized = -basis_pct / days_to_expiry * 252
        structure = ("contango" if basis_pct > 0.005
                     else "backwardation" if basis_pct < -0.005 else "flat")
        return {
            "data_mode": "ok",
            "basis_pct": round(basis_pct * 100, 3),
            "structure": structure,
            "days_to_expiry": days_to_expiry,
            "roll_yield_annual_pct": round(annualized * 100, 2),
            "note": ("多头展期有利" if annualized > 0.01
                     else "多头展期不利" if annualized < -0.01 else "展期影响中性"),
        }


# ── 便捷函数 ──

def analyze_futures(symbol: str, prices: List[float],
                    **kwargs) -> Dict:
    """一步式期货分析。"""
    fa = FuturesAnalyzer()
    sig = fa.analyze_contract(symbol, prices, **kwargs)
    return {
        "symbol": sig.symbol, "direction": sig.direction,
        "strength": sig.strength, "trend": sig.trend,
        "volatility_regime": sig.volatility_regime,
        "entry": sig.entry_price, "stop_loss": sig.stop_loss,
        "target": sig.target_price, "risk_reward": sig.risk_reward,
        "key_points": sig.key_points,
    }


if __name__ == "__main__":
    import random
    random.seed(42)
    base = 3800
    prices = [base]
    for _ in range(99):
        prices.append(prices[-1] * (1 + random.gauss(0.0001, 0.01)))
    oi = [100000 + i * 100 + random.gauss(0, 2000) for i in range(100)]

    fa = FuturesAnalyzer()
    sig = fa.analyze_contract("IF9999", prices, open_interest=oi)
    print(f"Futures: {sig.symbol} dir={sig.direction} strength={sig.strength}")
    print(f"  trend={sig.trend} vol={sig.volatility_regime} basis={sig.basis_signal}")
    print(f"  risk_reward={sig.risk_reward} key={sig.key_points}")
