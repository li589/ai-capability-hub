#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术分析引擎
Technical Analysis Engine
包含：MA/EMA/MACD/RSI/KDJ/布林带/均线多头判断/ADX/Hurst指数
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class TechnicalIndicators:
    """技术指标数据"""
    # 均线
    ma5: float = 0
    ma10: float = 0
    ma20: float = 0
    ma60: float = 0
    ma120: float = 0
    ma250: float = 0

    # EMA
    ema12: float = 0
    ema26: float = 0

    # MACD
    macd_dif: float = 0
    macd_dea: float = 0
    macd_hist: float = 0

    # RSI
    rsi6: float = 50
    rsi14: float = 50
    rsi24: float = 50

    # KDJ
    k: float = 50
    d: float = 50
    j: float = 50

    # 布林带
    bb_upper: float = 0
    bb_mid: float = 0
    bb_lower: float = 0
    bb_position: float = 0  # 0-100, 当前价在布林带中的位置

    # ADX
    adx: float = 0

    # 均线状态
    ma_arrangement: str = "混乱"  # 多头排列/空头排列/混乱

    # 综合评分
    tech_score: float = 0
    tech_signal: str = "中性"


class TechnicalAnalyzer:
    """技术分析指标计算器"""

    @staticmethod
    def calc_ma(prices: List[float], period: int) -> float:
        """简单移动平均"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        return sum(prices[-period:]) / period

    @staticmethod
    def calc_ema(prices: List[float], period: int) -> float:
        """指数移动平均"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        k = 2.0 / (period + 1)
        ema = sum(prices[:period]) / period
        for v in prices[period:]:
            ema = v * k + ema * (1 - k)
        return ema

    @staticmethod
    def calc_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """MACD计算 (DIF, DEA, MACD柱)

        正确实现：先计算完整的 DIF 序列（fast EMA - slow EMA），
        再对 DIF 序列做 signal 周期的 EMA 得到 DEA。
        """
        if len(prices) < slow + signal:
            return 0, 0, 0

        # 计算 fast EMA 序列
        k_fast = 2.0 / (fast + 1)
        ema_fast_series = []
        ema_f = sum(prices[:fast]) / fast
        ema_fast_series.append(ema_f)
        for v in prices[fast:]:
            ema_f = v * k_fast + ema_f * (1 - k_fast)
            ema_fast_series.append(ema_f)

        # 计算 slow EMA 序列
        k_slow = 2.0 / (slow + 1)
        ema_slow_series = []
        ema_s = sum(prices[:slow]) / slow
        ema_slow_series.append(ema_s)
        for v in prices[slow:]:
            ema_s = v * k_slow + ema_s * (1 - k_slow)
            ema_slow_series.append(ema_s)

        # DIF 序列：对齐两个 EMA 序列
        # ema_fast_series 从 index fast 开始，ema_slow_series 从 index slow 开始
        # DIF 从 index slow 开始有效
        offset = slow - fast
        dif_series = []
        for i in range(len(ema_slow_series)):
            fi = i + offset
            if 0 <= fi < len(ema_fast_series):
                dif_series.append(ema_fast_series[fi] - ema_slow_series[i])

        if len(dif_series) < signal:
            return 0, 0, 0

        # DEA = EMA(DIF, signal)
        k_signal = 2.0 / (signal + 1)
        dea = sum(dif_series[:signal]) / signal
        for v in dif_series[signal:]:
            dea = v * k_signal + dea * (1 - k_signal)

        dif = dif_series[-1]
        macd_hist = (dif - dea) * 2

        return dif, dea, macd_hist

    @staticmethod
    def calc_rsi(prices: List[float], period: int = 14) -> float:
        """RSI计算"""
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

    @staticmethod
    def calc_kdj(highs: List[float], lows: List[float], closes: List[float], period: int = 9) -> Tuple[float, float, float]:
        """KDJ计算（标准递推平滑，与行情软件口径一致）"""
        if len(closes) < period:
            return 50, 50, 50

        # 从序列起点逐日递推: K=(2/3)K_prev+(1/3)RSV, D=(2/3)D_prev+(1/3)K, 初值50
        k = d = 50.0
        n = len(closes)
        for i in range(n):
            s = max(0, i - period + 1)
            hh = max(highs[s:i + 1]) if len(highs) > i else closes[i]
            ll = min(lows[s:i + 1]) if len(lows) > i else closes[i]
            rsv = (closes[i] - ll) / (hh - ll) * 100 if hh != ll else 50
            k = 2 / 3 * k + 1 / 3 * rsv
            d = 2 / 3 * d + 1 / 3 * k
        j = 3 * k - 2 * d

        # 限制范围
        k = max(0, min(100, k))
        d = max(0, min(100, d))
        j = max(0, min(100, j))

        return k, d, j

    @staticmethod
    def calc_bollinger(prices: List[float], period: int = 20, std_mult: float = 2) -> Tuple[float, float, float]:
        """布林带计算 (上轨, 中轨, 下轨)"""
        if len(prices) < period:
            return 0, 0, 0

        recent = prices[-period:]
        mid = sum(recent) / period
        variance = sum((p - mid) ** 2 for p in recent) / period
        std = math.sqrt(variance)

        return mid + std_mult * std, mid, mid - std_mult * std

    @staticmethod
    def calc_hurst(returns: List[float], lookback: int = 100) -> float:
        """
        Hurst指数计算 - 区分趋势/均值回归/随机
        H < 0.5: 均值回归
        H = 0.5: 随机游走
        H > 0.5: 趋势延续
        """
        if len(returns) < lookback:
            lookback = len(returns)
        if lookback < 10:
            return 0.5

        data = returns[-lookback:]
        n = len(data)

        # R/S分析
        def range_over_std(n):
            if n > len(data):
                return 1
            subseries = [data[i:i+n] for i in range(0, len(data), n)]
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

        for n_size in [5, 10, 20, 50]:
            if n_size <= len(data):
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

    # ── v6.0 新增指标 ──

    @staticmethod
    def calc_obv(closes: List[float], volumes: List[float]) -> List[float]:
        """能量潮 OBV (On-Balance Volume)"""
        obv = [0.0]
        for i in range(1, min(len(closes), len(volumes))):
            if closes[i] > closes[i-1]:
                obv.append(obv[-1] + volumes[i])
            elif closes[i] < closes[i-1]:
                obv.append(obv[-1] - volumes[i])
            else:
                obv.append(obv[-1])
        return obv

    @staticmethod
    def calc_atr(highs: List[float], lows: List[float], closes: List[float],
                 period: int = 14) -> float:
        """真实波幅 ATR (Average True Range)"""
        n = min(len(highs), len(lows), len(closes))
        if n < period + 1:
            return 0.0
        tr_list = []
        for i in range(1, n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1]),
            )
            tr_list.append(tr)
        if not tr_list:
            return 0.0
        # Wilder's smoothing
        atr = sum(tr_list[:period]) / period
        for i in range(period, len(tr_list)):
            atr = (atr * (period - 1) + tr_list[i]) / period
        return round(atr, 4)

    @staticmethod
    def calc_adx(highs: List[float], lows: List[float], closes: List[float],
                 period: int = 14) -> dict:
        """平均趋向指标 ADX (Average Directional Index)
        返回: {adx, pdi, ndi}
        ADX > 25 强趋势, ADX < 20 弱趋势/震荡
        """
        n = min(len(highs), len(lows), len(closes))
        if n < period * 2:
            return {"adx": 0.0, "pdi": 0.0, "ndi": 0.0}

        tr_list, plus_dm, minus_dm = [], [], []
        for i in range(1, n):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1]),
            )
            tr_list.append(tr)
            up = highs[i] - highs[i-1]
            down = lows[i-1] - lows[i]
            plus_dm.append(up if up > down and up > 0 else 0)
            minus_dm.append(down if down > up and down > 0 else 0)

        # Wilder's smoothing
        atr = sum(tr_list[:period])
        pdi_sum = sum(plus_dm[:period])
        ndi_sum = sum(minus_dm[:period])
        pdi_vals, ndi_vals, adx_vals = [], [], []
        for i in range(period, len(tr_list)):
            atr = atr - atr / period + tr_list[i]
            pdi_sum = pdi_sum - pdi_sum / period + plus_dm[i]
            ndi_sum = ndi_sum - ndi_sum / period + minus_dm[i]
            pdi = (pdi_sum / atr * 100) if atr > 0 else 0
            ndi = (ndi_sum / atr * 100) if atr > 0 else 0
            dx = abs(pdi - ndi) / (pdi + ndi) * 100 if (pdi + ndi) > 0 else 0
            pdi_vals.append(pdi)
            ndi_vals.append(ndi)
            adx_vals.append(dx)

        # ADX = smoothed DX
        if adx_vals:
            adx = sum(adx_vals[:period]) / period if len(adx_vals) >= period else sum(adx_vals) / len(adx_vals)
            for i in range(period, len(adx_vals)):
                adx = (adx * (period - 1) + adx_vals[i]) / period
            return {
                "adx": round(adx, 2),
                "pdi": round(pdi_vals[-1] if pdi_vals else 0, 2),
                "ndi": round(ndi_vals[-1] if ndi_vals else 0, 2),
            }
        return {"adx": 0.0, "pdi": 0.0, "ndi": 0.0}

    @staticmethod
    def calc_williams_r(highs: List[float], lows: List[float], closes: List[float],
                        period: int = 14) -> float:
        """威廉指标 WR (Williams %R)
        -100 到 0: -20 以上超买, -80 以下超卖
        """
        n = min(len(highs), len(lows), len(closes))
        if n < period:
            return -50.0
        hh = max(highs[-period:])
        ll = min(lows[-period:])
        if hh == ll:
            return -50.0
        wr = (hh - closes[-1]) / (hh - ll) * -100
        return round(wr, 2)

    @staticmethod
    def calc_cci(highs: List[float], lows: List[float], closes: List[float],
                 period: int = 20) -> float:
        """商品通道指数 CCI (Commodity Channel Index)
        CCI > +100 超买, CCI < -100 超卖
        """
        n = min(len(highs), len(lows), len(closes))
        if n < period:
            return 0.0
        tp_list = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(n)]
        tp = tp_list[-period:]
        tp_avg = sum(tp) / len(tp)
        md = sum(abs(t - tp_avg) for t in tp) / len(tp)
        if md == 0:
            return 0.0
        cci = (tp[-1] - tp_avg) / (0.015 * md)
        return round(cci, 2)

    @staticmethod
    def calc_mfi(highs: List[float], lows: List[float], closes: List[float],
                 volumes: List[float], period: int = 14) -> float:
        """资金流量指标 MFI (Money Flow Index)
        0-100: > 80 超买, < 20 超卖
        """
        n = min(len(highs), len(lows), len(closes), len(volumes))
        if n < period + 1:
            return 50.0
        tp_list = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(n)]
        pos_flow, neg_flow = 0.0, 0.0
        for i in range(n - period, n):
            mf = tp_list[i] * volumes[i]
            if i > 0 and tp_list[i] > tp_list[i-1]:
                pos_flow += mf
            else:
                neg_flow += mf
        if neg_flow == 0:
            return 100.0
        mfr = pos_flow / neg_flow
        mfi = 100 - (100 / (1 + mfr))
        return round(mfi, 2)

    @staticmethod
    def check_ma_arrangement(prices: List[float]) -> str:
        """判断均线多头/空头排列"""
        if len(prices) < 60:
            return "数据不足"

        ma5 = TechnicalAnalyzer.calc_ma(prices, 5)
        ma10 = TechnicalAnalyzer.calc_ma(prices, 10)
        ma20 = TechnicalAnalyzer.calc_ma(prices, 20)
        ma60 = TechnicalAnalyzer.calc_ma(prices, 60)

        if ma5 > ma10 > ma20 > ma60:
            return "多头排列"
        elif ma5 < ma10 < ma20 < ma60:
            return "空头排列"
        else:
            return "混乱"

    @staticmethod
    def calc_bb_position(price: float, upper: float, mid: float, lower: float) -> float:
        """计算价格在布林带中的位置 (0-100)"""
        if upper == lower or upper == 0:
            return 50
        return (price - lower) / (upper - lower) * 100

    def analyze(self, code: str, prices: List[float], highs: List[float] = None, lows: List[float] = None) -> TechnicalIndicators:
        """
        综合技术分析

        参数:
            code: 股票代码
            prices: 收盘价列表（至少20个数据点）
            highs: 最高价列表（可选）
            lows: 最低价列表（可选）

        返回:
            TechnicalIndicators 对象

        注意:
            - 数据不足时（<20个点）会抛出ValueError
            - KDJ指标因需要历史平滑值，短期内可能有误差
            - 均线多头判断需要至少60个数据点
        """
        if len(prices) < 20:
            raise ValueError(f"[数据不足] 需要至少20个数据点进行技术分析，当前只有{len(prices)}个数据点。请检查股票代码是否正确或获取更多历史数据。")

        # 如果没有提供highs/lows，使用closes模拟
        if highs is None or len(highs) == 0:
            highs = prices
        if lows is None or len(lows) == 0:
            lows = prices

        current = prices[-1]

        # 均线计算
        ma5 = self.calc_ma(prices, 5)
        ma10 = self.calc_ma(prices, 10)
        ma20 = self.calc_ma(prices, 20)
        ma60 = self.calc_ma(prices, 60)
        ma120 = self.calc_ma(prices, 120) if len(prices) >= 120 else current
        ma250 = self.calc_ma(prices, 250) if len(prices) >= 250 else current

        # EMA计算
        ema12 = self.calc_ema(prices, 12)
        ema26 = self.calc_ema(prices, 26)

        # MACD
        macd_dif, macd_dea, macd_hist = self.calc_macd(prices)

        # RSI
        rsi6 = self.calc_rsi(prices, 6)
        rsi14 = self.calc_rsi(prices, 14)
        rsi24 = self.calc_rsi(prices, 24)

        # KDJ
        k, d, j = self.calc_kdj(highs, lows, prices)

        # 布林带
        bb_upper, bb_mid, bb_lower = self.calc_bollinger(prices)
        bb_position = self.calc_bb_position(current, bb_upper, bb_mid, bb_lower)

        # ADX (v6.0: returns dict with adx/pdi/ndi)
        adx_dict = self.calc_adx(highs, lows, prices)
        adx_value = adx_dict.get("adx", 0) if isinstance(adx_dict, dict) else 0

        # 均线排列
        ma_arrangement = self.check_ma_arrangement(prices)

        # 综合技术评分
        tech_score = self._calc_tech_score(
            current=current,
            ma5=ma5, ma10=ma10, ma20=ma20, ma60=ma60,
            rsi14=rsi14,
            macd_hist=macd_hist,
            bb_position=bb_position,
            ma_arrangement=ma_arrangement
        )

        return TechnicalIndicators(
            ma5=round(ma5, 2), ma10=round(ma10, 2), ma20=round(ma20, 2),
            ma60=round(ma60, 2), ma120=round(ma120, 2), ma250=round(ma250, 2),
            ema12=round(ema12, 2), ema26=round(ema26, 2),
            macd_dif=round(macd_dif, 4), macd_dea=round(macd_dea, 4), macd_hist=round(macd_hist, 4),
            rsi6=round(rsi6, 1), rsi14=round(rsi14, 1), rsi24=round(rsi24, 1),
            k=round(k, 1), d=round(d, 1), j=round(j, 1),
            bb_upper=round(bb_upper, 2), bb_mid=round(bb_mid, 2), bb_lower=round(bb_lower, 2),
            bb_position=round(bb_position, 1),
            adx=round(adx_value, 1),
            ma_arrangement=ma_arrangement,
            tech_score=tech_score,
            tech_signal=self._get_tech_signal(tech_score)
        )

    def _calc_tech_score(self, current: float, ma5: float, ma10: float, ma20: float, ma60: float,
                         rsi14: float, macd_hist: float, bb_position: float, ma_arrangement: str) -> float:
        """计算技术综合评分 (-100 ~ +100)"""
        score = 0

        # 均线状态 (40分)
        if ma_arrangement == "多头排列":
            score += 40
        elif ma_arrangement == "空头排列":
            score -= 40
        else:
            # 部分多头
            if ma5 > ma20:
                score += 20
            else:
                score -= 20

        # RSI (30分)
        if rsi14 < 30:
            score += 15  # 超卖，看涨
        elif rsi14 > 70:
            score -= 15  # 超买，看跌
        else:
            # 中性区间
            if rsi14 > 50:
                score += 5
            else:
                score -= 5

        # MACD (20分)
        if macd_hist > 0:
            score += 20
        else:
            score -= 20

        # 布林带位置 (10分)
        if bb_position > 80:
            score -= 10  # 接近上轨，可能回调
        elif bb_position < 20:
            score += 10  # 接近下轨，可能反弹

        return score

    def _get_tech_signal(self, score: float) -> str:
        """根据评分给出信号"""
        if score > 20:
            return "买入"
        elif score > -10:
            return "观望"
        else:
            return "卖出"

    def get_trading_signal(self, tech: TechnicalIndicators) -> Dict:
        """
        获取交易信号
        返回: {"action": "buy/sell/hold", "reason": "...", "confidence": 0-1}
        """
        signals = []

        # 均线信号
        if tech.ma_arrangement == "多头排列":
            signals.append(("买入", 0.8))
        elif tech.ma_arrangement == "空头排列":
            signals.append(("卖出", 0.8))

        # RSI信号
        if tech.rsi14 < 30:
            signals.append(("买入", 0.7))
        elif tech.rsi14 > 70:
            signals.append(("卖出", 0.7))

        # MACD信号
        if tech.macd_hist > 0:
            signals.append(("买入", 0.6))
        else:
            signals.append(("卖出", 0.6))

        # 布林带信号
        if tech.bb_position < 20:
            signals.append(("买入", 0.5))
        elif tech.bb_position > 80:
            signals.append(("卖出", 0.5))

        # 统计
        buy_signals = sum(1 for s, _ in signals if s == "买入")
        sell_signals = sum(1 for s, _ in signals if s == "卖出")

        if buy_signals > sell_signals:
            action = "买入"
            confidence = buy_signals / len(signals)
        elif sell_signals > buy_signals:
            action = "卖出"
            confidence = sell_signals / len(signals)
        else:
            action = "观望"
            confidence = 0.5

        reasons = [r for r, _ in signals]

        return {
            "action": action,
            "reasons": reasons,
            "confidence": round(confidence, 2),
            "tech_score": tech.tech_score,
            "tech_signal": tech.tech_signal
        }

