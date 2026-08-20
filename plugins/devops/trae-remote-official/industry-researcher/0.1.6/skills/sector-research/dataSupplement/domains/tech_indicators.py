# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 技术指标（纯本地计算，零网络请求）
==================================================================

功能概览:
  - compute_indicators: 基于K线计算全套技术指标
  - ma: 移动平均线 (MA5/MA10/MA20/MA60)
  - ema: 指数移动平均 (EMA12/EMA26)
  - macd: MACD (DIF/DEA/HIST)
  - rsi: 相对强弱指标 (RSI6/RSI12/RSI24)
  - kdj: KDJ随机指标 (K/D/J)
  - boll: 布林带 (upper/mid/lower)

设计原则:
  - 所有计算函数均为纯函数，不发起任何网络请求
  - compute_indicators 是唯一涉及数据获取的入口（先取K线再计算）
  - 支持任意长度的价格序列输入
  - 返回值为标准 Python 数据结构，便于序列化

零外部依赖 — 仅使用 Python 标准库（math 模块）。
"""

from __future__ import annotations

import sys
import os
import math
from typing import Optional

# 路径设置: 确保 core/ 和 providers/ 可导入
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.cache import cache_get, cache_set, make_key, TTL_KLINE
from core.ticker import normalize, detect_market, to_tencent_code

# ---------------------------------------------------------------------------
# 纯计算函数 — 零网络请求
# ---------------------------------------------------------------------------


def ma(closes: list, periods: list = None) -> dict:
    """移动平均线

    计算给定收盘价序列的简单移动平均线 (SMA)。

    Args:
        closes: 收盘价列表（按时间正序，最早在前）
        periods: 周期列表，默认 [5, 10, 20, 60]

    Returns:
        各周期MA值字典:
        {"MA5": [None, None, None, None, 10.5, 10.6, ...],
         "MA10": [...], "MA20": [...], "MA60": [...]}
        
        注: 前 (period-1) 个值为 None（数据不足无法计算）
    """
    if periods is None:
        periods = [5, 10, 20, 60]

    result = {}
    n = len(closes)

    for period in periods:
        key = f"MA{period}"
        values = []
        for i in range(n):
            if i < period - 1:
                values.append(None)
            else:
                window = closes[i - period + 1: i + 1]
                avg = sum(window) / period
                values.append(round(avg, 4))
        result[key] = values

    return result


def ema(closes: list, period: int = 12) -> list:
    """指数移动平均

    计算指数加权移动平均线 (EMA)。
    EMA_today = price_today * k + EMA_yesterday * (1-k)
    其中 k = 2 / (period + 1)

    Args:
        closes: 收盘价列表（按时间正序）
        period: EMA 周期，默认 12

    Returns:
        EMA 值列表，长度与 closes 相同。
        第一个值使用前 period 个数据的 SMA 初始化。
    """
    if not closes:
        return []

    n = len(closes)
    k = 2.0 / (period + 1)
    result = [0.0] * n

    # 初始值: 使用前 period 个价格的 SMA
    if n < period:
        # 数据不足，使用所有数据的均值初始化
        result[0] = closes[0]
        for i in range(1, n):
            result[i] = closes[i] * k + result[i - 1] * (1 - k)
    else:
        initial_sma = sum(closes[:period]) / period
        result[period - 1] = initial_sma
        # period 之前的值用逐步EMA
        result[0] = closes[0]
        for i in range(1, period - 1):
            result[i] = closes[i] * k + result[i - 1] * (1 - k)
        result[period - 1] = initial_sma
        # period 之后正常计算
        for i in range(period, n):
            result[i] = closes[i] * k + result[i - 1] * (1 - k)

    return [round(v, 4) for v in result]


def macd(closes: list, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD (DIF/DEA/HIST)

    计算 MACD 指标:
      - DIF = EMA(fast) - EMA(slow)
      - DEA = EMA(DIF, signal)
      - HIST = (DIF - DEA) * 2  (柱状图)

    Args:
        closes: 收盘价列表（按时间正序）
        fast: 快线周期，默认 12
        slow: 慢线周期，默认 26
        signal: 信号线周期，默认 9

    Returns:
        {"DIF": [...], "DEA": [...], "HIST": [...]}
    """
    if not closes or len(closes) < slow:
        return {"DIF": [], "DEA": [], "HIST": []}

    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)

    # DIF = EMA_fast - EMA_slow
    n = len(closes)
    dif = [round(ema_fast[i] - ema_slow[i], 4) for i in range(n)]

    # DEA = EMA(DIF, signal)
    dea = ema(dif, signal)

    # HIST = (DIF - DEA) * 2
    hist = [round((dif[i] - dea[i]) * 2, 4) for i in range(n)]

    return {"DIF": dif, "DEA": dea, "HIST": hist}


