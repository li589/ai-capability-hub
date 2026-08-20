#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术分析师 Agent
Technical Analyst Agent
均线系统/ADX/Hurst指数/均线排列综合分析
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import math


@dataclass
class TechnicalAgentResult:
    """技术分析师结果"""
    # 趋势
    trend: str = "震荡"  # 上升/下降/震荡
    trend_strength: float = 0  # 趋势强度 0-100

    # 均线系统
    ma_status: str = "混乱"  # 多头/空头/混乱
    ema_alignment: str = "混乱"

    # 动能指标
    adx: float = 0  # 趋势强度
    rsi: float = 50  # RSI
    momentum: float = 0  # 动能

    # Hurst指数
    hurst: float = 0.5  # <0.5均值回归, >0.5趋势

    # 综合评分
    tech_score: float = 0  # -100 ~ +100
    signal: str = "中性"


class TechnicalAgent:
    """
    技术分析师

    分析维度：
    1. 趋势跟踪 (25%): EMA排列、ADX趋势强度
    2. 均值回归 (20%): Z-score、布林带
    3. 动量 (25%): RSI、动量指标
    4. 波动率 (15%): ATR、波动率Z-score
    5. 统计套利 (15%): Hurst指数、偏度峰度
    """

    def analyze(
        self,
        prices: List[float],
        highs: List[float] = None,
        lows: List[float] = None,
        volumes: List[float] = None,
        lookback: int = 120
    ) -> TechnicalAgentResult:
        """
        执行技术分析

        Args:
            prices: 价格序列
            highs: 最高价序列
            lows: 最低价序列
            volumes: 成交量序列
            lookback: 回溯期

        Returns:
            TechnicalAgentResult
        """
        if len(prices) < 20:
            return TechnicalAgentResult()

        # 使用最近lookback个数据
        if len(prices) > lookback:
            prices = prices[-lookback:]
        if highs and len(highs) > lookback:
            highs = highs[-lookback:]
        if lows and len(lows) > lookback:
            lows = lows[-lookback:]

        if not highs:
            highs = prices
        if not lows:
            lows = prices

        # 1. 趋势分析 (25%)
        trend_score, trend_strength = self._analyze_trend(prices, highs, lows)

        # 2. 均值回归 (20%)
        reversion_score = self._analyze_mean_reversion(prices)

        # 3. 动量 (25%)
        momentum_score, rsi = self._analyze_momentum(prices)

        # 4. 波动率 (15%)
        volatility_score = self._analyze_volatility(prices, highs, lows)

        # 5. 统计套利 (15%)
        statistical_score, hurst = self._analyze_statistical(prices)

        # 综合评分
        total_score = (
            trend_score * 0.25 +
            reversion_score * 0.20 +
            momentum_score * 0.25 +
            volatility_score * 0.15 +
            statistical_score * 0.15
        )

        # 确定趋势
        if trend_strength > 70 and trend_score > 20:
            trend = "上升"
        elif trend_strength < 30 and trend_score < -20:
            trend = "下降"
        else:
            trend = "震荡"

        # 均线状态
        ma_status = self._check_ma_status(prices)

        return TechnicalAgentResult(
            trend=trend,
            trend_strength=round(trend_strength, 1),
            ma_status=ma_status,
            adx=round(self._calc_adx(prices, highs, lows), 1),
            rsi=round(rsi, 1),
            momentum=round(momentum_score, 1),
            hurst=round(hurst, 2),
            tech_score=round(total_score, 1),
            signal=self._get_signal(total_score)
        )

    def _analyze_trend(self, prices: List[float], highs: List[float], lows: List[float]) -> Tuple[float, float]:
        """趋势分析"""
        # EMA分析
        ema8 = self._calc_ema(prices, 8)
        ema21 = self._calc_ema(prices, 21)
        ema55 = self._calc_ema(prices, 55)

        score = 0
        if ema8 > ema21 > ema55:
            score = 30
        elif ema8 < ema21 < ema55:
            score = -30
        elif ema8 > ema21:
            score = 15
        elif ema8 < ema21:
            score = -15

        # ADX分析
        adx = self._calc_adx(prices, highs, lows)
        if adx > 25:
            score = score * 1.2 if score > 0 else score * 0.8
        elif adx < 15:
            score = score * 0.8

        # 趋势强度
        if ema8 > ema55:
            strength = min(100, (ema8 / ema55 - 1) * 500 + 50)
        else:
            strength = max(0, 100 - (ema55 / ema8 - 1) * 500)

        return score, strength

    def _analyze_mean_reversion(self, prices: List[float]) -> float:
        """均值回归分析"""
        if len(prices) < 20:
            return 0

        recent = prices[-20:]
        mean = sum(recent) / len(recent)
        variance = sum((p - mean) ** 2 for p in recent) / len(recent)
        std = variance ** 0.5

        if std == 0:
            return 0

        z_score = (prices[-1] - mean) / std

        # Z-score < -2 超卖, > 2 超买
        if z_score < -2:
            return 20  # 买入信号
        elif z_score > 2:
            return -20  # 卖出信号
        elif z_score < -1:
            return 10
        elif z_score > 1:
            return -10
        else:
            return 0

    def _analyze_momentum(self, prices: List[float]) -> Tuple[float, float]:
        """动量分析"""
        if len(prices) < 14:
            return 0, 50

        # RSI
        rsi = self._calc_rsi(prices, 14)

        # 动量
        if len(prices) >= 20:
            momentum_1m = (prices[-1] / prices[-20] - 1) * 100
        else:
            momentum_1m = 0

        if len(prices) >= 60:
            momentum_3m = (prices[-1] / prices[-60] - 1) * 100
        else:
            momentum_3m = momentum_1m

        # 综合动量评分
        momentum = momentum_1m * 0.6 + momentum_3m * 0.4

        score = 0
        if rsi < 30:
            score += 15
        elif rsi > 70:
            score -= 15
        else:
            score += (rsi - 50) * 0.3

        if momentum > 10:
            score += 10
        elif momentum > 5:
            score += 5
        elif momentum < -10:
            score -= 10
        elif momentum < -5:
            score -= 5

        return score, rsi

    def _analyze_volatility(self, prices: List[float], highs: List[float], lows: List[float]) -> float:
        """波动率分析"""
        if len(prices) < 14:
            return 0

        # ATR
        atr = self._calc_atr(prices, highs, lows, 14)
        current_price = prices[-1]

        if current_price > 0:
            atr_ratio = atr / current_price * 100
        else:
            atr_ratio = 0

        # ATR比率评分
        if atr_ratio < 2:
            return 10  # 低波动，可能突破
        elif atr_ratio > 5:
            return -10  # 高波动
        else:
            return 0

    def _analyze_statistical(self, prices: List[float]) -> Tuple[float, float]:
        """统计套利分析 - Hurst指数"""
        if len(prices) < 50:
            return 0, 0.5

        # 计算收益率
        returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]

        # Hurst指数
        hurst = self._calc_hurst(returns)

        score = 0
        if hurst > 0.6:
            score = 15  # 趋势延续
        elif hurst < 0.4:
            score = -15  # 均值回归
        else:
            score = 0

        return score, hurst

    def _calc_ema(self, prices: List[float], period: int) -> float:
        """计算EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        k = 2.0 / (period + 1)
        ema = sum(prices[:period]) / period
        for v in prices[period:]:
            ema = v * k + ema * (1 - k)
        return ema

    def _calc_rsi(self, prices: List[float], period: int = 14) -> float:
        """计算RSI"""
        if len(prices) < period + 1:
            return 50

        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i - 1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))

        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    def _calc_adx(self, prices: List[float], highs: List[float], lows: List[float], period: int = 14) -> float:
        """计算ADX"""
        if len(prices) < period + 1:
            return 0

        tr_list = []
        plus_dm_list = []
        minus_dm_list = []

        for i in range(1, len(prices)):
            high = highs[i] if i < len(highs) else prices[i]
            low = lows[i] if i < len(lows) else prices[i]
            prev_high = highs[i-1] if i-1 < len(highs) else prices[i-1]
            prev_low = lows[i-1] if i-1 < len(lows) else prices[i-1]
            prev_close = prices[i-1]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)

            plus_dm = max(high - prev_high, 0) if max(high - prev_high, 0) > max(prev_low - low, 0) else 0
            minus_dm = max(prev_low - low, 0) if max(prev_low - low, 0) > max(high - prev_high, 0) else 0

            plus_dm_list.append(plus_dm)
            minus_dm_list.append(minus_dm)

        if len(tr_list) < period:
            return 0

        # 计算ATR
        atr = sum(tr_list[-period:]) / period
        if atr == 0:
            return 0

        plus_di = sum(plus_dm_list[-period:]) / period / atr * 100
        minus_di = sum(minus_dm_list[-period:]) / period / atr * 100

        di_sum = plus_di + minus_di
        if di_sum == 0:
            return 0

        dx = abs(plus_di - minus_di) / di_sum * 100
        return dx

    def _calc_atr(self, prices: List[float], highs: List[float], lows: List[float], period: int = 14) -> float:
        """计算ATR"""
        if len(prices) < period + 1:
            return 0

        tr_list = []
        for i in range(1, len(prices)):
            high = highs[i] if i < len(highs) else prices[i]
            low = lows[i] if i < len(lows) else prices[i]
            prev_close = prices[i-1]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_list.append(tr)

        if len(tr_list) < period:
            return 0

        return sum(tr_list[-period:]) / period

    def _calc_hurst(self, returns: List[float], min_n: int = 10) -> float:
        """计算Hurst指数"""
        if len(returns) < min_n * 2:
            return 0.5

        def range_over_std(n):
            if n > len(returns):
                return 1
            subseries = [returns[i:i+n] for i in range(0, len(returns), n)]
            if len(subseries) < 2:
                return 1

            ranges = []
            for sub in subseries:
                if len(sub) < 2:
                    continue
                mean = sum(sub) / len(sub)
                cumsum = [0]
                for v in sub:
                    cumsum.append(cumsum[-1] + v - mean)
                r = max(cumsum) - min(cumsum)
                s = math.sqrt(sum((v - mean)**2 for v in sub) / len(sub)) if len(sub) > 1 else 1
                ranges.append(r / s if s > 0 else 1)

            return sum(ranges) / len(ranges) if ranges else 1

        # 计算不同窗口的R/S
        log_n = []
        log_rs = []

        for n_size in [5, 10, 20, min(50, len(returns)//2)]:
            if n_size <= len(returns) and n_size >= min_n:
                rs = range_over_std(n_size)
                log_n.append(math.log(n_size))
                log_rs.append(math.log(rs) if rs > 0 else 0)

        if len(log_n) < 2:
            return 0.5

        # 线性回归
        n_mean = sum(log_n) / len(log_n)
        rs_mean = sum(log_rs) / len(log_rs)

        numerator = sum((x - n_mean) * (y - rs_mean) for x, y in zip(log_n, log_rs))
        denominator = sum((x - n_mean)**2 for x in log_n)

        if denominator == 0:
            return 0.5

        hurst = numerator / denominator
        return max(0, min(1, hurst))

    def _check_ma_status(self, prices: List[float]) -> str:
        """检查均线状态"""
        if len(prices) < 60:
            return "数据不足"

        ma5 = sum(prices[-5:]) / 5
        ma10 = sum(prices[-10:]) / 10
        ma20 = sum(prices[-20:]) / 20
        ma60 = sum(prices[-60:]) / 60

        if ma5 > ma10 > ma20 > ma60:
            return "多头排列"
        elif ma5 < ma10 < ma20 < ma60:
            return "空头排列"
        else:
            return "混乱"

    @staticmethod
    def _get_signal(score: float) -> str:
        """生成信号"""
        if score > 30:
            return "买入"
        elif score < -30:
            return "卖出"
        else:
            return "中性"

    def get_trading_advice(self, result: TechnicalAgentResult) -> Dict:
        """获取交易建议"""
        advice = {
            "signal": result.signal,
            "trend": result.trend,
            "key_indicators": {
                "adx": result.adx,
                "rsi": result.rsi,
                "ma_status": result.ma_status,
                "hurst": result.hurst
            }
        }

        if result.signal == "买入":
            advice["action"] = "技术面积极，可考虑买入"
            if result.hurst > 0.6:
                advice["action"] += "（趋势延续型，注意止损）"
        elif result.signal == "卖出":
            advice["action"] = "技术面走弱，建议减仓或观望"
        else:
            advice["action"] = "技术面中性，等待明确信号"

        return advice