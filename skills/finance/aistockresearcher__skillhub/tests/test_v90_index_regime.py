# -*- coding: utf-8 -*-
"""v9.0 市场体制 + 波动率体制 测试（离线）"""

import sys
import math
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.index_analysis.market_regime import (
    classify_from_prices, max_drawdown, drawdown_from_high,
    slope_pct, sma, sma_series, MarketRegimeClassifier, RegimeResult,
)
from stock_researcher.index_analysis.volatility_regime import (
    realized_vol, vol_regime_label, is_bull_friendly,
    vol_of_vol, vol_percentile, rolling_vol_series,
    VolatilityRegimeAnalyzer, VolatilityResult,
)


def _up(n, start=100.0, daily=0.002):
    return [start * ((1 + daily) ** i) for i in range(n)]


def _down(n, start=100.0, daily=0.002):
    return [start * ((1 - daily) ** i) for i in range(n)]


def _flat(n, base=100.0, noise=0.0):
    return [base + noise * math.sin(i) for i in range(n)]


# ============================================================
# 1. 基础统计纯函数
# ============================================================

def test_sma_basic():
    assert sma([1, 2, 3, 4, 5], 5) == pytest.approx(3.0)
    assert sma([1, 2, 3], 5) is None


def test_sma_series_length():
    s = sma_series([1, 2, 3, 4, 5], 3)
    assert len(s) == 3   # 5-3+1


def test_max_drawdown_known():
    # 100 → 120 → 90 → 回撤 = 1-90/120 = 0.25
    assert max_drawdown([100, 120, 90]) == pytest.approx(0.25)


def test_max_drawdown_no_drawdown():
    assert max_drawdown([1, 2, 3, 4]) == pytest.approx(0.0)


def test_drawdown_from_high_current_below_peak():
    assert drawdown_from_high([100, 130, 117]) == pytest.approx(0.1)  # 1-117/130


def test_drawdown_from_high_at_peak():
    assert drawdown_from_high([100, 110, 120]) == pytest.approx(0.0)


def test_slope_pct_rising_positive():
    assert slope_pct([100, 101, 102, 103], n=4) > 0


# ============================================================
# 2. classify_from_prices —— 体制判定
# ============================================================

def test_classify_strong_uptrend_is_bull():
    """持续上行(260日) → 牛市、score > 0、价格在 MA200 上方。"""
    r = classify_from_prices(_up(260, daily=0.002))
    assert r["regime"] == "牛市"
    assert r["regime_score"] > 0
    assert r["price_vs_ma200"] == "上方"
    assert r["ma200_slope"] == "上升"


def test_classify_strong_downtrend_is_bear():
    """持续下行 → 熊市、score < 0、价格在 MA200 下方。"""
    r = classify_from_prices(_down(260, daily=0.002))
    assert r["regime"] == "熊市"
    assert r["regime_score"] < 0
    assert r["price_vs_ma200"] == "下方"


def test_classify_short_series_returns_neutral():
    """序列过短(<60) → 数据不足中性。"""
    r = classify_from_prices(_up(40))
    assert r["regime"] == "震荡"
    assert "数据不足" in r["note"] or r["price_vs_ma200"] == "数据不足"


def test_classify_probabilities_sum_to_one():
    r = classify_from_prices(_up(260))
    assert sum(r["probabilities"].values()) == pytest.approx(1.0, abs=1e-3)


def test_classify_returns_all_expected_keys():
    r = classify_from_prices(_up(260))
    for k in ("regime", "probability", "probabilities", "regime_score",
              "drawdown_from_high", "price_vs_ma200", "ma200_slope",
              "distance_52w_high", "distance_52w_low"):
        assert k in r


# ============================================================
# 3. MarketRegimeClassifier 集成
# ============================================================

class _StubRegime(MarketRegimeClassifier):
    def _fetch_prices(self, code, days):
        return _up(days, daily=0.002)


def test_classifier_bull_on_rising_market():
    r = _StubRegime().classify("sh000001", days=260)
    assert isinstance(r, RegimeResult)
    assert r.regime == "牛市"
    assert r.regime_score > 0


def test_classifier_no_data_returns_neutral():
    r = MarketRegimeClassifier().classify("bad_code_xyz", days=260)
    # 联网失败 → 降级中性
    assert r.regime in ("震荡",)


# ============================================================
# 4. 波动率体制
# ============================================================

def test_realized_vol_positive_for_volatile_series():
    prices = [100, 105, 95, 108, 92, 110, 90]
    rv = realized_vol(prices, n=5)
    assert rv > 0


def test_realized_vol_low_for_smooth_series():
    smooth = _up(40, daily=0.001)
    rv = realized_vol(smooth, n=20)
    assert rv < 0.25


def test_vol_regime_label_high():
    assert vol_regime_label(0.30, 0.25) == "高波动"


def test_vol_regime_label_low():
    assert vol_regime_label(0.08, 0.10) == "低波动"


def test_vol_regime_label_expanding():
    # 20d 显著高于 60d
    assert vol_regime_label(0.20, 0.12) == "扩张"


def test_vol_regime_label_compressing():
    assert vol_regime_label(0.10, 0.18) == "压缩"


def test_is_bull_friendly_low_vol():
    assert is_bull_friendly(0.10, 0.12, "低波动") is True


def test_is_bull_friendly_high_vol_false():
    assert is_bull_friendly(0.30, 0.25, "高波动") is False


def test_vol_of_vol_positive():
    prices = [100 + 5 * math.sin(i / 3) + 0.1 * i for i in range(60)]
    assert vol_of_vol(prices, 20) >= 0.0


def test_vol_percentile_in_range():
    prices = _up(120, daily=0.003)
    pct = vol_percentile(prices, 20)
    assert 0.0 <= pct <= 100.0


def test_volatility_analyzer_from_prices():
    v = VolatilityRegimeAnalyzer().analyze_from_prices("test", _up(120, daily=0.001))
    assert isinstance(v, VolatilityResult)
    assert v.realized_vol_20d >= 0
    assert v.regime in ("低波动", "扩张", "高波动", "压缩", "中性", "未知")