def rsi(closes: list, periods: list = None) -> dict:
    """相对强弱指标 (RSI)

    RSI = 100 - 100 / (1 + RS)
    RS = 平均上涨幅度 / 平均下跌幅度

    使用 Wilder 平滑法（指数移动平均）计算。

    Args:
        closes: 收盘价列表（按时间正序）
        periods: RSI 周期列表，默认 [6, 12, 24]

    Returns:
        各周期RSI值字典:
        {"RSI6": [None, None, ..., 65.3, 70.1, ...],
         "RSI12": [...], "RSI24": [...]}
    """
    if periods is None:
        periods = [6, 12, 24]

    if not closes or len(closes) < 2:
        return {f"RSI{p}": [] for p in periods}

    n = len(closes)
    # 计算价格变动
    changes = [0.0] + [closes[i] - closes[i - 1] for i in range(1, n)]

    result = {}
    for period in periods:
        key = f"RSI{period}"
        values = [None] * n

        if n <= period:
            result[key] = values
            continue

        # 初始 RS: 前 period 个变动的平均
        gains = [max(changes[i], 0) for i in range(1, period + 1)]
        losses = [abs(min(changes[i], 0)) for i in range(1, period + 1)]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            values[period] = 100.0
        else:
            rs = avg_gain / avg_loss
            values[period] = round(100 - 100 / (1 + rs), 2)

        # Wilder 平滑法递推
        for i in range(period + 1, n):
            change = changes[i]
            gain = max(change, 0)
            loss = abs(min(change, 0))

            avg_gain = (avg_gain * (period - 1) + gain) / period
            avg_loss = (avg_loss * (period - 1) + loss) / period

            if avg_loss == 0:
                values[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                values[i] = round(100 - 100 / (1 + rs), 2)

        result[key] = values

    return result


def kdj(highs: list, lows: list, closes: list, n: int = 9) -> dict:
    """KDJ随机指标

    计算步骤:
      1. RSV = (Close - Low_N) / (High_N - Low_N) * 100
      2. K = 2/3 * K_prev + 1/3 * RSV
      3. D = 2/3 * D_prev + 1/3 * K
      4. J = 3*K - 2*D

    Args:
        highs: 最高价列表（按时间正序）
        lows: 最低价列表（按时间正序）
        closes: 收盘价列表（按时间正序）
        n: RSV 周期，默认 9

    Returns:
        {"K": [...], "D": [...], "J": [...]}
    """
    length = len(closes)
    if length == 0 or len(highs) != length or len(lows) != length:
        return {"K": [], "D": [], "J": []}

    k_values = [None] * length
    d_values = [None] * length
    j_values = [None] * length

    # 初始化 K、D 为 50
    prev_k = 50.0
    prev_d = 50.0

    for i in range(length):
        if i < n - 1:
            # 数据不足周期时仍然计算（使用已有数据范围）
            window_high = max(highs[:i + 1])
            window_low = min(lows[:i + 1])
        else:
            window_high = max(highs[i - n + 1: i + 1])
            window_low = min(lows[i - n + 1: i + 1])

        # RSV
        if window_high == window_low:
            rsv = 50.0
        else:
            rsv = (closes[i] - window_low) / (window_high - window_low) * 100

        # K, D, J
        cur_k = 2.0 / 3 * prev_k + 1.0 / 3 * rsv
        cur_d = 2.0 / 3 * prev_d + 1.0 / 3 * cur_k
        cur_j = 3 * cur_k - 2 * cur_d

        k_values[i] = round(cur_k, 2)
        d_values[i] = round(cur_d, 2)
        j_values[i] = round(cur_j, 2)

        prev_k = cur_k
        prev_d = cur_d

    return {"K": k_values, "D": d_values, "J": j_values}


def boll(closes: list, period: int = 20, std_dev: float = 2.0) -> dict:
    """布林带 (Bollinger Bands)

    计算布林带三条轨道:
      - 中轨 (mid): period 日简单移动平均
      - 上轨 (upper): mid + std_dev * 标准差
      - 下轨 (lower): mid - std_dev * 标准差

    Args:
        closes: 收盘价列表（按时间正序）
        period: 均线周期，默认 20
        std_dev: 标准差倍数，默认 2.0

    Returns:
        {"upper": [...], "mid": [...], "lower": [...]}
        前 (period-1) 个值为 None
    """
    n = len(closes)
    upper = [None] * n
    mid = [None] * n
    lower = [None] * n

    for i in range(period - 1, n):
        window = closes[i - period + 1: i + 1]
        avg = sum(window) / period

        # 标准差
        variance = sum((x - avg) ** 2 for x in window) / period
        sd = math.sqrt(variance)

        mid[i] = round(avg, 4)
        upper[i] = round(avg + std_dev * sd, 4)
        lower[i] = round(avg - std_dev * sd, 4)

    return {"upper": upper, "mid": mid, "lower": lower}


# ---------------------------------------------------------------------------
# 综合入口 — 获取K线 + 计算指标
# ---------------------------------------------------------------------------


def _fetch_kline(code: str, freq: str = "day", count: int = 120) -> list[dict]:
    """内部: 获取K线数据用于指标计算。

    尝试多个数据源获取K线:
    1. 腾讯日K
    2. akshare
    3. 通达信

    Args:
        code: 股票代码
        freq: K线周期 day/week/month
        count: 获取条数

    Returns:
        K线数据列表: [{date, open, high, low, close, volume}, ...]
    """
    # 直接复用 domains.kline 的成熟实现（含通达信→Yahoo fallback 链）
    from domains.kline import get_kline
    return get_kline(code, freq=freq, count=count)


def compute_indicators(code: str, indicators: list = None,
                       freq: str = "day", count: int = 120) -> dict:
    """基于K线计算技术指标，先获取K线再本地计算

    这是技术指标模块的综合入口函数。先从数据源获取指定股票的K线数据，
    然后在本地计算所有请求的技术指标。

    支持指标:
      - MA(5/10/20/60): 移动平均线
      - EMA(12/26): 指数移动平均
      - MACD(DIF/DEA/HIST): MACD
      - RSI(6/12/24): 相对强弱指标
      - KDJ(K/D/J): 随机指标
      - BOLL(upper/mid/lower): 布林带

    Args:
        code: 股票代码，如 '600519'
        indicators: 需要计算的指标列表，如 ['ma', 'macd', 'rsi']
                    默认 None 表示计算全部指标
        freq: K线周期，可选 'day'(日K)、'week'(周K)、'month'(月K)
        count: K线条数，默认 120

    Returns:
        计算结果字典:
        {
            "kline": [{date, open, high, low, close, volume}, ...],
            "ma": {"MA5": [...], "MA10": [...], "MA20": [...], "MA60": [...]},
            "ema": {"EMA12": [...], "EMA26": [...]},
            "macd": {"DIF": [...], "DEA": [...], "HIST": [...]},
            "rsi": {"RSI6": [...], "RSI12": [...], "RSI24": [...]},
            "kdj": {"K": [...], "D": [...], "J": [...]},
            "boll": {"upper": [...], "mid": [...], "lower": [...]},
        }
    """
    if indicators is None:
        indicators = ["ma", "ema", "macd", "rsi", "kdj", "boll"]

    # 标准化指标名称
    indicators = [ind.lower().strip() for ind in indicators]

    normalized = normalize(code)
    ck = make_key("compute_indicators", normalized, freq, count, ",".join(sorted(indicators)))
    cached = cache_get(ck)
    if cached is not None:
        return cached

    # 获取K线数据
    kline = _fetch_kline(normalized, freq=freq, count=count)
    if not kline:
        return {"kline": [], "error": "无法获取K线数据"}

    # 提取价格序列
    closes = [k["close"] for k in kline]
    highs = [k["high"] for k in kline]
    lows = [k["low"] for k in kline]

    result = {"kline": kline}

    # 按需计算各指标
    if "ma" in indicators:
        result["ma"] = ma(closes, periods=[5, 10, 20, 60])

    if "ema" in indicators:
        result["ema"] = {
            "EMA12": ema(closes, 12),
            "EMA26": ema(closes, 26),
        }

    if "macd" in indicators:
        result["macd"] = macd(closes, fast=12, slow=26, signal=9)

    if "rsi" in indicators:
        result["rsi"] = rsi(closes, periods=[6, 12, 24])

    if "kdj" in indicators:
        result["kdj"] = kdj(highs, lows, closes, n=9)

    if "boll" in indicators:
        result["boll"] = boll(closes, period=20, std_dev=2.0)

    cache_set(ck, result, ttl=TTL_KLINE)
    return result
