# -*- coding: utf-8 -*-
"""v9.0 市场结构 + 指数估值 + 市场内含 测试（离线）"""

import sys
import math
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.index_analysis.market_structure import (
    find_swing_highs, find_swing_lows, trend_structure_from_swings,
    atr, nearest_levels, break_signals,
    MarketStructureAnalyzer, StructureResult,
)
from stock_researcher.index_analysis.index_valuation import (
    percentile_of, valuation_score_from_percentile, valuation_score_from_pe,
    valuation_label_from_score, aggregate_pe,
    IndexValuation, IndexValuationResult,
)
from stock_researcher.index_analysis.market_internals import (
    daily_ad_series, ema, mcclellan_oscillator,
    breadth_status_from_mcclellan, new_highs_lows, health_from_internals,
    MarketInternalsAnalyzer, InternalsResult,
)


# ============================================================
# 1. 市场结构 —— 摆动点 / 趋势结构
# ============================================================

def test_find_swing_highs_in_zigzag():
    """明显的锯齿序列应找到若干高点。"""
    prices = [10, 12, 15, 12, 10, 8, 10, 13, 16, 13, 10]
    highs = find_swing_highs(prices, k=2)
    assert len(highs) >= 1
    assert 15 in highs or 16 in highs


def test_find_swing_lows_in_zigzag():
    prices = [10, 12, 15, 12, 10, 8, 10, 13, 16, 13, 10]
    lows = find_swing_lows(prices, k=2)
    assert 8 in lows


def test_trend_structure_rising_swings_is_uptrend():
    """高点与低点都逐级抬高 → 上升。"""
    highs = [10, 12, 15, 18]
    lows = [5, 7, 10, 13]
    structure, score = trend_structure_from_swings(highs, lows)
    assert structure == "上升"
    assert score > 0


def test_trend_structure_falling_swings_is_downtrend():
    highs = [18, 15, 12, 10]
    lows = [13, 10, 7, 5]
    structure, score = trend_structure_from_swings(highs, lows)
    assert structure == "下降"
    assert score < 0


def test_trend_structure_insufficient_is_sideways():
    structure, score = trend_structure_from_swings([10], [5])
    assert structure == "震荡"


def test_atr_positive_for_volatile():
    assert atr([100, 105, 98, 110, 95], n=4) > 0


def test_nearest_levels_basic():
    prices = [100, 110, 90, 105]   # last=105
    res, sup = nearest_levels(prices, [110], [90])
    assert res >= 105
    assert sup <= 105


def test_break_signals_down_break():
    prices = [10, 12, 15, 12, 8]   # last=8 跌破前低 12
    bdown, bup = break_signals(prices, [15], [12])
    assert bdown is True


def test_market_structure_analyzer_from_prices():
    up = [100 * (1.002 ** i) for i in range(80)]
    ms = MarketStructureAnalyzer().analyze_from_prices("test", up)
    assert isinstance(ms, StructureResult)
    assert ms.trend_structure in ("上升", "下降", "震荡", "未知")
    assert ms.atr >= 0


# ============================================================
# 2. 指数估值纯函数
# ============================================================

def test_percentile_of_extremes():
    hist = [10, 12, 14, 16, 18, 20]
    assert percentile_of(20, hist) == pytest.approx(100.0)
    assert percentile_of(10, hist) == pytest.approx(0.0)


def test_percentile_of_median():
    hist = [10, 12, 14, 16, 18, 20]
    assert percentile_of(14, hist) == pytest.approx(40.0)  # (2)/5*100


def test_percentile_of_insufficient_returns_none():
    assert percentile_of(15, [10, 12]) is None
    assert percentile_of(15, []) is None


def test_valuation_score_from_percentile_high_is_expensive():
    """高分位(贵)→正分；低分位(便宜)→负分。"""
    assert valuation_score_from_percentile(90) > 0
    assert valuation_score_from_percentile(10) < 0
    assert valuation_score_from_percentile(50) == pytest.approx(0.0)
    assert valuation_score_from_percentile(None) == 0.0


def test_valuation_score_from_pe_low_pe_positive():
    assert valuation_score_from_pe(8, "cn") < 0   # 低 PE → 便宜 → 负分(便宜)
    assert valuation_score_from_pe(40, "cn") > 0  # 高 PE → 贵 → 正分


def test_valuation_label_ranges():
    assert valuation_label_from_score(-70) == "极度低估"
    assert valuation_label_from_score(-30) == "低估"
    assert valuation_label_from_score(0) == "合理"
    assert valuation_label_from_score(30) == "高估"
    assert valuation_label_from_score(70) == "极度高估"


def test_aggregate_pe_median():
    """成分股 PE 取中位数（剔除负值）。"""
    assert aggregate_pe([10, 20, 30, -5, None]) == pytest.approx(20.0)


def test_aggregate_pe_empty():
    assert aggregate_pe([]) is None


def test_index_valuation_unavailable_returns_honest():
    """所有源失败 → data_mode='unavailable'，不编造分位。"""
    iv = IndexValuationResult(code="x", data_mode="unavailable")
    assert iv.pe_percentile is None
    assert iv.valuation_label == "未知"


# ============================================================
# 3. 市场内含
# ============================================================

def test_daily_ad_series_net_positive_when_most_rising():
    data = {"a": [10, 11, 12], "b": [10, 11, 12], "c": [10, 9, 8]}
    series = daily_ad_series(data)
    assert len(series) == 2
    # 最后一日：a,b 涨, c 跌 → net = 1
    assert series[-1] == 1


def test_ema_decays_to_value():
    e = ema([10, 10, 10, 10], 3)
    assert len(e) == 4
    assert e[-1] == pytest.approx(10.0)


def test_mcclellan_returns_float():
    net = [10, -5, 20, -10, 15, -8, 12, -3, 18, -6,
           14, -2, 16, -4, 11, -7, 13, -1, 17, -5,
           10, -3, 12, 2, 8, -2, 9, 1, 7, 0,
           6, -1, 8, 2, 5, -1, 7, 3, 4, 1,
           6, 2, 5, 3, 4, 2, 3, 1, 2, 0]
    mcc = mcclellan_oscillator(net)
    assert isinstance(mcc, float)


def test_mcclellan_short_series_zero():
    assert mcclellan_oscillator([1, 2, 3]) == 0.0


def test_breadth_status_overbought_oversold():
    assert breadth_status_from_mcclellan(50, 100) == "超买"
    assert breadth_status_from_mcclellan(-50, 100) == "超卖"
    assert breadth_status_from_mcclellan(5, 100) == "中性"


def test_new_highs_lows_rising_only():
    data = {"a": [10 + i for i in range(30)]}
    hi, lo = new_highs_lows(data, 20)
    assert hi == 1 and lo == 0


def test_health_from_internals_overheated():
    assert health_from_internals(85, 5, 1) == "过热"


def test_health_from_internals_freezing():
    assert health_from_internals(15, 1, 5) == "冰点"


def test_market_internals_analyzer_stub():
    """注入合成成分股数据，验证内含分析链路。"""
    class _Stub(MarketInternalsAnalyzer):
        def _resolve(self, code):
            return ["a", "b", "c", "d", "e"], "full"

        def _fetch_closes(self, codes, days=60):
            return {c: [10 * (1.003 ** i) for i in range(50)] for c in codes}

    mi = _Stub().analyze("sh000300")
    assert isinstance(mi, InternalsResult)
    assert mi.data_mode == "full"
    assert mi.advancers >= 1
    assert mi.health in ("健康", "过热", "中性", "偏弱", "冰点")