# ============================================================
# v3.1.0 增量 — ATR 自适应止损 / 趋势强度评分
# ============================================================

def atr_trailing_stop(prices, highs, lows, atr_period=14, atr_multiple=2.5):
    """基于 ATR 的移动止损价 — 返回当前应设的止损位。

    Args:
        prices, highs, lows: 等长的价格序列
        atr_period: ATR 计算窗口
        atr_multiple: 止损距离 = ATR × 倍数
    """
    import numpy as _np
    p = _np.array(prices, dtype=float)
    h = _np.array(highs, dtype=float)
    l = _np.array(lows, dtype=float)
    n = min(len(p), len(h), len(l))
    if n < atr_period + 1:
        return {'stop': None, 'atr': None, 'recommendation': '样本不足'}
    trs = []
    for i in range(-atr_period, 0):
        tr = max(h[i] - l[i],
                 abs(h[i] - p[i - 1]),
                 abs(l[i] - p[i - 1]))
        trs.append(tr)
    atr = float(_np.mean(trs))
    price = float(p[-1])
    stop = price - atr * atr_multiple
    if price < l[-atr_period:].min():
        rec = '当前价已近周期低点，建议重新评估入场'
    elif price > h[-atr_period:].max():
        rec = '当前价已近周期高点，注意回落风险'
    else:
        rec = f'ATR({atr_period})={atr:.2f}，建议将止损设为 {stop:.2f}'
    return {
        'stop': round(stop, 4),
        'atr': round(atr, 4),
        'price': round(price, 4),
        'recommendation': rec,
    }


