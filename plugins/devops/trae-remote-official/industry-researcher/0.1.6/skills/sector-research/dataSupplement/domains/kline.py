# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · K线数据
========================================

多周期多市场 K 线获取，支持日/周/月/分钟级别。
根据市场自动路由至最优数据源并实现 fallback。

Fallback 策略:
  - A股: 通达信(首选) → 腾讯
  - 美股: 新浪 → Yahoo
  - 港股: Yahoo（首选参数） → Yahoo（备选参数）→ 通达信
"""

from __future__ import annotations

import os
import sys
import datetime
import logging
from typing import List, Optional

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.ticker import detect_market, normalize, to_yahoo_symbol
from providers import tdx, sina, yahoo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 频率映射表
# ---------------------------------------------------------------------------

# 通达信 frequency 代码映射
_TDX_FREQ_MAP = {
    "day": 9,
    "week": 5,
    "month": 6,
    "5min": 0,
    "15min": 1,
    "30min": 2,
    "60min": 3,
}

# Yahoo Finance interval 映射
_YAHOO_INTERVAL_MAP = {
    "day": "1d",
    "week": "1wk",
    "month": "1mo",
    "5min": "5m",
    "15min": "15m",
    "30min": "30m",
    "60min": "60m",
}

# Yahoo Finance range 映射（根据 count 和 freq 推算合理范围）
_YAHOO_RANGE_MAP = {
    "day": "1y",
    "week": "2y",
    "month": "5y",
    "5min": "5d",
    "15min": "5d",
    "30min": "1mo",
    "60min": "1mo",
}

# 新浪美股 period 映射
_SINA_US_PERIOD_MAP = {
    "day": "day",
    "week": "week",
    "month": "month",
}


def get_kline(code: str, freq: str = "day", count: int = 120) -> list[dict]:
    """获取K线数据，支持多周期多市场。

    根据证券代码自动判断市场，选择最优数据源获取历史 K 线。
    支持日线、周线、月线及分钟级别（5/15/30/60 分钟）。

    Args:
        code: 证券代码，支持多种格式:
              - A股: "600519", "sh600519", "600519.SH"
              - 港股: "00700", "0700.HK"
              - 美股: "AAPL", "AAPL.US"
        freq: K线周期，可选值:
              - "day": 日K线
              - "week": 周K线
              - "month": 月K线
              - "5min": 5分钟K线
              - "15min": 15分钟K线
              - "30min": 30分钟K线
              - "60min": 60分钟K线
        count: 获取条数，默认 120（通达信最大 800）

    Returns:
        K线数据列表，每条记录包含:
        [
            {
                date: 日期/时间字符串,
                open: 开盘价,
                high: 最高价,
                low: 最低价,
                close: 收盘价,
                volume: 成交量,
                amount: 成交额,
            },
            ...
        ]
        获取失败返回空列表 []。

    Fallback:
        A股: 通达信(首选) → Yahoo(日线以上)
        美股: 新浪 → Yahoo
        港股: Yahoo → 新浪
    """
    market = detect_market(code)
    normalized = normalize(code)

    # 参数校验
    if freq not in _TDX_FREQ_MAP and freq not in _YAHOO_INTERVAL_MAP:
        logger.warning(f"不支持的K线周期: {freq}，降级为日线")
        freq = "day"

    count = max(1, min(count, 800))

    if market == "CN":
        return _kline_cn(normalized, freq, count)
    elif market == "US":
        return _kline_us(normalized, freq, count)
    else:
        return _kline_hk(normalized, freq, count)


# ---------------------------------------------------------------------------
# A股 K线
# ---------------------------------------------------------------------------


def _kline_cn(code: str, freq: str, count: int) -> list[dict]:
    """A股K线 fallback: 通达信 → Yahoo(日线以上)"""

    # 第一优先: 通达信
    try:
        tdx_freq = _TDX_FREQ_MAP.get(freq, 9)
        raw = tdx.bars(code=code, frequency=tdx_freq, count=count)
        if raw:
            return _normalize_tdx_kline(raw)
    except Exception as e:
        logger.debug(f"通达信K线获取失败({code}, {freq}): {e}")

    # 第二优先: Yahoo（A股也可通过 Yahoo 获取日线以上数据）
    if freq in ("day", "week", "month"):
        try:
            yahoo_symbol = to_yahoo_symbol(code)
            interval = _YAHOO_INTERVAL_MAP.get(freq, "1d")
            range_ = _YAHOO_RANGE_MAP.get(freq, "1y")
            raw = yahoo.chart(symbol=yahoo_symbol, interval=interval, range_=range_)
            if raw:
                return _normalize_yahoo_kline(raw, count)
        except Exception as e:
            logger.debug(f"Yahoo A股K线获取失败({code}, {freq}): {e}")

    logger.warning(f"A股K线所有数据源获取失败: {code}, freq={freq}")
    return []


# ---------------------------------------------------------------------------
# 美股 K线
# ---------------------------------------------------------------------------


def _kline_us(code: str, freq: str, count: int) -> list[dict]:
    """美股K线 fallback: 新浪 → Yahoo"""

    # 第一优先: 新浪（仅支持 day/week/month）
    sina_period = _SINA_US_PERIOD_MAP.get(freq)
    if sina_period:
        try:
            raw = sina.us_kline(code=code, period=sina_period)
            if raw:
                return raw[:count]
        except Exception as e:
            logger.debug(f"新浪美股K线获取失败({code}, {freq}): {e}")

    # 第二优先: Yahoo（支持所有周期）
    try:
        yahoo_symbol = to_yahoo_symbol(code)
        interval = _YAHOO_INTERVAL_MAP.get(freq, "1d")
        range_ = _YAHOO_RANGE_MAP.get(freq, "1y")
        raw = yahoo.chart(symbol=yahoo_symbol, interval=interval, range_=range_)
        if raw:
            return _normalize_yahoo_kline(raw, count)
    except Exception as e:
        logger.debug(f"Yahoo美股K线获取失败({code}, {freq}): {e}")

    logger.warning(f"美股K线所有数据源获取失败: {code}, freq={freq}")
    return []


# ---------------------------------------------------------------------------
# 港股 K线
# ---------------------------------------------------------------------------


def _kline_hk(code: str, freq: str, count: int) -> list[dict]:
    """港股K线 fallback: Yahoo（首选参数） → Yahoo（备选参数）→ 通达信"""

    # 第一优先: Yahoo
    try:
        yahoo_symbol = to_yahoo_symbol(code)
        interval = _YAHOO_INTERVAL_MAP.get(freq, "1d")
        range_ = _YAHOO_RANGE_MAP.get(freq, "1y")
        raw = yahoo.chart(symbol=yahoo_symbol, interval=interval, range_=range_)
        if raw:
            return _normalize_yahoo_kline(raw, count)
    except Exception as e:
        logger.debug(f"Yahoo港股K线获取失败({code}, {freq}): {e}")

    # 第二优先: 新浪港股（暂无专用接口，尝试 hq 获取）
    # 新浪港股K线能力有限，仅作为最终兜底
    try:
        yahoo_symbol = to_yahoo_symbol(code)
        # 二次尝试 Yahoo 不同参数
        interval = _YAHOO_INTERVAL_MAP.get(freq, "1d")
        range_ = "max" if freq in ("month", "week") else "6mo"
        raw = yahoo.chart(symbol=yahoo_symbol, interval=interval, range_=range_)
        if raw:
            return _normalize_yahoo_kline(raw, count)
    except Exception as e:
        logger.debug(f"Yahoo港股K线二次获取失败({code}, {freq}): {e}")

    logger.warning(f"港股K线所有数据源获取失败: {code}, freq={freq}")
    return []


# ---------------------------------------------------------------------------
# 数据标准化
# ---------------------------------------------------------------------------


def _normalize_tdx_kline(raw: list) -> list[dict]:
    """标准化通达信 K 线数据。

    通达信 bars() 返回 DataFrame 转 records 后的字段名可能为:
    datetime/open/high/low/close/vol/amount 或类似变体。
    """
    results = []
    for item in raw:
        record = {
            "date": str(item.get("datetime", item.get("date", ""))),
            "open": _safe_float(item.get("open")),
            "high": _safe_float(item.get("high")),
            "low": _safe_float(item.get("low")),
            "close": _safe_float(item.get("close")),
            "volume": _safe_float(item.get("vol", item.get("volume"))),
            "amount": _safe_float(item.get("amount")),
        }
        results.append(record)
    return results


def _normalize_yahoo_kline(raw: dict, count: int) -> list[dict]:
    """标准化 Yahoo chart 数据。

    Yahoo chart() 返回结构:
    {
        "timestamp": [...],
        "indicators": {
            "quote": [{
                "open": [...],
                "high": [...],
                "low": [...],
                "close": [...],
                "volume": [...]
            }]
        }
    }
    """
    timestamps = raw.get("timestamp", [])
    if not timestamps:
        return []

    indicators = raw.get("indicators", {})
    quotes = indicators.get("quote", [{}])
    if not quotes:
        return []

    quote_data = quotes[0]
    opens = quote_data.get("open", [])
    highs = quote_data.get("high", [])
    lows = quote_data.get("low", [])
    closes = quote_data.get("close", [])
    volumes = quote_data.get("volume", [])

    results = []
    for i, ts in enumerate(timestamps):
        if ts is None:
            continue

        # Unix 时间戳转日期字符串
        try:
            dt = datetime.datetime.fromtimestamp(ts)
            date_str = dt.strftime("%Y-%m-%d %H:%M:%S") if dt.hour > 0 else dt.strftime("%Y-%m-%d")
        except (ValueError, OSError, OverflowError):
            date_str = str(ts)

        record = {
            "date": date_str,
            "open": _safe_float(opens[i] if i < len(opens) else None),
            "high": _safe_float(highs[i] if i < len(highs) else None),
            "low": _safe_float(lows[i] if i < len(lows) else None),
            "close": _safe_float(closes[i] if i < len(closes) else None),
            "volume": _safe_float(volumes[i] if i < len(volumes) else None),
            "amount": None,  # Yahoo 不提供成交额
        }
        results.append(record)

    # 截取最新 count 条
    if len(results) > count:
        results = results[-count:]

    return results


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数，None/无效值返回 None。"""
    if val is None:
        return None
    try:
        result = float(val)
        return result if result == result else None  # 过滤 NaN
    except (ValueError, TypeError):
        return None
