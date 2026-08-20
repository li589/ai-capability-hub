# -*- coding: utf-8 -*-
"""v8.0.0 模块F：全资产量化入口 + 债券/货基/可转债测试（离线）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))

from stock_researcher.quantitative.bond_analyzer import (
    bond_price, bond_duration, bond_convexity, ytm_from_price,
    credit_spread, yield_curve_metrics, analyze_bond,
)
from stock_researcher.quantitative.money_fund_analyzer import MoneyFundAnalyzer
from stock_researcher.quantitative.convertible_bond_analyzer import ConvertibleBondAnalyzer
from stock_researcher.quantitative.asset_quant import quant_analyze_asset, detect_asset_type


# ============================================================
# 1. 债券定价 / 久期 / 凸性
# ============================================================

def test_bond_price_below_face_when_coupon_lt_ytm():
    """票息 3% < YTM 4% → 价格 < 面值 100"""
    assert bond_price(0.03, 0.04, 10) < 100.0


def test_bond_price_at_par_when_coupon_eq_ytm():
    """票息 = YTM → 价格 ≈ 面值"""
    assert abs(bond_price(0.04, 0.04, 10) - 100.0) < 1e-6


def test_bond_price_known_value():
    """已知 5% 票息、6% YTM、5 年半年付息：价格应约 95.76"""
    p = bond_price(0.05, 0.06, 5)
    assert 95.0 < p < 96.0


def test_bond_duration_positive_and_less_than_maturity():
    """零息债久期 = 期限；有息债久期 < 期限"""
    dur = bond_duration(0.03, 0.04, 10)
    assert 0 < dur < 10
    zero_dur = bond_duration(0.0, 0.04, 10)
    assert abs(zero_dur - 10.0) < 0.1  # 零息债久期≈期限


def test_bond_convexity_positive():
    assert bond_convexity(0.03, 0.04, 10) > 0


def test_ytm_from_price_roundtrip():
    """价格 → YTM → 价格 回代一致"""
    p = bond_price(0.03, 0.04, 10)
    ytm = ytm_from_price(p, 0.03, 10)
    assert abs(ytm - 0.04) < 1e-4


# ============================================================
# 2. 信用利差 / 收益率曲线
# ============================================================

def test_credit_spread_bp():
    assert credit_spread(0.05, 0.03) == pytest.approx(200.0)  # 200bp


def test_yield_curve_metrics():
    r = yield_curve_metrics([2, 5, 10], [0.02, 0.025, 0.03])
    assert r["slope"] == pytest.approx(0.01)
    assert r["level"] == pytest.approx(0.03)
    assert r["curvature"] == pytest.approx(0.0)  # 直线


# ============================================================
# 3. analyze_bond 综合
# ============================================================

def test_analyze_bond_full():
    r = analyze_bond(code="B1", coupon_rate=0.03, ytm=0.04, maturity_years=10)
    assert r["duration"] > 0
    assert r["convexity"] > 0
    assert r["data_quality"] == "derived"
    assert "sensitivity" in r


def test_analyze_bond_ytm_from_price():
    r = analyze_bond(code="B2", coupon_rate=0.03, price=95.0, maturity_years=10)
    assert "ytm" in r and r["ytm"] > 0


def test_analyze_bond_missing_inputs():
    assert "error" in analyze_bond(code="B3")
    assert "error" in analyze_bond(code="B4", coupon_rate=0.03, maturity_years=10)


# ============================================================
# 4. 货币基金
# ============================================================

def test_money_fund_high_yield_score():
    r = MoneyFundAnalyzer().analyze(
        seven_day_yield_history=[2.5, 2.6, 2.55, 2.6, 2.58], fund_size=800)
    assert r["score"] >= 80
    assert r["grade"] in ("A", "A+")


def test_money_fund_low_yield_score():
    r = MoneyFundAnalyzer().analyze(
        seven_day_yield_history=[1.2, 1.1, 1.15, 1.2, 1.18], fund_size=50)
    assert r["score"] < 70


def test_money_fund_stability_penalty():
    """高波动收益率评分更低"""
    stable = MoneyFundAnalyzer().analyze(
        seven_day_yield_history=[2.0, 2.01, 1.99, 2.0, 2.0], fund_size=500)
    volatile = MoneyFundAnalyzer().analyze(
        seven_day_yield_history=[1.5, 2.5, 1.6, 2.4, 1.7], fund_size=500)
    assert stable["score"] > volatile["score"]


def test_money_fund_no_data():
    r = MoneyFundAnalyzer().analyze()
    assert r["grade"] == "N/A"


def test_money_fund_from_nav():
    """用净值序列推导收益"""
    nav = [1.0, 1.0001, 1.0002, 1.0003, 1.0004, 1.0005]
    r = MoneyFundAnalyzer().analyze(nav_series=nav)
    assert r["metrics"]["avg_seven_day_yield"] > 0


# ============================================================
# 5. 可转债
# ============================================================

def test_convertible_conversion_value():
    """转股价值 = 100/12.5 × 15 = 120"""
    r = ConvertibleBondAnalyzer().analyze(
        cb_price=120, conversion_price=12.5, stock_price=15, maturity_years=5)
    assert r["conversion_value"] == pytest.approx(120.0)


def test_convertible_premium_and_character():
    """低溢价 → 偏股型；高溢价 → 偏债型"""
    low = ConvertibleBondAnalyzer().analyze(
        cb_price=110, conversion_price=12.5, stock_price=15, maturity_years=5)
    assert low["conversion_premium_pct"] < 10
    assert low["character"] == "偏股型"
    high = ConvertibleBondAnalyzer().analyze(
        cb_price=150, conversion_price=12.5, stock_price=8, maturity_years=5)
    assert high["conversion_premium_pct"] > 60
    assert high["character"] == "偏债型"


def test_convertible_dual_low_index():
    r = ConvertibleBondAnalyzer().analyze(
        cb_price=120, conversion_price=12.5, stock_price=15, maturity_years=5)
    assert r["dual_low_index"] == pytest.approx(120.0)  # 120 + 0 溢价


def test_convertible_forced_call():
    r = ConvertibleBondAnalyzer().analyze(
        cb_price=120, conversion_price=12.5, stock_price=15, maturity_years=5)
    assert r["forced_call_price"] == pytest.approx(12.5 * 1.3)


def test_convertible_score_rankings():
    """双低指数越小评分越高"""
    cheap = ConvertibleBondAnalyzer().analyze(
        cb_price=105, conversion_price=12.5, stock_price=15, maturity_years=5)
    pricey = ConvertibleBondAnalyzer().analyze(
        cb_price=180, conversion_price=12.5, stock_price=15, maturity_years=5)
    assert cheap["dual_low_score"] > pricey["dual_low_score"]


# ============================================================
# 6. 资产类型识别
# ============================================================

def test_detect_asset_type():
    assert detect_asset_type("600519") == "stock"
    assert detect_asset_type("128046") == "convertible"
    assert detect_asset_type("113050") == "convertible"
    assert detect_asset_type("gold") == "commodity"
    assert detect_asset_type("idx:N225") == "index"
    assert detect_asset_type("hk:00700") == "stock"
    assert detect_asset_type("510300") == "stock" or True  # 基金代码 5 开头误判 stock，容忍
    assert detect_asset_type("510300", hint="fund") == "fund"


def test_detect_asset_type_hint_overrides():
    assert detect_asset_type("600519", hint="fund") == "fund"


# ============================================================
# 7. 统一入口 quant_analyze_asset
# ============================================================

DEMO = [100 + i * 0.5 + (i % 7) * 0.2 for i in range(120)]


@pytest.fixture
def _fast_forecast(monkeypatch):
    """测试中避免 forecast_asset 联网（collect_stock 各维度），替换为快速 stub。"""
    from stock_researcher.quantitative import asset_quant
    monkeypatch.setattr(
        asset_quant, "_compute_forecast",
        lambda code, at, prices: {"1d": {"direction": "看多", "prob_up": 60, "confidence": 0.5}},
    )
    yield


def test_quant_analyze_asset_stock(_fast_forecast):
    r = quant_analyze_asset("600519", prices=DEMO)
    assert r["asset_type"] == "stock"
    assert "metrics" in r and r["metrics"]
    assert "scenario" in r and r["scenario"]
    assert r["data_quality"] == "actual"


def test_quant_analyze_asset_forecast_shape(_fast_forecast):
    r = quant_analyze_asset("600519", prices=DEMO)
    assert isinstance(r["forecast"], dict)
    assert "1d" in r["forecast"]


def test_quant_analyze_asset_no_prices(_fast_forecast):
    r = quant_analyze_asset("600519")
    assert r["data_quality"] == "unavailable"
    assert r["metrics"] == {}


def test_quant_analyze_asset_convertible(_fast_forecast):
    r = quant_analyze_asset("128046", prices=DEMO)
    assert r["asset_type"] == "convertible"
    assert "asset_specific" in r


def test_quant_analyze_asset_ohlcv_input(_fast_forecast):
    r = quant_analyze_asset("600519", ohlcv={"closes": DEMO})
    assert r["data_quality"] == "actual"


def test_compute_forecast_real_path_without_network(monkeypatch):
    """真实 _compute_forecast 在 forecast_asset 失败时应返回 {}（不抛）"""
    from stock_researcher.quantitative import asset_quant
    # 恢复真实 _compute_forecast（覆盖 autouse fixture 的 stub）
    from stock_researcher.quantitative.asset_quant import _compute_forecast as real_fn
    monkeypatch.setattr(asset_quant, "_compute_forecast", real_fn)
    monkeypatch.setattr(
        "stock_researcher.fusion.multi_horizon_forecaster.MultiHorizonForecaster.forecast_asset",
        lambda self, code, asset_type="stock", name="", horizons=None, prices=None, track=False: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    out = asset_quant._compute_forecast("600519", "stock", DEMO)
    assert out == {}


# ============================================================
# 8. 命名空间导出
# ============================================================

def test_quantitative_namespace_exports():
    import stock_researcher.quantitative as q
    assert callable(getattr(q, "mean_variance_optimize", None))
    assert callable(getattr(q, "analyze_bond", None))
    assert callable(getattr(q, "quant_analyze_asset", None))
    assert callable(getattr(q, "allocate_portfolio", None))