def trend_strength(prices, short=20, long=60):
    """趋势强度评分 (-100 ~ +100)，结合均线斜率与价效比。"""
    import numpy as _np
    p = _np.array(prices, dtype=float)
    if len(p) < long:
        return {'score': 0, 'level': '数据不足'}
    ma_s = float(_np.mean(p[-short:]))
    ma_l = float(_np.mean(p[-long:]))
    diff = (ma_s - ma_l) / max(ma_l, 1e-9) * 100
    if len(p) >= 2 * short:
        prev_ma_s = float(_np.mean(p[-2 * short:-short]))
        slope = (ma_s - prev_ma_s) / max(prev_ma_s, 1e-9) * 100
    else:
        slope = diff
    tail = p[-short:]
    rng = float(_np.max(tail) - _np.min(tail))
    avg_close = float(_np.mean(tail))
    direction = abs(p[-1] - p[-short]) / max(avg_close, 1e-9) * 100
    efficiency = direction / (rng + 1e-9)
    efficiency = max(0, min(1, efficiency))
    score_raw = 0.5 * diff + 0.5 * slope
    score = max(-100, min(100, score_raw * efficiency * 5))
    if score > 60:
        level = '强上升趋势'
    elif score > 25:
        level = '温和上升'
    elif score < -60:
        level = '强下降趋势'
    elif score < -25:
        level = '温和下降'
    else:
        level = '震荡 / 无明显趋势'
    return {
        'score': round(score, 1),
        'level': level,
        'ma_slope_pct': round(slope, 3),
        'ma_gap_pct': round(diff, 3),
        'efficiency': round(efficiency, 4),
    }
