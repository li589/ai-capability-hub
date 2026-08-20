#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三维预测引擎
Three-Dimension Prediction Engine
情绪面(25%) + 估值面(25%) + 历史案例(30%) + 技术面(20%)
"""

import math
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field


@dataclass
class InvestmentHorizon:
    """投资周期分析结果"""
    period: str = ""  # "短期(1-5日)"/"中期(20-60日)"/"长期(120+日)"
    period_days: int = 0

    score: float = 0  # -100 ~ +100
    signal: str = "中性"  # 强烈看多/看多/中性/看空/强烈看空
    confidence: float = 0.5  # 0 ~ 1

    # 预测值
    predicted_return: float = 0  # 预测涨跌幅%
    p10: float = 0  # 10%分位数
    p50: float = 0  # 中位数
    p90: float = 0  # 90%分位数

    # 蒙特卡洛
    prob_up: float = 50  # 上涨概率%
    prob_down: float = 50  # 下跌概率%

    # 因素
    key_factors: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class ThreeDimensionPrediction:
    """三维预测结果"""
    # 各维度评分
    sentiment_score: float = 0   # 情绪面
    valuation_score: float = 0   # 估值面
    historical_score: float = 0  # 历史案例
    technical_score: float = 0   # 技术面

    # 加权综合评分
    composite_score: float = 0

    # 最终信号
    final_signal: str = "中性"
    confidence: float = 0.5

    # 各周期预测
    short_term: InvestmentHorizon = None
    medium_term: InvestmentHorizon = None
    long_term: InvestmentHorizon = None

    def __post_init__(self):
        if self.short_term is None:
            self.short_term = InvestmentHorizon(period="短期(1-5日)", period_days=3)
        if self.medium_term is None:
            self.medium_term = InvestmentHorizon(period="中期(20-60日)", period_days=30)
        if self.long_term is None:
            self.long_term = InvestmentHorizon(period="长期(120+日)", period_days=120)


class ThreeDimensionPredictionEngine:
    """
    三维预测引擎

    权重分配（v7.0 优化：增强短期情绪和动量权重）：
    - 情绪面 (25%): 新闻舆情、资金流向、涨跌幅
    - 估值面 (25%): PE/PB历史分位、估值中枢、安全边际
    - 历史案例 (30%): 同类股票在相似估值/情绪下的走势
    - 技术面 (20%): 均线、MACD、RSI综合信号
    """

    WEIGHTS = {
        "sentiment": 0.25,
        "valuation": 0.25,
        "historical": 0.30,
        "technical": 0.20,
    }

    # v7.0 短期预测权重（1d/3d/5d 增强情绪+动量）
    SHORT_TERM_WEIGHTS = {
        "sentiment": 0.30,     # 情绪面：新闻+论坛情绪（增强）
        "technical": 0.25,     # 技术面：RSI+MACD+KDJ
        "historical": 0.25,    # 历史案例：近期动量
        "valuation": 0.20,     # 估值面：短期影响较小（减弱）
    }

    # 预测周期参数
    SHORT_DAYS = [1, 3, 5]
    MEDIUM_DAYS = [20, 30, 60]
    LONG_DAYS = [120, 180, 250]

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)
        # 不设固定种子，每次运行产生不同的蒙特卡洛模拟结果

    def predict(
        self,
        sentiment_score: float = 0,
        valuation_score: float = 0,
        historical_score: float = 0,
        technical_score: float = 0,
        prices: List[float] = None,
        returns: List[float] = None,
        sentiment_factors: Dict = None,
        valuation_factors: Dict = None,
        technical_factors: Dict = None
    ) -> ThreeDimensionPrediction:
        """
        执行三维预测

        Args:
            sentiment_score: 情绪面评分 (-100 ~ +100)
            valuation_score: 估值面评分 (-100 ~ +100)
            historical_score: 历史案例评分 (-100 ~ +100)
            technical_score: 技术面积分 (-100 ~ +100)
            prices: 历史价格序列（用于蒙特卡洛模拟）
            returns: 历史收益率序列
            sentiment_factors: 情绪面因素详情
            valuation_factors: 估值面因素详情
            technical_factors: 技术面因素详情

        Returns:
            ThreeDimensionPrediction: 三维预测结果
        """
        sentiment_factors = sentiment_factors or {}
        valuation_factors = valuation_factors or {}
        technical_factors = technical_factors or {}

        # 计算各维度得分
        s_score = max(-100, min(100, sentiment_score))
        v_score = max(-100, min(100, valuation_score))
        h_score = max(-100, min(100, historical_score))
        t_score = max(-100, min(100, technical_score))

        # 加权综合评分
        composite = (
            s_score * self.WEIGHTS["sentiment"] +
            v_score * self.WEIGHTS["valuation"] +
            h_score * self.WEIGHTS["historical"] +
            t_score * self.WEIGHTS["technical"]
        )

        # 综合评分归一化到 -100 ~ +100
        composite = max(-100, min(100, composite))

        # 生成最终信号
        final_signal = self._score_to_signal(composite)
        confidence = self._calc_confidence(composite, s_score, v_score, h_score, t_score)

        # 创建预测结果
        result = ThreeDimensionPrediction(
            sentiment_score=round(s_score, 1),
            valuation_score=round(v_score, 1),
            historical_score=round(h_score, 1),
            technical_score=round(t_score, 1),
            composite_score=round(composite, 1),
            final_signal=final_signal,
            confidence=round(confidence, 2)
        )

        # 如果有价格数据，执行蒙特卡洛模拟
        if prices and len(prices) >= 30:
            result = self._add_monte_carlo_predictions(result, prices, returns)

        # 生成各周期预测
        result = self._generate_horizon_predictions(result, s_score, v_score, h_score, t_score,
                                                    sentiment_factors, valuation_factors, technical_factors)

        return result

    def _score_to_signal(self, score: float) -> str:
        """根据评分生成信号"""
        if score > 60:
            return "强烈看多"
        elif score > 30:
            return "看多"
        elif score > -30:
            return "中性"
        elif score > -60:
            return "看空"
        else:
            return "强烈看空"

    def _calc_confidence(self, composite: float, s: float, v: float, h: float, t: float) -> float:
        """计算预测置信度"""
        # 各维度一致性
        scores = [abs(s), abs(v), abs(h), abs(t)]
        avg_signal = sum(scores) / len(scores)
        signal_consistency = min(1.0, avg_signal / 50)

        # 综合评分绝对值
        score_abs = abs(composite)

        # 置信度 = 信号一致性 * 0.5 + 评分强度 * 0.5
        confidence = signal_consistency * 0.5 + (score_abs / 100) * 0.5

        return min(0.95, max(0.3, confidence))

    def _add_monte_carlo_predictions(
        self,
        result: ThreeDimensionPrediction,
        prices: List[float],
        returns: List[float] = None
    ) -> ThreeDimensionPrediction:
        """添加蒙特卡洛模拟预测"""
        if returns is None:
            if len(prices) < 2:
                returns = []
            else:
                returns = [prices[i] / prices[i-1] - 1 for i in range(1, len(prices))]

        if len(returns) < 20:
            return result

        # 计算收益率统计
        mu = sum(returns) / len(returns)
        variance = sum((r - mu) ** 2 for r in returns) / len(returns)
        sigma = math.sqrt(variance) if variance > 0 else 0.1

        last_price = prices[-1]

        # v7.0: 计算动量调整因子（近期20日 vs 长期60日）
        momentum_adj = 0.0
        if len(returns) >= 60:
            recent_mu = sum(returns[-20:]) / 20 if len(returns) >= 20 else mu
            long_mu = sum(returns[-60:]) / 60
            momentum_adj = max(-1.0, min(1.0, (recent_mu - long_mu) / (sigma + 1e-12) * 2))
        elif len(returns) >= 20:
            recent_mu = sum(returns[-20:]) / 20
            if abs(mu) > 1e-12:
                momentum_adj = max(-1.0, min(1.0, (recent_mu - mu) / abs(mu) * 0.5))

        # 短期模拟 (500次)
        short_returns = self._simulate(sigma, mu, 3, 500, momentum_adj)
        result.short_term = self._create_horizon(
            "短期(1-5日)", 3,
            self._calc_score_from_simulation(short_returns, last_price),
            last_price, short_returns
        )

        # 中期模拟 (500次)
        medium_returns = self._simulate(sigma, mu, 30, 500, momentum_adj * 0.5)
        result.medium_term = self._create_horizon(
            "中期(20-60日)", 30,
            self._calc_score_from_simulation(medium_returns, last_price),
            last_price, medium_returns
        )

        # 长期模拟 (500次) — 动量影响减半
        long_returns = self._simulate(sigma, mu, 120, 500, momentum_adj * 0.2)
        result.long_term = self._create_horizon(
            "长期(120+日)", 120,
            self._calc_score_from_simulation(long_returns, last_price),
            last_price, long_returns
        )

        return result

    def _simulate(self, sigma: float, mu: float, days: int, sims: int,
                  momentum_adj: float = 0.0) -> List[float]:
        """蒙特卡洛模拟（v7.0: 支持动量调整因子）

        Args:
            sigma: 日波动率
            mu: 日均收益率
            days: 模拟天数
            sims: 模拟次数
            momentum_adj: 动量调整因子(-1~1)，短期增强信号敏感性
        """
        # v7.0: 信号驱动 μ 调整幅度从 0.25σ 扩大到 0.35σ
        adj = max(-0.35, min(0.35, momentum_adj * 0.35))
        mu_adj = mu + adj * sigma
        results = []
        for _ in range(sims):
            price = 1.0
            for _ in range(days):
                price *= (1 + random.gauss(mu_adj / 252, sigma))
            results.append(price - 1.0)  # 返回收益率
        return results

    def _calc_score_from_simulation(self, returns: List[float], last_price: float) -> float:
        """从模拟结果计算评分"""
        if not returns:
            return 0

        # 平均收益
        avg_return = sum(returns) / len(returns)

        # 上涨概率
        prob_up = sum(1 for r in returns if r > 0) / len(returns)

        # 综合评分：均值*50 + 上涨概率*50
        score = avg_return * 500 + prob_up * 50 - 50

        return max(-100, min(100, score))

    def _create_horizon(
        self,
        period: str,
        period_days: int,
        score: float,
        last_price: float,
        returns: List[float]
    ) -> InvestmentHorizon:
        """创建投资周期预测"""
        if not returns:
            return InvestmentHorizon(period=period, period_days=period_days)

        returns_sorted = sorted(returns)
        n = len(returns_sorted)

        p10 = returns_sorted[int(n * 0.1)]
        p50 = returns_sorted[n // 2]
        p90 = returns_sorted[int(n * 0.9)]

        prob_up = sum(1 for r in returns if r > 0) / len(returns) * 100
        prob_down = sum(1 for r in returns if r < 0) / len(returns) * 100

        predicted_return = sum(returns) / len(returns) * 100

        return InvestmentHorizon(
            period=period,
            period_days=period_days,
            score=round(score, 1),
            signal=self._score_to_signal(score),
            confidence=round(min(0.9, 0.5 + abs(score) / 200), 2),
            predicted_return=round(predicted_return, 2),
            p10=round(p10 * 100, 2),
            p50=round(p50 * 100, 2),
            p90=round(p90 * 100, 2),
            prob_up=round(prob_up, 1),
            prob_down=round(prob_down, 1)
        )

    def _generate_horizon_predictions(
        self,
        result: ThreeDimensionPrediction,
        s: float, v: float, h: float, t: float,
        sentiment_factors: Dict,
        valuation_factors: Dict,
        technical_factors: Dict
    ) -> ThreeDimensionPrediction:
        """生成各周期预测及建议"""

        # 短期预测因素
        short_factors = []
        if s > 30:
            short_factors.append("情绪面偏好")
        elif s < -30:
            short_factors.append("情绪面承压")

        if technical_factors.get("rsi"):
            if technical_factors["rsi"] < 30:
                short_factors.append("RSI超卖反弹")
            elif technical_factors["rsi"] > 70:
                short_factors.append("RSI超买回调")

        if technical_factors.get("macd_hist", 0) > 0:
            short_factors.append("MACD金叉")
        elif technical_factors.get("macd_hist", 0) < 0:
            short_factors.append("MACD死叉")

        result.short_term.key_factors = short_factors[:3]
        result.short_term.suggestion = self._generate_short_suggestion(result.short_term.score, short_factors)

        # 中期预测因素
        medium_factors = []
        if v > 20:
            medium_factors.append("估值偏低")
        elif v < -20:
            medium_factors.append("估值偏高")

        if technical_factors.get("ma_arrangement"):
            if technical_factors["ma_arrangement"] == "多头排列":
                medium_factors.append("均线多头")
            else:
                medium_factors.append("均线空头")

        result.medium_term.key_factors = medium_factors[:3]
        result.medium_term.suggestion = self._generate_medium_suggestion(result.medium_term.score, medium_factors)

        # 长期预测因素
        long_factors = []
        if h > 30:
            long_factors.append("历史同类走势强")
        elif h < -30:
            long_factors.append("历史同类走势弱")

        if valuation_factors.get("margin_of_safety"):
            ms = valuation_factors["margin_of_safety"]
            if ms > 20:
                long_factors.append(f"安全边际{ms:.0f}%")
            elif ms < -10:
                long_factors.append(f"溢价风险{-ms:.0f}%")

        result.long_term.key_factors = long_factors[:3]
        result.long_term.suggestion = self._generate_long_suggestion(result.long_term.score, long_factors)

        # 风险因素
        result.short_term.risk_factors = self._get_risk_factors(s, v, h, t, "short")
        result.medium_term.risk_factors = self._get_risk_factors(s, v, h, t, "medium")
        result.long_term.risk_factors = self._get_risk_factors(s, v, h, t, "long")

        return result

    def _get_risk_factors(self, s: float, v: float, h: float, t: float, period: str) -> List[str]:
        """获取风险因素"""
        risks = []

        if s > 70:
            risks.append("情绪过热可能回调")
        if s < -70:
            risks.append("情绪极度悲观")

        if v > 60:
            risks.append("估值偏高")
        if v < -60:
            risks.append("基本面可能恶化")

        if t < -40:
            risks.append("技术面走弱")
        if t > 40:
            risks.append("技术超买")

        if period == "short":
            if t < -20:
                risks.append("短期趋势向下")
        elif period == "medium":
            if v > 40:
                risks.append("中期估值压力")
        elif period == "long":
            if h < -20:
                risks.append("长期历史表现差")

        return risks[:3]

    def _generate_short_suggestion(self, score: float, factors: List[str]) -> str:
        """生成短期建议"""
        if score > 30:
            return "可适当参与，短线机会明确"
        elif score > 0:
            return "轻仓观望，等待确认信号"
        elif score > -30:
            return "谨慎操作，控制仓位"
        else:
            return "回避短期，等待底部确认"

    def _generate_medium_suggestion(self, score: float, factors: List[str]) -> str:
        """生成中期建议"""
        if score > 30:
            return "中期看好，可逢低布局"
        elif score > 0:
            return "中性偏多，择机配置"
        elif score > -30:
            return "谨慎对待，等待趋势明朗"
        else:
            return "中期承压，控制风险"

    def _generate_long_suggestion(self, score: float, factors: List[str]) -> str:
        """生成长期建议"""
        if score > 30:
            return "长期价值显现，适合定投"
        elif score > 0:
            return "长期布局，耐心持有"
        elif score > -30:
            return "长期中性，观望为主"
        else:
            return "长期谨慎，控制仓位"

    def predict_with_factors(
        self,
        news_sentiment: float = 0,    # 新闻情感 (-1 ~ 1)
        money_flow: float = 0,        # 资金流向 (-100 ~ +100)
        change_pct: float = 0,        # 当日涨跌幅 (-10 ~ +10)
        pe_percentile: float = 50,    # PE历史分位 (0-100)
        pb_percentile: float = 50,    # PB历史分位 (0-100)
        similar_returns: List[float] = None,  # 同类股票历史收益
        tech_score: float = 0,        # 技术综合评分 (-100 ~ +100)
        ma_status: str = "混乱",      # 均线状态
        rsi: float = 50,             # RSI值
        macd_hist: float = 0         # MACD柱
    ) -> ThreeDimensionPrediction:
        """
        使用因子直接预测（简化接口）

        Args:
            news_sentiment: 新闻情感 (-1 ~ 1, 正=利好)
            money_flow: 资金流向 (-100 ~ +100, 正=流入)
            change_pct: 当日涨跌幅 (-10 ~ +10)
            pe_percentile: PE历史分位 (0-100)
            pb_percentile: PB历史分位 (0-100)
            similar_returns: 同类股票历史收益率序列
            tech_score: 技术综合评分 (-100 ~ +100)
            ma_status: 均线状态
            rsi: RSI值
            macd_hist: MACD柱

        Returns:
            ThreeDimensionPrediction
        """
        # 情绪面评分
        sentiment_score = (
            news_sentiment * 30 +  # 新闻情感 * 30
            money_flow * 0.4 +     # 资金流向
            change_pct * 5         # 涨跌幅 * 5
        )

        # 估值面评分
        val_offset = 50 - (pe_percentile + pb_percentile) / 2
        valuation_score = val_offset * 1.2

        # 历史案例评分
        historical_score = 0
        if similar_returns:
            avg_return = sum(similar_returns) / len(similar_returns)
            historical_score = avg_return * 100

        # 技术面评分
        technical_score = tech_score

        return self.predict(
            sentiment_score=sentiment_score,
            valuation_score=valuation_score,
            historical_score=historical_score,
            technical_score=technical_score,
            sentiment_factors={
                "news_sentiment": news_sentiment,
                "money_flow": money_flow,
                "change_pct": change_pct
            },
            valuation_factors={
                "pe_percentile": pe_percentile,
                "pb_percentile": pb_percentile
            },
            technical_factors={
                "ma_status": ma_status,
                "rsi": rsi,
                "macd_hist": macd_hist
            }
        )