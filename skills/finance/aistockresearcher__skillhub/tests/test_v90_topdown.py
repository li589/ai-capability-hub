# -*- coding: utf-8 -*-
"""v9.0 自上而下整合 + 宏观序列 + 包根导出 测试（离线）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))

from stock_researcher.data.macro_series import (
    _slope_of, trend_label, build_result, MacroSeriesResult,
)
from stock_researcher.data.index_constituents import (
    FALLBACK_BASKET, IndexConstituents,
)
from stock_researcher.analysis.top_down import (
    TopDownReport, TopDownResult, build_topdown,
)


# ============================================================
# 1. macro_series 纯函数
# ============================================================

def test_slope_of_rising_positive():
    assert _slope_of([100, 101, 102, 103, 104]) > 0


def test_slope_of_falling_negative():
    assert _slope_of([104, 103, 102, 101, 100]) < 0


def test_trend_label_rising():
    assert trend_label(0.5, [100, 102, 104, 106], recent_n=3) == "回升"


def test_trend_label_falling():
    assert trend_label(-0.5, [106, 104, 102, 100], recent_n=3) == "回落"


def test_trend_label_insufficient():
    assert trend_label(0.5, [1, 2], recent_n=3) == "数据不足"


def test_build_result_shape():
    r = build_result("pmi", [50.0, 50.5, 51.0, 51.5], ["2025-01", "2025-02", "2025-03", "2025-04"])
    assert isinstance(r, MacroSeriesResult)
    assert r.latest == pytest.approx(51.5)
    assert r.trend == "回升"
    assert len(r.values) == 4
    assert r.momentum_3 == pytest.approx(1.0)   # 51.5-50.5


def test_build_result_empty_values():
    r = build_result("pmi", [], [])
    assert r.latest is None


# ============================================================
# 2. index_constituents 兜底篮子
# ============================================================

def test_fallback_basket_covers_major_indices():
    for code in ("sh000300", "sz399006", "sh000688", "100.SPX", "100.HSI"):
        assert len(FALLBACK_BASKET.get(code, [])) >= 6


def test_index_constituents_no_network_returns_fallback():
    """网络禁用时返回精选篮子（真实数据兜底）。"""
    codes = IndexConstituents(use_network=False).get("sh000300")
    assert len(codes) >= 10
    assert "600519" in codes


def test_index_constituents_unknown_returns_empty():
    codes = IndexConstituents(use_network=False).get("unknown_idx")
    assert codes == []


# ============================================================
# 3. TopDownReport 整合
# ============================================================

def test_topdown_result_structure_defaults():
    """未填充时结构完整（字段齐全）。"""
    r = TopDownResult(market="cn")
    assert r.position_tilt == "中性"
    assert r.top_sectors == []
    assert r.risk_factors == []


def test_topdown_build_degrades_gracefully_without_network(monkeypatch):
    """网络环节全部失败时 build 不抛异常，返回结构完整的结果。"""
    rep = TopDownReport()
    monkeypatch.setattr(rep, "_fill_regime", lambda res, bench: None)
    monkeypatch.setattr(rep, "_fill_cycle", lambda res, market: None)
    monkeypatch.setattr(rep, "_fill_sectors", lambda res, market, n: None)
    monkeypatch.setattr(rep, "_fill_index_health", lambda res, bench, market: None)
    r = rep.build(market="cn")
    assert isinstance(r, TopDownResult)
    assert r.market == "cn"
    assert r.benchmark == "sh000001"
    assert r.position_tilt in ("进攻", "中性", "防御")
    assert isinstance(r.summary, str)


def test_topdown_build_us_market(monkeypatch):
    """us 市场基准映射正确（网络环节存根）。"""
    rep = TopDownReport()
    monkeypatch.setattr(rep, "_fill_regime", lambda res, bench: None)
    monkeypatch.setattr(rep, "_fill_cycle", lambda res, market: None)
    monkeypatch.setattr(rep, "_fill_sectors", lambda res, market, n: None)
    monkeypatch.setattr(rep, "_fill_index_health", lambda res, bench, market: None)
    r = rep.build(market="us")
    assert r.market == "us"
    assert r.benchmark == "100.SPX"


def test_topdown_synthesize_position_tilt_logic():
    """熊市 → 防御；强牛市 → 进攻（纯逻辑验证）。"""
    r = TopDownResult(market="cn")
    r.regime = "熊市"
    r.regime_score = -50
    TopDownReport()._synthesize(r)
    assert r.position_tilt == "防御"
    assert any("熊市" in f for f in r.risk_factors)

    r2 = TopDownResult(market="cn")
    r2.regime = "牛市"
    r2.regime_score = 60
    TopDownReport()._synthesize(r2)
    assert r2.position_tilt == "进攻"


def test_topdown_favored_themes_intersection():
    """favored_themes = 周期受益 ∩ RPS 强势（交集优先）。"""
    r = TopDownResult(market="cn")
    r.cycle_favored = ["银行", "电子", "汽车"]
    r.top_sectors = [
        {"sector": "电子", "rps": 40, "percentile": 80, "trend": "上升", "data_mode": "proxy"},
        {"sector": "计算机", "rps": 30, "percentile": 70, "trend": "上升", "data_mode": "proxy"},
    ]
    TopDownReport()._synthesize(r)
    assert "电子" in r.favored_themes   # 交集命中


def test_topdown_format_is_string():
    r = TopDownResult(market="cn")
    r.summary = "测试摘要"
    text = TopDownReport.format(r)
    assert isinstance(text, str)
    assert "CN" in text


def test_build_topdown_convenience():
    r = build_topdown(market="hk")
    assert isinstance(r, TopDownResult)


# ============================================================
# 4. 包根 v9.0 懒导出
# ============================================================

def _real_root_module():
    """取真实 stock_researcher 根模块。

    注意：test_v71_analysis 在收集期向 sys.modules 注入了一个「假根模块」
    （裸 ModuleType，无 __file__/__getattr__），使真实包 __init__.py 从未
    执行。本辅助函数检测到假根模块时强制重导入真实包（子模块已在
    sys.modules 中，重导入不会重复执行）。
    """
    import sys
    mod = sys.modules.get("stock_researcher")
    if mod is not None and not hasattr(mod, "__file__"):
        sys.modules.pop("stock_researcher", None)
    import stock_researcher
    return stock_researcher


def test_root_lazy_export_sector():
    sr = _real_root_module()
    srs = sr.SectorRelativeStrength
    assert srs is not None


def test_root_lazy_export_regime():
    sr = _real_root_module()
    mrc = sr.MarketRegimeClassifier
    assert mrc is not None


def test_root_lazy_export_scenario_and_topdown():
    sr = _real_root_module()
    assert sr.MacroScenarioEngine is not None
    assert sr.TopDownReport is not None
    assert sr.PredictionCalibrator is not None


def test_root_lazy_export_unknown_raises():
    sr = _real_root_module()
    with pytest.raises(AttributeError):
        sr.不存在的属性xyz
