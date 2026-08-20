# -*- coding: utf-8 -*-
"""v9.0 宏观情景引擎 + 预测校准 测试（离线）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.quantitative.scenario_engine import (
    SCENARIO_DEFS, DEFAULT_PROBABILITIES, scenario_return, weighted_outcomes,
    blend_report, sample_scenario_path, MacroScenarioEngine,
)
from stock_researcher.evolution.calibration import (
    bucket_reliability, brier_score, expected_calibration_error,
    isotonic_fit, calibrate_value, PredictionCalibrator,
)


# ============================================================
# 1. 情景引擎
# ============================================================

def test_scenario_return_soft_landing_boosts():
    """软着陆：漂移+0.04 → 预期收益高于基准。"""
    r, v = scenario_return(0.10, 0.18, "软着陆")
    assert r > 0.10
    assert v < 0.18   # 波动缩小


def test_scenario_return_hard_landing_lowers():
    r, v = scenario_return(0.10, 0.18, "硬着陆")
    assert r < 0.10
    assert v > 0.18


def test_scenario_return_unknown_returns_base():
    r, v = scenario_return(0.10, 0.18, "不存在的情景")
    assert r == 0.10 and v == 0.18


def test_default_probabilities_sum_to_one():
    assert sum(DEFAULT_PROBABILITIES.values()) == pytest.approx(1.0)


def test_blend_report_probabilities_normalized():
    rep = blend_report(0.08, 0.20, {"软着陆": 2.0, "硬着陆": 2.0})
    assert sum(rep.probabilities.values()) == pytest.approx(1.0)


def test_blend_report_weighted_between_tail_and_best():
    rep = blend_report(0.08, 0.20)
    assert rep.tail_risk <= rep.weighted_return <= rep.best_case
    assert rep.tail_risk < 0   # 至少有一个下行情景


def test_blend_report_upside_probability_range():
    rep = blend_report(0.08, 0.20)
    assert 0.0 <= rep.upside_probability <= 1.0


def test_blend_report_outcomes_have_rationale():
    rep = blend_report(0.08, 0.20)
    for o in rep.outcomes:
        assert o.rationale
        assert o.asset_tilt  # 资产偏好非空


def test_sample_scenario_path_returns_list():
    paths = sample_scenario_path(0.08, 0.20, "硬着陆", horizon_days=21, sims=200)
    assert len(paths) == 200
    # 硬着陆偏下行：多数路径应为负或低
    assert any(p < 0 for p in paths)


def test_macro_engine_list_and_analyze():
    eng = MacroScenarioEngine()
    assert "软着陆" in eng.list_scenarios()
    rep = eng.analyze(0.08, 0.20)
    assert rep.weighted_return is not None
    assert isinstance(rep.outcomes, list) and len(rep.outcomes) > 0


def test_tail_var_negative_for_hard_landing():
    eng = MacroScenarioEngine()
    var = eng.tail_var(0.08, 0.20, "硬着陆", horizon_days=21, sims=300, quantile=0.05)
    assert var < 0   # 5% 分位应为负（下行）


# ============================================================
# 2. 预测校准
# ============================================================

def test_bucket_reliability_basic():
    pairs = [(0.2, 0), (0.2, 0), (0.8, 1), (0.8, 1), (0.5, 1)]
    rel = bucket_reliability(pairs)
    assert len(rel) >= 1
    for b in rel:
        assert 0 <= b["hit_rate"] <= 1
        assert b["count"] > 0


def test_brier_score_perfect():
    """完美校准（conf=hit）→ Brier=0。"""
    assert brier_score([(0.0, 0), (1.0, 1), (0.0, 0)]) == pytest.approx(0.0)


def test_brier_score_worst():
    """完全反向（conf=1 全 miss）→ Brier=1。"""
    assert brier_score([(1.0, 0), (1.0, 0)]) == pytest.approx(1.0)


def test_brier_score_empty():
    assert brier_score([]) == 0.0


def test_expected_calibration_error_zero_when_perfect():
    pairs = [(0.2, 0.2 > 0.5), (0.8, 0.8 > 0.5)]  # placeholder
    # 直接构造完美可靠性
    rel = [{"count": 10, "avg_conf": 0.2, "hit_rate": 0.2},
           {"count": 10, "avg_conf": 0.8, "hit_rate": 0.8}]
    assert expected_calibration_error(rel, 20) == pytest.approx(0.0)


def test_isotonic_fit_monotonic():
    """PAV 保序回归结果应单调非降。"""
    pairs = [(0.3, 0), (0.4, 1), (0.5, 0), (0.6, 1), (0.7, 1), (0.8, 1)]
    fitted = isotonic_fit(pairs)
    ys = [y for _, y in fitted]
    for i in range(1, len(ys)):
        assert ys[i] >= ys[i - 1] - 1e-9   # 非降


def test_isotonic_fit_empty():
    assert isotonic_fit([]) == []


def test_calibrate_value_empty_returns_original():
    assert calibrate_value(0.7, []) == 0.7


def test_calibrate_value_within_range():
    """校准值应落在拟合数据的 y 范围内。"""
    pairs = [(0.2, 0)] * 10 + [(0.8, 1)] * 10
    fitted = isotonic_fit(pairs)
    cal = calibrate_value(0.5, fitted)
    assert fitted[0][1] - 1e-6 <= cal <= fitted[-1][1] + 1e-6


def test_calibrator_no_history_returns_original():
    """无历史数据 → calibrate 原样返回（诚实）。"""
    cal = PredictionCalibrator()
    out = cal.calibrate(0.7, horizon="1M")
    assert out == 0.7


def test_calibrator_build_with_synthetic(monkeypatch):
    """注入合成历史，验证 build 返回可靠性 + Brier。"""
    cal = PredictionCalibrator()
    # 构造 40 条：低 conf 多 miss，高 conf 多 hit
    pairs = [(0.2, 0)] * 15 + [(0.3, 0)] * 5 + [(0.7, 1)] * 10 + [(0.8, 1)] * 10
    monkeypatch.setattr(cal, "_load_pairs", lambda *a, **k: pairs)
    res = cal.build(horizon="1M")
    assert res.n_samples == 40
    assert res.sufficient is True
    assert 0 <= res.brier <= 1
    assert len(res.reliability) >= 1
