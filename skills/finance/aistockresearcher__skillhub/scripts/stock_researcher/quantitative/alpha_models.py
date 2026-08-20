# -*- coding: utf-8 -*-
"""
Alpha模型 - 信号生成模型
Alpha Models - Signal Generation Models

基于 QuantConnect Lean AlphaFramework 架构

参考模型：
- DualThrustAlpha: 双thrust突破策略
- RateOfChangeAlpha: 动量策略
- MeanReversionAlpha: 均值回归策略
- MomentumAlpha: 趋势跟踪策略
- ValueInvestingAlpha: 格林布拉特神奇公式
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class InsightDirection(Enum):
    """交易方向"""
    UP = 1
    DOWN = -1
    FLAT = 0


@dataclass
class Insight:
    """
    信号/洞察
    代表对某个证券的预测信号
    """
    symbol: str
    direction: InsightDirection  # UP/DOWN/FLAT
    confidence: float = 0.5     # 置信度 0-1
    magnitude: float = 0        # 预测幅度 %
    period: int = 5             # 预测周期（天）
    generated_at: str = ""      # 生成时间
    model_name: str = ""        # 模型名称
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.direction, int):
            self.direction = InsightDirection(self.direction)


class AlphaModel:
    """Alpha模型基类"""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__

    def update(self, symbol: str, data: Dict) -> Optional[Insight]:
        """
        基于最新数据更新信号

        Args:
            symbol: 股票代码
            data: 包含OHLCV等数据的字典

        Returns:
            Insight: 信号对象，无信号时返回None
        """
        raise NotImplementedError

    def batch_update(self, symbols: List[str], data_map: Dict[str, Dict]) -> List[Insight]:
        """
        批量更新多个证券的信号

        Args:
            symbols: 股票代码列表
            data_map: {symbol: data} 数据映射

        Returns:
            List[Insight]: 信号列表
        """
        insights = []
        for symbol in symbols:
            data = data_map.get(symbol)
            if data:
                insight = self.update(symbol, data)
                if insight:
                    insights.append(insight)
        return insights


class DualThrustAlpha(AlphaModel):
    """
    双Thrust Alpha模型

    策略原理：
    - 计算过去N日的Range = max(HH-LC, HC-LL)（不含当日）
      其中 HH=最高价, LC=最低收盘价, HC=最高收盘价, LL=最低价
    - 上轨 = 当日开盘价 + K1 * Range
    - 下轨 = 当日开盘价 - K2 * Range
    - 价格突破上轨买入，跌破下轨卖出

    适用于：A股个股、指数日内策略

    参数：
    - k1, k2: 系数（默认0.5-0.7）
    - period: 计算窗口（默认20日）
    """

    def __init__(self, k1: float = 0.63, k2: float = 0.63, period: int = 20, name: str = ""):
        super().__init__(name or "DualThrust")
        self.k1 = k1
        self.k2 = k2
        self.period = period
        self._history: Dict[str, List[Dict]] = {}

    def update(self, symbol: str, data: Dict) -> Optional[Insight]:
        """更新信号"""
        if symbol not in self._history:
            self._history[symbol] = []

        self._history[symbol].append(data)

        # 需要 period 根历史 + 当日共 period+1 根
        if len(self._history[symbol]) < self.period + 1:
            return None

        # 保留最近 period+1 条数据，并使用裁剪后的窗口
        if len(self._history[symbol]) > self.period + 1:
            self._history[symbol] = self._history[symbol][-(self.period + 1):]

        history = self._history[symbol]

        # 计算Range：用前 period 根K线（不含当日），
        # 避免当日极值膨胀区间后再用当日收盘价自我判定突破
        past = history[:-1]
        highs = [h.get('high', 0) for h in past]
        lows = [h.get('low', 0) for h in past]
        closes = [h.get('close', 0) for h in past]

        hh = max(highs)
        lc = min(closes)
        hc = max(closes)
        ll = min(lows)

        range_val = max(hh - lc, hc - ll)

        current_price = data.get('close', 0)
        # 突破基准锚定当日开盘价（经典 DualThrust 定义）。
        # 修复：原实现锚定当日收盘价，current > current + k1*Range
        # 数学上永不成立，模型永远不会产生任何信号
        base = data.get('open', 0) or current_price
        upper_line = base + self.k1 * range_val
        lower_line = base - self.k2 * range_val

        prev_close = closes[-1] if closes else current_price

        insight = None

        # 买入条件：当日价格上穿上轨（前一收盘尚未突破，即当日新上穿）
        if current_price > upper_line and prev_close <= upper_line:
            magnitude = (current_price - upper_line) / upper_line * 100
            insight = Insight(
                symbol=symbol,
                direction=InsightDirection.UP,
                confidence=0.6,
                magnitude=abs(magnitude),
                period=5,
                model_name=self.name,
                metadata={
                    'upper_line': upper_line,
                    'lower_line': lower_line,
                    'range': range_val,
                    'breakout': 'upper'
                }
            )

        # 卖出条件：当日价格下穿下轨（前一收盘尚未跌破）
        elif current_price < lower_line and prev_close >= lower_line:
            magnitude = (lower_line - current_price) / lower_line * 100
            insight = Insight(
                symbol=symbol,
                direction=InsightDirection.DOWN,
                confidence=0.6,
                magnitude=abs(magnitude),
                period=5,
                model_name=self.name,
                metadata={
                    'upper_line': upper_line,
                    'lower_line': lower_line,
                    'range': range_val,
                    'breakout': 'lower'
                }
            )

        return insight


class RateOfChangeAlpha(AlphaModel):
    """
    变动率Alpha模型 (ROC)

    策略原理：
    - ROC = (当前价格 - N日前价格) / N日前价格 * 100
    - ROC > 0 表示动量向上
    - ROC < 0 表示动量向下

    适用于：短线动量/反转策略

    参数：
    - period: 回看周期（默认10日）
    - threshold: 触发阈值（默认5%）
    """

    def __init__(self, period: int = 10, threshold: float = 5.0, name: str = ""):
        super().__init__(name or f"ROC({period})")
        self.period = period
        self.threshold = threshold
        self._history: Dict[str, List[float]] = {}

    def update(self, symbol: str, data: Dict) -> Optional[Insight]:
        """更新信号"""
        if symbol not in self._history:
            self._history[symbol] = []

        close = data.get('close', 0)
        if close <= 0:
            return None

        self._history[symbol].append(close)

        if len(self._history[symbol]) < self.period + 1:
            return None

        # 保留足够的历史数据
        if len(self._history[symbol]) > self.period + 5:
            self._history[symbol] = self._history[symbol][-(self.period+1):]

        current_price = self._history[symbol][-1]
        past_price = self._history[symbol][-(self.period + 1)]

        if past_price <= 0:
            return None

        roc = (current_price - past_price) / past_price * 100

        # 判断信号
        if abs(roc) < self.threshold:
            return None

        direction = InsightDirection.UP if roc > 0 else InsightDirection.DOWN
        magnitude = abs(roc)

        return Insight(
            symbol=symbol,
            direction=direction,
            confidence=min(0.9, magnitude / 20),
            magnitude=magnitude,
            period=self.period // 2,
            model_name=self.name,
            metadata={'roc': roc, 'period': self.period}
        )


class MeanReversionAlpha(AlphaModel):
    """
    均值回归Alpha模型

    策略原理：
    - 计算过去N日均值和标准差
    - 当价格偏离均值超过K个标准差时，预期回归
    - 布林带配合RSI使用效果更佳

    适用于：震荡市、高波动股

    参数：
    - period: 计算窗口（默认20日）
    - std_threshold: 标准差倍数（默认2.0）
    """

    def __init__(self, period: int = 20, std_threshold: float = 2.0, name: str = ""):
        super().__init__(name or "MeanReversion")
        self.period = period
        self.std_threshold = std_threshold
        self._history: Dict[str, List[float]] = {}

    def update(self, symbol: str, data: Dict) -> Optional[Insight]:
        """更新信号"""
        if symbol not in self._history:
            self._history[symbol] = []

        close = data.get('close', 0)
        if close <= 0:
            return None

        self._history[symbol].append(close)

        if len(self._history[symbol]) < self.period:
            return None

        if len(self._history[symbol]) > self.period + 10:
            self._history[symbol] = self._history[symbol][-(self.period+1):]

        prices = self._history[symbol][-self.period:]
        current_price = prices[-1]

        # 计算均值和标准差
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std = math.sqrt(variance)

        if std <= 0:
            return None

        # 计算偏离
        deviation = (current_price - mean) / std

        insight = None

        # 价格严重低于均值（可能反弹）
        if deviation < -self.std_threshold:
            insight = Insight(
                symbol=symbol,
                direction=InsightDirection.UP,
                confidence=min(0.85, abs(deviation) / 4),
                magnitude=abs(deviation) * 3,
                period=5,
                model_name=self.name,
                metadata={'deviation': deviation, 'mean': mean, 'std': std}
            )

        # 价格严重高于均值（可能回落）
        elif deviation > self.std_threshold:
            insight = Insight(
                symbol=symbol,
                direction=InsightDirection.DOWN,
                confidence=min(0.85, abs(deviation) / 4),
                magnitude=abs(deviation) * 3,
                period=5,
                model_name=self.name,
                metadata={'deviation': deviation, 'mean': mean, 'std': std}
            )

        return insight


class MomentumAlpha(AlphaModel):
    """
    动量Alpha模型

    策略原理：
    - 使用EMA计算趋势方向
    - 多周期EMA交叉产生信号
    - 短周期上穿长周期买入，反之卖出

    适用于：趋势明显的个股

    参数：
    - fast_period: 快线周期（默认5日）
    - slow_period: 慢线周期（默认20日）
    """

    def __init__(self, fast_period: int = 5, slow_period: int = 20, name: str = ""):
        super().__init__(name or "Momentum")
        self.fast_period = fast_period
        self.slow_period = slow_period
        self._ema_fast: Dict[str, List[float]] = {}
        self._ema_slow: Dict[str, List[float]] = {}

    def _calc_ema(self, prices: List[float], period: int) -> float:
        """计算EMA"""
        if len(prices) < period:
            return 0
        k = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = price * k + ema * (1 - k)
        return ema

    def update(self, symbol: str, data: Dict) -> Optional[Insight]:
        """更新信号"""
        close = data.get('close', 0)
        if close <= 0:
            return None

        if symbol not in self._ema_fast:
            self._ema_fast[symbol] = []
            self._ema_slow[symbol] = []

        self._ema_fast[symbol].append(close)
        self._ema_slow[symbol].append(close)

        max_len = max(self.slow_period + 5, self.fast_period + 5)
        if len(self._ema_fast[symbol]) > max_len:
            self._ema_fast[symbol] = self._ema_fast[symbol][-max_len:]
            self._ema_slow[symbol] = self._ema_slow[symbol][-max_len:]

        if len(self._ema_fast[symbol]) < self.slow_period:
            return None

        fast_ema = self._calc_ema(self._ema_fast[symbol], self.fast_period)
        slow_ema = self._calc_ema(self._ema_slow[symbol], self.slow_period)

        prev_fast = self._calc_ema(self._ema_fast[symbol][-self.fast_period-1:-1], self.fast_period) \
            if len(self._ema_fast[symbol]) > self.fast_period else fast_ema
        prev_slow = self._calc_ema(self._ema_slow[symbol][-self.slow_period-1:-1], self.slow_period) \
            if len(self._ema_slow[symbol]) > self.slow_period else slow_ema

        insight = None

        # 金叉买入
        if fast_ema > slow_ema and prev_fast <= prev_slow:
            diff = (fast_ema - slow_ema) / slow_ema * 100
            insight = Insight(
                symbol=symbol,
                direction=InsightDirection.UP,
                confidence=min(0.85, diff * 5),
                magnitude=diff * 2,
                period=10,
                model_name=self.name,
                metadata={'fast_ema': fast_ema, 'slow_ema': slow_ema, 'cross': 'golden'}
            )

        # 死叉卖出
        elif fast_ema < slow_ema and prev_fast >= prev_slow:
            diff = (slow_ema - fast_ema) / slow_ema * 100
            insight = Insight(
                symbol=symbol,
                direction=InsightDirection.DOWN,
                confidence=min(0.85, diff * 5),
                magnitude=diff * 2,
                period=10,
                model_name=self.name,
                metadata={'fast_ema': fast_ema, 'slow_ema': slow_ema, 'cross': 'death'}
            )

        return insight


class ValueInvestingAlpha(AlphaModel):
    """
    价值投资Alpha模型（格林布拉特神奇公式简化版）

    策略原理（实际实现）：
    - PE 越低的股票越便宜（价值分）
    - ROE 越高的股票盈利能力越强（质量分）
    - 综合评分选择最佳价值股

    适用于：价值投资、长线持有

    参数：
    - pe_max: PE上限（默认50）
    - roa_min: ROE下限（默认5%）。历史参数名，实际过滤的是 ROE；
      也可用 roe_min 显式指定（优先级更高）
    """

    def __init__(self, pe_max: float = 50, roa_min: float = 5.0,
                 roe_min: float = None, name: str = ""):
        super().__init__(name or "ValueInvesting")
        self.pe_max = pe_max
        # roa_min 为历史命名，统一归一到 roe_min 语义
        self.roe_min = roe_min if roe_min is not None else roa_min
        self.roa_min = self.roe_min  # 向后兼容：保留旧属性名

    def update(self, symbol: str, data: Dict) -> Optional[Insight]:
        """
        更新信号（v5.0 升级：集成 moat + financial_health 评分）
        需要传入财务数据：pe, pb, roe, earnings_growth 等
        可选传入：moat_score, health_score（来自 value_investing 模块的预计算值）
        """
        pe = data.get('pe', 0)
        pb = data.get('pb', 0)
        roe = data.get('roe', 0)  # 净资产收益率 %
        earnings_growth = data.get('earnings_growth', 0)  # 盈利增长 %
        # v5.0 新增：预计算的护城河/财务健康评分（来自 value_investing 模块）
        moat_score = data.get('moat_score', 0)
        health_score = data.get('health_score', 0)

        if pe <= 0 or pe > self.pe_max:
            return None

        # 价值维度：PE 越低越好（保留原逻辑）
        value_score = max(0, 100 - (pe / self.pe_max * 100))

        # v5.0 升级：质量维度优先使用 moat + financial_health
        if moat_score > 0 and health_score > 0:
            # 有预计算值时，用 moat × 0.5 + health × 0.3 + ROE × 0.2
            quality_score = (moat_score * 0.5 + health_score * 0.3 +
                             min(100, roe * 5) * 0.2) if roe > 0 else \
                            (moat_score * 0.6 + health_score * 0.4)
            # v5.0 新公式：value 30% + moat 40% + health 30%
            composite_score = value_score * 0.3 + quality_score * 0.7
        else:
            # 无预计算值时，退回原逻辑（PE 60% + ROE 40%）
            quality_score = min(100, roe * 5) if roe > 0 else 0
            composite_score = value_score * 0.6 + quality_score * 0.4

        # v5.0: 阈值从 40 提升到 50（有 moat/health 时要求更高，避免弱信号）
        threshold = 50 if (moat_score > 0 or health_score > 0) else 40
        if composite_score < threshold:
            return None

        # 基于评分的置信度
        confidence = composite_score / 100 * 0.8

        # 预测幅度 - 价值股通常预期收益10-30%
        magnitude = composite_score * 0.3

        return Insight(
            symbol=symbol,
            direction=InsightDirection.UP,
            confidence=confidence,
            magnitude=magnitude,
            period=60,  # 价值投资周期较长
            model_name=self.name,
            metadata={
                'value_score': value_score,
                'quality_score': quality_score,
                'composite_score': composite_score,
                'pe': pe,
                'pb': pb,
                'roe': roe,
                'moat_score': moat_score,
                'health_score': health_score,
            }
        )

    def batch_update_with_fundamentals(
        self,
        stock_data_list: List[Dict]
    ) -> List[Insight]:
        """
        批量更新价值投资信号

        Args:
            stock_data_list: 包含财务数据的股票列表
            [{
                'symbol': '600519',
                'name': '贵州茅台',
                'pe': 30.5,
                'pb': 12.3,
                'roe': 25.6,
                'earnings_growth': 15.2
            }, ...]

        Returns:
            List[Insight]: 按综合评分排序的买入信号
        """
        scored_stocks = []

        for stock in stock_data_list:
            symbol = stock.get('symbol', '')
            pe = stock.get('pe', 0)
            roe = stock.get('roe', 0)

            if pe <= 0 or pe > self.pe_max or roe < self.roa_min:
                continue

            value_score = max(0, 100 - (pe / self.pe_max * 100))
            quality_score = min(100, roe * 5) if roe > 0 else 0
            composite_score = value_score * 0.6 + quality_score * 0.4

            scored_stocks.append({
                'symbol': symbol,
                'name': stock.get('name', symbol),
                'composite_score': composite_score,
                'value_score': value_score,
                'quality_score': quality_score,
                'pe': pe,
                'roe': roe
            })

        # 按综合评分排序
        scored_stocks.sort(key=lambda x: x['composite_score'], reverse=True)

        insights = []
        for i, stock in enumerate(scored_stocks[:20]):  # 取前20只
            confidence = stock['composite_score'] / 100 * 0.8
            magnitude = stock['composite_score'] * 0.3

            insights.append(Insight(
                symbol=stock['symbol'],
                direction=InsightDirection.UP,
                confidence=confidence,
                magnitude=magnitude,
                period=60,
                model_name=self.name,
                metadata={
                    'rank': i + 1,
                    'name': stock['name'],
                    'value_score': stock['value_score'],
                    'quality_score': stock['quality_score'],
                    'pe': stock['pe'],
                    'roe': stock['roe']
                }
            ))

        return insights


def create_alpha_model(model_type: str, **kwargs) -> AlphaModel:
    """
    工厂函数：创建Alpha模型

    Args:
        model_type: 模型类型
            - 'dual_thrust': 双Thrust策略
            - 'roc': 变动率策略
            - 'mean_reversion': 均值回归策略
            - 'momentum': 动量策略
            - 'value': 价值投资策略

    Returns:
        AlphaModel: 实例化的模型
    """
    models = {
        'dual_thrust': DualThrustAlpha,
        'roc': RateOfChangeAlpha,
        'mean_reversion': MeanReversionAlpha,
        'momentum': MomentumAlpha,
        'value': ValueInvestingAlpha,
    }

    model_class = models.get(model_type.lower())
    if not model_class:
        raise ValueError(f"Unknown model type: {model_type}")

    return model_class(**kwargs)


# ============================================================
# v3.1.0 增量 — Alpha 信号横截面稳健性
# ============================================================

def _cross_section_demean(values):
    """横截面去均值（按天）— 用于去除市场共性 beta。"""
    import numpy as _np
    arr = _np.array(values, dtype=float)
    return arr - _np.nanmean(arr)


def robust_alpha_blend(alpha_signals, decay=0.94, max_period=12):
    """对多周期 Alpha 信号做指数加权合成，结果稳定且对衰退不敏感。

    Args:
        alpha_signals: list of dicts {period, ic, ir, hit_rate}
        decay: 指数衰减率（默认 0.94）
        max_period: 最大考虑周期数
    """
    import math
    out = []
    weights_used = []
    for sig in alpha_signals:
        period = int(sig.get('period', 1))
        if period > max_period:
            continue
        w = decay ** (period - 1)
        weights_used.append(w)
        out.append({
            'period': period,
            'weight': round(w, 4),
            'ic': sig.get('ic', 0),
            'ir': sig.get('ir', 0),
            'hit_rate': sig.get('hit_rate', 0),
        })
    total_w = sum(weights_used) or 1.0
    blended = {
        'ic': round(sum(s['weight'] * s['ic'] for s in out) / total_w, 4),
        'ir': round(sum(s['weight'] * s['ir'] for s in out) / total_w, 4),
        'hit_rate': round(sum(s['weight'] * s['hit_rate'] for s in out) / total_w, 4),
    }
    return {'per_period': out, 'blended': blended,
            'decay': decay, 'total_weight': round(total_w, 4)}
