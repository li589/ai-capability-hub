# -*- coding: utf-8 -*-
"""v8.0.0 模块E：ML overlay + 进化闭环 track 测试（离线 mock，测试环境 sklearn 被屏蔽）"""

import sys
import types
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.fusion.multi_horizon_forecaster import (
    MultiHorizonForecaster, ForecastResult,
)


def _mk_fr(horizon="1d", prob_up=60.0):
    return ForecastResult(
        horizon=horizon, horizon_days=1, direction="看多", predicted_pct=2.0,
        p10=-1, p50=2, p90=5, prob_up=prob_up, confidence=0.7,
        composite_score=15, top_drivers=[], risk_factors=[], narrative="",
    )


# ============================================================
# 1. _kline_to_ohlcv
# ============================================================

def test_kline_to_ohlcv():
    f = MultiHorizonForecaster()
    kline = {"dates": ["d1", "d2"], "opens": [1, 2], "highs": [1.5, 2.5],
             "lows": [0.5, 1.5], "closes": [1, 2], "volumes": [100, 200]}
    ohlcv = f._kline_to_ohlcv(kline)
    assert len(ohlcv) == 2
    assert ohlcv[0]["close"] == 1.0
    assert ohlcv[1]["volume"] == 200


def test_kline_to_ohlcv_empty():
    assert MultiHorizonForecaster._kline_to_ohlcv(None) == []
    assert MultiHorizonForecaster._kline_to_ohlcv({}) == []


def test_kline_to_ohlcv_missing_fields():
    """缺 open/high/low/volume 时用 close 兜底"""
    f = MultiHorizonForecaster()
    ohlcv = f._kline_to_ohlcv({"closes": [10, 11]})
    assert ohlcv[0]["open"] == 10.0
    assert ohlcv[0]["high"] == 10.0


# ============================================================
# 2. ML overlay 降级（无 sklearn 环境）
# ============================================================

def test_ml_overlay_noop_without_sklearn():
    """测试环境 sklearn 被屏蔽 → import ml_predictor 失败 → 静默 no-op"""
    f = MultiHorizonForecaster()
    fr = _mk_fr("1d", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 70})
    assert out.prob_up == 60.0  # 未改变


def test_ml_overlay_ignores_long_horizon():
    """仅 1d/3d/5d 叠加；1M/1Q 不处理"""
    f = MultiHorizonForecaster()
    fr = _mk_fr("1M", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 70})
    assert out.prob_up == 60.0


def test_ml_overlay_insufficient_data():
    """OHLCV < 60 条时不叠加"""
    f = MultiHorizonForecaster()
    fr = _mk_fr("1d", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 30})
    assert out.prob_up == 60.0


# ============================================================
# 3. ML overlay 可用时（模拟 sklearn 环境）
# ============================================================

def _install_fake_ml(monkeypatch, mres):
    fake = types.ModuleType("ml_predictor")
    fake.ml_available = lambda: True

    class FakeMHP:
        def __init__(self, *a, **k):
            pass

        def train_and_predict(self, ohlcv):
            return mres

    fake.MultiHorizonMLPredictor = FakeMHP
    monkeypatch.setitem(sys.modules, "stock_researcher.quantitative.ml_predictor", fake)


def test_ml_overlay_blends_when_available(monkeypatch):
    """ML prob_up 0.9(90) 与 MC 60 混合 → 0.6*60+0.4*90 = 72"""
    _install_fake_ml(monkeypatch, {"1d": {"prob_up": 0.9, "confidence": 0.8}})
    f = MultiHorizonForecaster()
    fr = _mk_fr("1d", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 70})
    assert abs(out.prob_up - 72.0) < 0.5
    assert "ML叠加" in out.narrative


def test_ml_overlay_ignores_low_confidence(monkeypatch):
    """ML 置信度 < 0.5 时不改写"""
    _install_fake_ml(monkeypatch, {"1d": {"prob_up": 0.95, "confidence": 0.2}})
    f = MultiHorizonForecaster()
    fr = _mk_fr("1d", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 70})
    assert out.prob_up == 60.0


def test_ml_overlay_ignores_small_divergence(monkeypatch):
    """ML 与 MC 分歧 < 15 时不改写"""
    _install_fake_ml(monkeypatch, {"1d": {"prob_up": 0.68, "confidence": 0.8}})  # 68 vs 60 差 8
    f = MultiHorizonForecaster()
    fr = _mk_fr("1d", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 70})
    assert out.prob_up == 60.0


def test_ml_overlay_missing_horizon(monkeypatch):
    """ML 结果不含该 horizon 时不叠加"""
    _install_fake_ml(monkeypatch, {"3d": {"prob_up": 0.9, "confidence": 0.8}})
    f = MultiHorizonForecaster()
    fr = _mk_fr("1d", 60.0)
    out = f._ml_overlay(fr, {"closes": [1.0] * 70})
    assert out.prob_up == 60.0


# ============================================================
# 4. 进化闭环 track
# ============================================================

def _install_fake_tracker(monkeypatch):
    calls = []

    class FakeTracker:
        def __init__(self):
            pass

        def new_record(self, *a):
            calls.append(a)
            return None

    fake = types.ModuleType("pt")
    fake.PredictionTracker = FakeTracker
    monkeypatch.setitem(sys.modules, "stock_researcher.evolution.prediction_tracker", fake)
    return calls


def test_track_writes_records(monkeypatch):
    calls = _install_fake_tracker(monkeypatch)
    f = MultiHorizonForecaster()
    hresults = {"1d": _mk_fr("1d", 60.0), "1M": _mk_fr("1M", 55.0)}
    f._track_predictions("stock", "600519", hresults)
    assert len(calls) == 2
    assert calls[0][0] == "stock"
    assert calls[0][1] == "600519"


def test_track_no_records_when_empty():
    f = MultiHorizonForecaster()
    f._track_predictions("stock", "600519", None)  # 不抛


def test_forecast_methods_have_track_param():
    import inspect
    sig = inspect.signature(MultiHorizonForecaster.forecast_stock)
    assert "track" in sig.parameters
    assert sig.parameters["track"].default is False
    sig2 = inspect.signature(MultiHorizonForecaster.forecast_asset)
    assert "track" in sig2.parameters
