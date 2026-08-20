# -*- coding: utf-8 -*-
"""
技术指标模块
Technical Indicators Module

基于 QuantConnect Lean Indicators 架构
提供与A股数据源适配的技术指标

指标列表：
- 趋势类：EMA, SMA, MACD, ADX
- 摆动类：RSI, KD(J), CCI
- 布林类：BollingerBands
- 其他：Hurst指数、动量指标
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IndicatorResult:
    """指标计算结果"""
    name: str
    value: float
    is_ready: bool = False
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class RollingWindow:
    """滚动窗口"""

    def __init__(self, size: int):
        self.size = size
        self._data: List[float] = []

    def add(self, value: float):
        """添加数据"""
        self._data.append(value)
        if len(self._data) > self.size:
            self._data.pop(0)

    @property
    def is_ready(self) -> bool:
        return len(self._data) >= self.size

    @property
    def samples(self) -> int:
        return len(self._data)

    def __getitem__(self, i: int) -> float:
        if i < 0:
            i = len(self._data) + i
        return self._data[i]

    def __len__(self) -> int:
        return len(self._data)

    @property
    def max(self) -> float:
        return max(self._data) if self._data else 0

    @property
    def min(self) -> float:
        return min(self._data) if self._data else 0


class MovingAverage:
    """移动平均基类"""

    def __init__(self, name: str, period: int):
        self.name = name
        self.period = period
        self._window = RollingWindow(period)
        self._value = 0.0

    def update(self, value: float) -> float:
        self._window.add(value)
        self._value = self._compute()
        return self._value

    def _compute(self) -> float:
        if not self._window.is_ready:
            return sum(self._window._data) / len(self._window._data) if self._window._data else 0
        return self._calc()

    def _calc(self) -> float:
        raise NotImplementedError

    @property
    def value(self) -> float:
        return self._value

    @property
    def is_ready(self) -> bool:
        return self._window.is_ready


class SMA(MovingAverage):
    """简单移动平均 (Simple Moving Average)"""

    def __init__(self, period: int):
        super().__init__(f"SMA({period})", period)

    def _calc(self) -> float:
        return sum(self._window._data) / self.period


class EMA(MovingAverage):
    """指数移动平均 (Exponential Moving Average)"""

    def __init__(self, period: int):
        super().__init__(f"EMA({period})", period)
        self._k = 2 / (period + 1)
        self._ema = 0.0

    def _calc(self) -> float:
        if not self._window.is_ready:
            return sum(self._window._data) / len(self._window._data)
        if self._ema == 0:
            self._ema = self._window[0]
        for i in range(1, len(self._window._data)):
            self._ema = self._window[i] * self._k + self._ema * (1 - self._k)
        return self._ema


class MACD:
    """
    MACD指标 (Moving Average Convergence Divergence)

    计算：
    - DIF = EMA(12) - EMA(26)
    - DEA = EMA(DIF, 9)
    - MACD柱 = (DIF - DEA) * 2
    """

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self._ema_fast = EMA(fast)
        self._ema_slow = EMA(slow)
        self._ema_signal = EMA(signal)
        self._dif = 0.0
        self._dea = 0.0
        self._histogram = 0.0

    def update(self, price: float) -> Tuple[float, float, float]:
        """返回 (DIF, DEA, MACD柱)"""
        self._ema_fast.update(price)
        self._ema_slow.update(price)
        self._dif = self._ema_fast.value - self._ema_slow.value
        self._ema_signal.update(self._dif)
        self._dea = self._ema_signal.value
        self._histogram = (self._dif - self._dea) * 2
        return self._dif, self._dea, self._histogram

    @property
    def dif(self) -> float:
        return self._dif

    @property
    def dea(self) -> float:
        return self._dea

    @property
    def histogram(self) -> float:
        return self._histogram

    @property
    def is_ready(self) -> bool:
        return self._ema_slow.is_ready

    def get_result(self) -> IndicatorResult:
        return IndicatorResult(
            name=f"MACD({self.fast},{self.slow},{self.signal})",
            value=self._dif,
            is_ready=self.is_ready,
            metadata={
                'dif': self._dif,
                'dea': self._dea,
                'histogram': self._histogram,
                'signal': 'bullish' if self._histogram > 0 else 'bearish'
            }
        )


class RSI:
    """
    RSI指标 (Relative Strength Index)

    计算：
    - RS = 平均涨幅 / 平均跌幅
    - RSI = 100 - 100 / (1 + RS)

    参数：
    - period: 计算周期（默认14）
    """

    def __init__(self, period: int = 14):
        self.period = period
        self._gains = RollingWindow(period)
        self._losses = RollingWindow(period)
        self._avg_gain = 0.0
        self._avg_loss = 0.0
        self._value = 50.0

    def update(self, price: float, prev_price: float = None) -> float:
        """更新RSI"""
        if prev_price is not None:
            change = price - prev_price
            gain = max(0, change)
            loss = max(0, -change)
            self._gains.add(gain)
            self._losses.add(loss)

        if self._gains.samples >= self.period:
            if self._avg_gain == 0:
                self._avg_gain = sum(self._gains._data) / self.period
                self._avg_loss = sum(self._losses._data) / self.period
            else:
                self._avg_gain = (self._avg_gain * (self.period - 1) + self._gains[-1]) / self.period
                self._avg_loss = (self._avg_loss * (self.period - 1) + self._losses[-1]) / self.period

            if self._avg_loss == 0:
                self._value = 100
            else:
                rs = self._avg_gain / self._avg_loss
                self._value = 100 - (100 / (1 + rs))

        return self._value

    @property
    def value(self) -> float:
        return self._value

    @property
    def is_ready(self) -> bool:
        return self._gains.samples >= self.period

    def get_result(self) -> IndicatorResult:
        signal = 'overbought' if self._value > 70 else 'oversold' if self._value < 30 else 'neutral'
        return IndicatorResult(
            name=f"RSI({self.period})",
            value=self._value,
            is_ready=self.is_ready,
            metadata={'signal': signal}
        )


class BollingerBands:
    """
    布林带指标 (Bollinger Bands)

    计算：
    - 中轨 = MA(N)
    - 上轨 = 中轨 + K * STD
    - 下轨 = 中轨 - K * STD

    参数：
    - period: 周期（默认20）
    - k: 标准差倍数（默认2）
    """

    def __init__(self, period: int = 20, k: float = 2.0):
        self.period = period
        self.k = k
        self._window = RollingWindow(period)
        self._middle = 0.0
        self._upper = 0.0
        self._lower = 0.0

    def update(self, price: float) -> Tuple[float, float, float]:
        """返回 (上轨, 中轨, 下轨)"""
        self._window.add(price)

        if self._window.is_ready:
            self._middle = sum(self._window._data) / self.period
            variance = sum((p - self._middle) ** 2 for p in self._window._data) / self.period
            std = math.sqrt(variance)
            self._upper = self._middle + self.k * std
            self._lower = self._middle - self.k * std

        return self._upper, self._middle, self._lower

    @property
    def upper(self) -> float:
        return self._upper

    @property
    def middle(self) -> float:
        return self._middle

    @property
    def lower(self) -> float:
        return self._lower

    @property
    def is_ready(self) -> bool:
        return self._window.is_ready

    def get_position(self, price: float) -> float:
        """计算价格在布林带中的位置 (0-1)"""
        if not self.is_ready or self._upper == self._lower:
            return 0.5
        return (price - self._lower) / (self._upper - self._lower)

    def get_result(self) -> IndicatorResult:
        return IndicatorResult(
            name=f"BollingerBands({self.period},{self.k})",
            value=self._middle,
            is_ready=self.is_ready,
            metadata={
                'upper': self._upper,
                'middle': self._middle,
                'lower': self._lower,
                'bandwidth': (self._upper - self._lower) / self._middle if self._middle else 0
            }
        )


class ADX:
    """
    ADX指标 (Average Directional Index)

    计算：
    - +DI = 上升动向指数
    - -DI = 下降动向指数
    - DX = |+DI - -DI| / (|+DI + -DI|) * 100
    - ADX = DX的EMA
    """

    def __init__(self, period: int = 14):
        self.period = period
        self._tr_window = RollingWindow(period)
        self._plus_dm_window = RollingWindow(period)
        self._minus_dm_window = RollingWindow(period)
        self._plus_di = 0.0
        self._minus_di = 0.0
        self._adx = 0.0
        self._prev_high = 0.0
        self._prev_low = 0.0
        self._ema_adx = EMA(period)

    def update(self, high: float, low: float, prev_high: float, prev_low: float, prev_close: float) -> Tuple[float, float, float]:
        """更新ADX"""
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        plus_dm = max(high - prev_high, 0) if (high - prev_high) > (prev_low - low) else 0
        minus_dm = max(prev_low - low, 0) if (prev_low - low) > (high - prev_high) else 0

        self._tr_window.add(tr)
        self._plus_dm_window.add(plus_dm)
        self._minus_dm_window.add(minus_dm)

        self._prev_high = prev_high
        self._prev_low = prev_low

        if self._tr_window.is_ready:
            sum_tr = sum(self._tr_window._data)
            sum_plus_dm = sum(self._plus_dm_window._data)
            sum_minus_dm = sum(self._minus_dm_window._data)

            if sum_tr > 0:
                self._plus_di = (sum_plus_dm / sum_tr) * 100
                self._minus_di = (sum_minus_dm / sum_tr) * 100

            di_sum = self._plus_di + self._minus_di
            if di_sum > 0:
                dx = abs(self._plus_di - self._minus_di) / di_sum * 100
                self._adx = self._ema_adx.update(dx)

        return self._plus_di, self._minus_di, self._adx

    @property
    def plus_di(self) -> float:
        return self._plus_di

    @property
    def minus_di(self) -> float:
        return self._minus_di

    @property
    def adx(self) -> float:
        return self._adx

    @property
    def is_ready(self) -> bool:
        return self._tr_window.is_ready and self._ema_adx.is_ready

    def get_result(self) -> IndicatorResult:
        trend = 'strong' if self._adx > 25 else 'weak'
        direction = 'up' if self._plus_di > self._minus_di else 'down' if self._minus_di > self._plus_di else 'neutral'
        return IndicatorResult(
            name=f"ADX({self.period})",
            value=self._adx,
            is_ready=self.is_ready,
            metadata={
                'plus_di': self._plus_di,
                'minus_di': self._minus_di,
                'adx': self._adx,
                'trend': trend,
                'direction': direction
            }
        )


class HurstIndex:
    """
    Hurst指数

    用于判断时间序列的特性：
    - H < 0.5: 均值回归
    - H = 0.5: 随机游走
    - H > 0.5: 趋势延续

    参数：
    - lookback: 回看周期（默认100）
    """

    def __init__(self, lookback: int = 100):
        self.lookback = lookback
        self._prices: List[float] = []
        self._value = 0.5

    def update(self, price: float) -> float:
        """更新Hurst指数"""
        self._prices.append(price)
        if len(self._prices) > self.lookback:
            self._prices.pop(0)

        if len(self._prices) >= 20:  # 至少需要20个数据点
            self._value = self._calc_hurst()

        return self._value

    def _calc_hurst(self) -> float:
        """计算Hurst指数"""
        n = len(self._prices)
        lags = [2, 4, 8, 16]
        rs_values = []

        for lag in lags:
            if lag >= n:
                continue

            rs_list = []
            for i in range(0, n - lag, lag):
                subset = self._prices[i:i + lag]
                mean = sum(subset) / lag
                deviations = [x - mean for x in subset]
                cumdev = 0
                maxdev = 0
                mindev = 0

                for d in deviations:
                    cumdev += d
                    maxdev = max(maxdev, cumdev)
                    mindev = min(mindev, cumdev)

                r = maxdev - mindev
                s = math.sqrt(sum(d ** 2 for d in deviations) / lag)
                if s > 0:
                    rs_list.append(r / s)

            if rs_list:
                avg_rs = sum(rs_list) / len(rs_list)
                rs_values.append((math.log(lag), math.log(avg_rs)))

        if len(rs_values) >= 2:
            x = [rv[0] for rv in rs_values]
            y = [rv[1] for rv in rs_values]
            x_mean = sum(x) / len(x)
            y_mean = sum(y) / len(y)

            numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
            denominator = sum((x[i] - x_mean) ** 2 for i in range(len(x)))

            if denominator > 0:
                return max(0, min(1, numerator / denominator))

        return 0.5

    @property
    def value(self) -> float:
        return self._value

    @property
    def is_ready(self) -> bool:
        return len(self._prices) >= 20

    def get_result(self) -> IndicatorResult:
        if self._value < 0.5:
            regime = 'mean_reverting'
            signal = '建议均值回归策略'
        elif self._value > 0.5:
            regime = 'trending'
            signal = '建议趋势跟踪策略'
        else:
            regime = 'random'
            signal = '建议区间震荡策略'

        return IndicatorResult(
            name=f"Hurst({self.lookback})",
            value=self._value,
            is_ready=self.is_ready,
            metadata={
                'regime': regime,
                'signal': signal,
                'interpretation': f'H={self._value:.2f}'
            }
        )


class KDJ:
    """
    KDJ随机指标

    计算：
    - RSV = (收盘价 - N日内最低价) / (N日内最高价 - N日内最低价) * 100
    - K = 2/3 * 前K值 + 1/3 * RSV
    - D = 2/3 * 前D值 + 1/3 * K
    - J = 3 * K - 2 * D
    """

    def __init__(self, n: int = 9, m1: int = 3, m2: int = 3):
        self.n = n
        self.m1 = m1
        self.m2 = m2
        self._low_window = RollingWindow(n)
        self._high_window = RollingWindow(n)
        self._k = 50.0
        self._d = 50.0
        self._j = 50.0

    def update(self, high: float, low: float, close: float) -> Tuple[float, float, float]:
        """更新KDJ"""
        self._high_window.add(high)
        self._low_window.add(low)

        if self._low_window.is_ready:
            lowest_low = self._low_window.min
            highest_high = self._high_window.max

            if highest_high != lowest_low:
                rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
            else:
                rsv = 50

            self._k = (2 * self._k + rsv) / 3
            self._d = (2 * self._d + self._k) / 3
            self._j = 3 * self._k - 2 * self._d

        return self._k, self._d, self._j

    @property
    def k(self) -> float:
        return self._k

    @property
    def d(self) -> float:
        return self._d

    @property
    def j(self) -> float:
        return self._j

    @property
    def is_ready(self) -> bool:
        return self._low_window.is_ready

    def get_result(self) -> IndicatorResult:
        if self._k < 20:
            signal = 'oversold'
        elif self._k > 80:
            signal = 'overbought'
        else:
            signal = 'neutral'

        return IndicatorResult(
            name=f"KDJ({self.n},{self.m1},{self.m2})",
            value=self._k,
            is_ready=self.is_ready,
            metadata={
                'k': self._k,
                'd': self._d,
                'j': self._j,
                'signal': signal
            }
        )


class CCI:
    """
    CCI顺势指标 (Commodity Channel Index)

    计算：
    - TP = (最高价 + 最低价 + 收盘价) / 3
    - SMA_TP = TP的N日简单移动平均
    - CCI = (TP - SMA_TP) / (0.015 * 平均绝对偏差)
    """

    def __init__(self, period: int = 14):
        self.period = period
        self._tp_window: List[float] = []
        self._sma_tp = 0.0
        self._value = 0.0

    def update(self, high: float, low: float, close: float) -> float:
        """更新CCI"""
        tp = (high + low + close) / 3
        self._tp_window.append(tp)

        if len(self._tp_window) > self.period:
            self._tp_window.pop(0)

        if len(self._tp_window) >= self.period:
            self._sma_tp = sum(self._tp_window) / self.period
            mean_dev = sum(abs(tp - self._sma_tp) for tp in self._tp_window) / self.period
            if mean_dev > 0:
                self._value = (tp - self._sma_tp) / (0.015 * mean_dev)

        return self._value

    @property
    def value(self) -> float:
        return self._value

    @property
    def is_ready(self) -> bool:
        return len(self._tp_window) >= self.period

    def get_result(self) -> IndicatorResult:
        if self._value > 100:
            signal = 'overbought'
        elif self._value < -100:
            signal = 'oversold'
        else:
            signal = 'neutral'

        return IndicatorResult(
            name=f"CCI({self.period})",
            value=self._value,
            is_ready=self.is_ready,
            metadata={'signal': signal}
        )


class QuantIndicators:
    """
    综合技术指标计算器

    封装常用指标，提供统一的计算接口
    """

    def __init__(self):
        self.macd = MACD()
        self.rsi = RSI(14)
        self.bollinger = BollingerBands(20, 2)
        self.adx = ADX(14)
        self.hurst = HurstIndex(100)
        self.kdj = KDJ()
        self.cci = CCI()

    def update(self, ohlcv: Dict) -> Dict[str, IndicatorResult]:
        """
        更新所有指标

        Args:
            ohlcv: 包含 high, low, close, open, volume 的字典

        Returns:
            Dict[str, IndicatorResult]: 各指标结果
        """
        high = ohlcv.get('high', 0)
        low = ohlcv.get('low', 0)
        close = ohlcv.get('close', 0)
        open_price = ohlcv.get('open', close)
        volume = ohlcv.get('volume', 0)

        results = {}

        # MACD
        self.macd.update(close)
        results['macd'] = self.macd.get_result()

        # RSI
        prev_close = ohlcv.get('prev_close', close)
        self.rsi.update(close, prev_close)
        results['rsi'] = self.rsi.get_result()

        # 布林带
        self.bollinger.update(close)
        results['bollinger'] = self.bollinger.get_result()

        # ADX
        prev_high = ohlcv.get('prev_high', high)
        prev_low = ohlcv.get('prev_low', low)
        prev_close = ohlcv.get('prev_close', close)
        if prev_high and prev_low:
            self.adx.update(high, low, prev_high, prev_low, prev_close)
            results['adx'] = self.adx.get_result()

        # Hurst
        self.hurst.update(close)
        results['hurst'] = self.hurst.get_result()

        # KDJ
        self.kdj.update(high, low, close)
        results['kdj'] = self.kdj.get_result()

        # CCI
        self.cci.update(high, low, close)
        results['cci'] = self.cci.get_result()

        return results

    def get_summary(self) -> Dict:
        """获取技术分析摘要"""
        return {
            'macd': {
                'dif': self.macd.dif,
                'dea': self.macd.dea,
                'histogram': self.macd.histogram,
                'signal': '看多' if self.macd.histogram > 0 else '看空'
            },
            'rsi': {
                'value': self.rsi.value,
                'signal': '超买' if self.rsi.value > 70 else '超卖' if self.rsi.value < 30 else '中性'
            },
            'bollinger': {
                'upper': self.bollinger.upper,
                'middle': self.bollinger.middle,
                'lower': self.bollinger.lower,
                'position': self.bollinger.get_position(self.bollinger.middle)
            },
            'adx': {
                'adx': self.adx.adx,
                'plus_di': self.adx.plus_di,
                'minus_di': self.adx.minus_di,
                'trend': '强势' if self.adx.adx > 25 else '弱势'
            },
            'hurst': self.hurst.get_result().metadata,
            'kdj': {
                'k': self.kdj.k,
                'd': self.kdj.d,
                'j': self.kdj.j
            },
            'cci': {
                'value': self.cci.value,
                'signal': '超买' if self.cci.value > 100 else '超卖' if self.cci.value < -100 else '中性'
            }
        }


# ============================================================
# v3.1.0 增量 — 自适应 MACD / RSI
# ============================================================

def adaptive_macd(prices, atr_period=14, fast=None, slow=None, signal=None):
    """根据 ATR 自适应调整 MACD 快慢参数 — 高波动股票自动放大窗口。"""
    import numpy as _np
    p = _np.array(prices, dtype=float)
    if len(p) < atr_period + 26:
        return None
    # ATR
    diffs = _np.abs(_np.diff(p))
    atr = float(_np.mean(diffs[-atr_period:]))
    # 波动率自放大
    vol_ratio = atr / float(_np.mean(p[-atr_period:])) if _np.mean(p[-atr_period:]) > 0 else 0
    scale = max(0.5, min(1.5, 1 + vol_ratio * 8))
    fast = fast or int(round(12 * scale))
    slow = slow or int(round(26 * scale))
    signal_p = signal or int(round(9 * scale))
    fast = max(5, fast)
    slow = max(fast + 5, slow)
    signal_p = max(5, signal_p)

    def _ema(s, n):
        k = 2 / (n + 1)
        out = [s[0]]
        for v in s[1:]:
            out.append(v * k + out[-1] * (1 - k))
        return out

    ema_f = _ema(p.tolist(), fast)
    ema_s = _ema(p.tolist(), slow)
    # 先算 DIF 序列，再对 DIF 序列取 EMA 得 DEA
    # （修复：原实现对标量 DIF 自我 EMA，DEA 恒等于 DIF，histogram 恒为 0）
    dif_series = [f - s for f, s in zip(ema_f, ema_s)]
    dea_series = _ema(dif_series, signal_p)
    dif = dif_series[-1]
    dea = dea_series[-1]
    hist = 2 * (dif - dea)
    return {
        'DIF': round(dif, 4),
        'DEA': round(dea, 4),
        'histogram': round(hist, 4),
        'fast': fast,
        'slow': slow,
        'signal': signal_p,
        'atr': round(atr, 4),
        'vol_scale': round(scale, 4),
    }


def adaptive_rsi(prices, base_period=14, vol_window=20):
    """ATR 调整的 RSI — 波动率高时缩短周期，低波动时拉长。"""
    import numpy as _np
    p = _np.array(prices, dtype=float)
    if len(p) < vol_window + 5:
        return None
    vol = float(_np.std(_np.diff(p[-vol_window:]) / p[-vol_window:][:-1]))
    scale = 1.0 + vol * 6.0
    period = max(5, int(round(base_period / scale)))
    if len(p) < period + 1:
        return None
    gains, losses = [], []
    for i in range(-period, 0):
        diff = p[i] - p[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_g = sum(gains) / period
    avg_l = sum(losses) / period
    if avg_l == 0:
        rsi = 100.0
    else:
        rs = avg_g / avg_l
        rsi = 100 - 100 / (1 + rs)
    return {
        'rsi': round(rsi, 4),
        'period': period,
        'vol_scale': round(scale, 4),
    }
