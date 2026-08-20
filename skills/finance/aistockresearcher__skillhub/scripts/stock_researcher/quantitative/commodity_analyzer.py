# -*- coding: utf-8 -*-
"""
商品/黄金量化分析模块 v1.0
Commodities & Gold Quantitative Analysis

功能：
  1. 黄金多因子定价模型（美元、利率、通胀、避险情绪、央行购金）
  2. 金银比 / 金油比 均值回归策略
  3. 黄金技术指标（RSI、MACD、布林带）
  4. 黄金短期/中期预测
  5. 商品跨品种相关性分析

数据源：东方财富贵金属 / 伦敦金 LBMA / COMEX 期货

用法：
  from quantitative.commodity_analyzer import GoldAnalyzer
  ga = GoldAnalyzer()
  result = ga.analyze_gold(gold_prices, usd_index, real_yields)
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class GoldSignal:
    """黄金分析信号"""
    direction: str  # bullish / bearish / neutral
    score: float  # -100 ~ 100
    factors: Dict[str, float]  # 各因子贡献
    target_price: float
    confidence: float  # 0~1
    key_drivers: List[str]


class GoldAnalyzer:
    """黄金量化分析器

    基于 5 因子定价模型：
      GOLD = f(USD, RealYield, Inflation, RiskSentiment, CBPurchase)
    """

    # 因子权重（可调参）
    DEFAULT_WEIGHTS = {
        "usd_index": -0.30,       # 美元走弱 → 金价涨
        "real_yield": -0.35,      # 实际利率下行 → 金价涨
        "inflation": 0.20,        # 通胀预期上升 → 金价涨
        "risk_sentiment": 0.10,   # 避险情绪高涨 → 金价涨
        "cb_purchase": 0.05,      # 央行购金 → 金价涨
    }

    # 关键支撑/阻力位
    SUPPORT_RESISTANCE = {
        "strong_support": 0.85,
        "support": 0.92,
        "resistance": 1.08,
        "strong_resistance": 1.15,
    }

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()
        self._normalize_weights()

    def _normalize_weights(self):
        total = sum(abs(w) for w in self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}

    def analyze_gold(self, gold_prices: List[float],
                     usd_index: List[float] = None,
                     real_yields: List[float] = None,
                     cpi: List[float] = None,
                     vix: List[float] = None,
                     cb_purchases: float = 0) -> GoldSignal:
        """综合黄金分析。

        Args:
            gold_prices: 黄金价格序列（日线，至少 20 条）
            usd_index: 美元指数序列
            real_yields: 美国实际利率（TIPS 收益率）
            cpi: CPI 同比序列
            vix: VIX 恐慌指数序列
            cb_purchases: 央行季度购金量（吨）
        """
        if not gold_prices or len(gold_prices) < 20:
            return GoldSignal("neutral", 0, {}, gold_prices[-1] if gold_prices else 0, 0, ["数据不足"])

        factors = {}
        drivers = []
        current = gold_prices[-1]
        ma20 = sum(gold_prices[-20:]) / 20
        ma60 = sum(gold_prices[-60:]) / 60 if len(gold_prices) >= 60 else ma20

        # 1. 价格趋势因子
        trend_score = self._trend_score(gold_prices)
        factors["trend"] = trend_score
        if trend_score > 0.3:
            drivers.append("价格趋势向上")
        elif trend_score < -0.3:
            drivers.append("价格趋势向下")

        # 2. 美元因子
        if usd_index and len(usd_index) >= 20:
            usd_score = self._usd_score(usd_index)
            factors["usd"] = usd_score * abs(self.weights["usd_index"])
            if usd_score > 0.2:
                drivers.append("美元走弱利好金价")
            elif usd_score < -0.2:
                drivers.append("美元走强压制金价")

        # 3. 实际利率因子
        if real_yields and len(real_yields) >= 20:
            yield_score = self._real_yield_score(real_yields)
            factors["real_yield"] = yield_score * abs(self.weights["real_yield"])
            if yield_score > 0.2:
                drivers.append("实际利率下行利好金价")

        # 4. 通胀因子
        if cpi and len(cpi) >= 3:
            cpi_score = self._inflation_score(cpi)
            factors["inflation"] = cpi_score * abs(self.weights["inflation"])
            if cpi_score > 0.15:
                drivers.append("通胀上行推动金价")

        # 5. 避险因子
        if vix and len(vix) >= 10:
            risk_score = self._risk_score(vix)
            factors["risk"] = risk_score * abs(self.weights["risk_sentiment"])
            if risk_score > 0.15:
                drivers.append("市场恐慌情绪助推避险需求")

        # 6. 央行购金因子
        if cb_purchases > 0:
            cb_score = min(cb_purchases / 500, 1.0)
            factors["cb_buying"] = cb_score * abs(self.weights["cb_purchase"])
            if cb_purchases > 100:
                drivers.append(f"央行持续购金({cb_purchases:.0f}吨)")

        # 综合评分
        total_score = sum(factors.values()) * 100
        total_score = max(-100, min(100, total_score))

        direction = "bullish" if total_score > 15 else ("bearish" if total_score < -15 else "neutral")
        target = current * (1 + total_score / 300)
        conf = min(abs(total_score) / 100 + 0.3, 1.0)

        return GoldSignal(direction, round(total_score, 1), factors,
                          round(target, 2), round(conf, 2), drivers[:5])

    def _trend_score(self, prices: List[float]) -> float:
        n = len(prices)
        ma5 = sum(prices[-5:]) / 5
        ma20 = sum(prices[-20:]) / 20
        ma60 = sum(prices[-60:]) / 60 if n >= 60 else ma20
        current = prices[-1]
        score = 0.0
        if current > ma5 > ma20:
            score += 0.4
        elif current < ma5 < ma20:
            score -= 0.4
        if ma20 > ma60:
            score += 0.3
        else:
            score -= 0.3
        # RSI
        rsi = self._calc_rsi(prices, 14)
        if 40 <= rsi <= 60:
            score += 0.1
        elif rsi > 70:
            score -= 0.2
        elif rsi < 30:
            score += 0.2
        return max(-1, min(1, score))

    def _usd_score(self, usd: List[float]) -> float:
        """美元走弱=利好金价，返回正值"""
        change = (usd[-1] - usd[-20]) / usd[-20]
        return -change * 5  # 美元每跌1%，金价因子+0.05

    def _real_yield_score(self, yields: List[float]) -> float:
        """实际利率下降=利好金价"""
        change = yields[-1] - yields[-20]
        return -change * 10

    def _inflation_score(self, cpi: List[float]) -> float:
        """通胀加速=利好金价"""
        avg_recent = sum(cpi[-3:]) / 3
        avg_prior = sum(cpi[-6:-3]) / 3 if len(cpi) >= 6 else avg_recent
        return (avg_recent - avg_prior) * 5

    def _risk_score(self, vix: List[float]) -> float:
        avg = sum(vix[-10:]) / 10
        if avg > 30:
            return 0.8
        elif avg > 25:
            return 0.5
        elif avg > 20:
            return 0.2
        else:
            return 0

    def _calc_rsi(self, prices: List[float], period: int = 14) -> float:
        if len(prices) < period + 1:
            return 50
        gains = [max(prices[i] - prices[i - 1], 0) for i in range(1, min(len(prices), period + 1))]
        losses = [abs(min(prices[i] - prices[i - 1], 0)) for i in range(1, min(len(prices), period + 1))]
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def gold_silver_ratio_strategy(self, gold_price: float, silver_price: float) -> Dict:
        """金银比均值回归策略。
        历史均值 ~70，极端值 >90 建议做多白银/做空黄金，<50 建议做多黄金/做空白银。
        """
        ratio = gold_price / silver_price if silver_price > 0 else 0
        mean = 70
        signal = "neutral"
        if ratio > 90:
            signal = "buy_silver_sell_gold"
        elif ratio > 80:
            signal = "consider_silver"
        elif ratio < 50:
            signal = "buy_gold_sell_silver"
        elif ratio < 60:
            signal = "consider_gold"
        z_score = (ratio - mean) / 15
        return {
            "gold_silver_ratio": round(ratio, 2),
            "historical_mean": mean,
            "z_score": round(z_score, 2),
            "signal": signal,
        }

    def gold_oil_ratio_strategy(self, gold_price: float, oil_price: float) -> Dict:
        """金油比分析。>30 经济衰退风险高，<15 经济过热。"""
        ratio = gold_price / oil_price if oil_price > 0 else 0
        signal = "neutral"
        if ratio > 30:
            signal = "recession_risk_high"
        elif ratio > 25:
            signal = "recession_warning"
        elif ratio < 15:
            signal = "overheating"
        elif ratio < 18:
            signal = "growth_strong"
        return {
            "gold_oil_ratio": round(ratio, 2),
            "signal": signal,
        }

    def predict_gold(self, gold_prices: List[float],
                     factors: Dict[str, List[float]] = None,
                     horizon: str = "medium") -> Dict:
        """预测黄金走势。

        Args:
            gold_prices: 历史金价
            factors: 多因子数据
            horizon: short(5日)/medium(20日)/long(60日)
        """
        if not gold_prices or len(gold_prices) < 20:
            return {"error": "数据不足"}

        current = gold_prices[-1]
        signal = self.analyze_gold(
            gold_prices,
            usd_index=factors.get("usd") if factors else None,
            real_yields=factors.get("yields") if factors else None,
            cpi=factors.get("cpi") if factors else None,
            vix=factors.get("vix") if factors else None,
        )

        days = {"short": 5, "medium": 20, "long": 60}.get(horizon, 20)
        vol = self._calc_volatility(gold_prices[-30:]) if len(gold_prices) >= 30 else 0.15
        drift = signal.score / 100 * 0.05  # 年化 drift

        # 简单蒙特卡洛
        predicted = current * (1 + drift * days / 252)
        p10 = predicted * (1 - 1.28 * vol * (days / 252) ** 0.5)
        p90 = predicted * (1 + 1.28 * vol * (days / 252) ** 0.5)

        return {
            "horizon": f"{days}日",
            "current": round(current, 2),
            "predicted": round(predicted, 2),
            "p10": round(p10, 2),
            "p50": round(predicted, 2),
            "p90": round(p90, 2),
            "volatility_30d": round(vol * 100, 1),
            "signal": signal.direction,
            "score": signal.score,
            "confidence": signal.confidence,
            "key_drivers": signal.key_drivers,
        }

    def _calc_volatility(self, prices: List[float]) -> float:
        if len(prices) < 2:
            return 0.15
        returns = [math.log(prices[i] / prices[i - 1]) for i in range(1, len(prices))]
        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
        return math.sqrt(variance * 252)


# ── 便捷函数 ──

def analyze_gold(gold_prices: List[float], **kwargs) -> Dict:
    """一步式黄金分析。"""
    ga = GoldAnalyzer()
    signal = ga.analyze_gold(gold_prices, **kwargs)
    return {
        "direction": signal.direction,
        "score": signal.score,
        "target_price": signal.target_price,
        "confidence": signal.confidence,
        "key_drivers": signal.key_drivers,
    }


if __name__ == "__main__":
    # 模拟数据测试
    import random
    random.seed(42)
    base = 2400
    prices = [base]
    for _ in range(119):
        prices.append(prices[-1] * (1 + random.gauss(0.0002, 0.008)))

    usd = [105 - i * 0.02 + random.gauss(0, 0.3) for i in range(120)]
    yields = [2.0 - i * 0.005 + random.gauss(0, 0.02) for i in range(120)]

    ga = GoldAnalyzer()
    signal = ga.analyze_gold(prices, usd_index=usd, real_yields=yields)
    print(f"Gold Signal: {signal.direction} score={signal.score} target={signal.target_price}")
    print(f"Drivers: {signal.key_drivers}")

    ratio = ga.gold_silver_ratio_strategy(prices[-1], 31.5)
    print(f"Au/Ag Ratio: {ratio}")
