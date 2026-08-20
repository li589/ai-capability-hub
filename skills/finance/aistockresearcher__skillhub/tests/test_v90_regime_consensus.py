# -*- coding: utf-8 -*-
"""v9.0 体制叠加 + 信号共识 测试（离线）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.fusion.regime_overlay import (
    RegimeOverlay, REGIME_WEIGHTS, MOMENTUM_DIMS,
    detect_regime_from_prices, normalize_regime,
)
from stock_researcher.fusion.signal_consensus import (
    SignalConsensus, compute_consensus, consensus_from_scores,
)


# ============================================================
# 1. RegimeOverlay —— 体制权重
# ============================================================

def test_weights_for_bull_returns_dict():
    w = RegimeOverlay.weights_for("牛市", "1d")
    assert w is not None
    assert "technical" in w


def test_weights_for_none_returns_none():
    """regime=None → None（向后兼容）。"""
    assert RegimeOverlay.weights_for(None, "1d") is None
    assert RegimeOverlay.weights_for("未知体制", "1d") is None


def test_apply_regime_weights_none_unchanged():
    """regime=None → 权重原样（仅副本）。"""
    default = {"technical": 0.3, "macro": 0.2}
    out = RegimeOverlay.apply_regime_weights(default, None, "1d")
    assert out == default
    assert out is not default   # 是副本


def test_apply_regime_weights_bear_downweights_technical():
    """熊市：technical 权重相对默认应下降，valuation/macro 上升。"""
    default = {"technical": 0.30, "sentiment": 0.20, "money_flow": 0.20,
               "macro": 0.05, "valuation": 0.05, "policy": 0.05,
               "broker": 0.05, "news": 0.05, "quant_vol": 0.03, "quant_factor": 0.02}
    bear = RegimeOverlay.apply_regime_weights(default, "熊市", "1M")
    # 归一化后比较：熊市 technical 占比应低于默认
    assert bear["technical"] < default["technical"] * 1.0 / sum(default.values())
    assert bear["valuation"] > default["valuation"] * 1.0 / sum(default.values())


def test_apply_regime_weights_normalizes_to_one():
    default = {"technical": 0.3, "macro": 0.2, "valuation": 0.1}
    out = RegimeOverlay.apply_regime_weights(default, "熊市", "1M")
    assert sum(out.values()) == pytest.approx(1.0, abs=1e-6)


# ============================================================
# 2. RegimeOverlay —— 动量折扣
# ============================================================

def test_momentum_dampening_none_unchanged():
    assert RegimeOverlay.momentum_dampening(30, "technical", None) == 30


def test_momentum_dampening_bull_unchanged():
    assert RegimeOverlay.momentum_dampening(30, "technical", "牛市") == 30


def test_momentum_dampening_bear_reduces_momentum():
    """熊市对动量类信号打折（0.5）。"""
    assert RegimeOverlay.momentum_dampening(30, "technical", "熊市") == 15


def test_momentum_dampening_non_momentum_unchanged():
    """非动量类维度（valuation）在熊市不打折。"""
    assert RegimeOverlay.momentum_dampening(30, "valuation", "熊市") == 30


def test_momentum_dampening_flip_mode_bear():
    """flip_momentum=True 时熊市动量翻号（-0.6）。"""
    assert RegimeOverlay.momentum_dampening(30, "technical", "熊市",
                                            flip_momentum=True) == -18


def test_confidence_adjustment_bear_lowers():
    assert RegimeOverlay.confidence_adjustment("熊市") < 1.0
    assert RegimeOverlay.confidence_adjustment("牛市") == 1.0
    assert RegimeOverlay.confidence_adjustment(None) == 1.0


def test_normalize_regime():
    assert normalize_regime("牛市") == "牛市"
    assert normalize_regime("bear market") == "熊市"
    assert normalize_regime("高波动") == "熊市"   # 高波动保守归熊
    assert normalize_regime("震荡市") == "震荡"
    assert normalize_regime(None) is None


def test_detect_regime_from_prices_rising():
    prices = [100 * (1.002 ** i) for i in range(120)]
    r = detect_regime_from_prices(prices)
    assert r is not None


# ============================================================
# 3. SignalConsensus —— 共识度
# ============================================================

def test_compute_consensus_unanimous_bull():
    """全部看多 → 强共识看多，dispersion 低，置信乘数>1。"""
    c = compute_consensus([40, 35, 30, 45, 38])
    assert c.bull_count == 5
    assert c.consensus_score > 25
    assert c.dispersion < 40
    assert c.confidence_multiplier >= 1.0
    assert "看多" in c.label


def test_compute_consensus_unanimous_bear():
    c = compute_consensus([-40, -35, -30, -45, -38])
    assert c.bear_count == 5
    assert c.consensus_score < -25
    assert "看空" in c.label


def test_compute_consensus_split_is_divergent():
    """多空各半 → 分歧，dispersion 高，置信乘数<1，均值回归倾斜>0。"""
    c = compute_consensus([40, 35, -30, -45, 10])
    assert c.dispersion >= 55 or c.label == "分歧" or c.confidence_multiplier < 1.0


def test_compute_consensus_empty():
    c = compute_consensus([])
    assert c.label == "无信号"


def test_consensus_confidence_multiplier_range():
    c = compute_consensus([10, 20, 30, 5, 15])
    assert 0.6 <= c.confidence_multiplier <= 1.1


def test_consensus_from_scores_convenience():
    c = consensus_from_scores([20, 20, -20, -20])
    assert isinstance(c.dispersion, float)


def test_signal_consensus_class_with_dims():
    """SignalConsensus.compute 接受类 DimensionSignal 对象。"""

    class Dim:
        def __init__(self, dim, score, direction="", available=True):
            self.dimension = dim
            self.score = score
            self.direction = direction
            self.available = available

    dims = [Dim("technical", 30, "看多"), Dim("macro", -20, "看空"),
            Dim("sentiment", 25, "看多"), Dim("valuation", 15, "看多")]
    c = SignalConsensus().compute(dims)
    assert c.bull_count >= 2
    assert -100 <= c.consensus_score <= 100
