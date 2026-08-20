# -*- coding: utf-8 -*-
"""v8.0.0 模块D：蒙特卡洛增强测试（跳跃扩散 + 肥尾 t 分布）"""

import math
import random
import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.quantitative.scenario_simulator import (
    _simulate_std_t, _simulate_paths, _simulate_gbm_paths,
    quick_scenario_forecast, ScenarioSimulator,
)


def _sample_kurtosis(samples):
    n = len(samples)
    mean = sum(samples) / n
    m2 = sum((x - mean) ** 2 for x in samples) / n
    m4 = sum((x - mean) ** 4 for x in samples) / n
    return m4 / (m2 ** 2) - 3 if m2 > 1e-12 else 0.0


def _std_normal_samples(rng, n):
    out = []
    for _ in range(n):
        u1 = rng.random()
        u2 = rng.random()
        if u1 <= 0:
            u1 = 1e-12
        out.append(math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2))
    return out


# ============================================================
# 1. 肥尾 t 分布
# ============================================================

def test_t_distribution_kurtosis_greater_than_normal():
    """t(6) 样本峰度显著高于正态（肥尾）"""
    rng = random.Random(7)
    t_samp = [_simulate_std_t(rng, 6) for _ in range(20000)]
    rng2 = random.Random(7)
    n_samp = _std_normal_samples(rng2, 20000)
    assert _sample_kurtosis(t_samp) > 1.5, f"t 分布应肥尾，峰度 {_sample_kurtosis(t_samp):.2f}"
    assert _sample_kurtosis(n_samp) < 0.5


def test_t_distribution_lower_dof_fatter_tail():
    """自由度越低尾越肥"""
    rng = random.Random(1)
    t2 = [_simulate_std_t(rng, 4) for _ in range(15000)]
    rng = random.Random(1)
    t20 = [_simulate_std_t(rng, 20) for _ in range(15000)]
    assert _sample_kurtosis(t2) > _sample_kurtosis(t20)


def test_std_t_returns_finite():
    rng = random.Random(3)
    vals = [_simulate_std_t(rng, 6) for _ in range(500)]
    assert all(math.isfinite(v) for v in vals)


# ============================================================
# 2. 跳跃扩散
# ============================================================

def test_jumps_increase_dispersion():
    """启用跳跃后路径收益离散度更大"""
    no_jump = _simulate_paths(100, 0, 0.02, 30, 2000, seed=1, use_jumps=False)
    jump = _simulate_paths(100, 0, 0.02, 30, 2000, seed=1, use_jumps=True,
                           lambda_jump=0.2, jump_vol=0.05)
    mean_abs = lambda xs: sum(abs(x) for x in xs) / len(xs)
    assert mean_abs(jump) > mean_abs(no_jump)


def test_jump_vol_higher_more_extreme():
    """跳跃波动越大，极端损失更常见"""
    mild = _simulate_paths(100, 0, 0.02, 30, 1500, seed=5, use_jumps=True,
                           lambda_jump=0.3, jump_vol=0.02)
    severe = _simulate_paths(100, 0, 0.02, 30, 1500, seed=5, use_jumps=True,
                             lambda_jump=0.3, jump_vol=0.08)
    assert min(severe) < min(mild)


def test_same_seed_deterministic():
    """同种子同参数 → 同结果（可复现）"""
    a = _simulate_paths(100, 0.001, 0.02, 20, 300, seed=42, distribution="t",
                        use_jumps=True, lambda_jump=0.1, jump_vol=0.03, dof=5)
    b = _simulate_paths(100, 0.001, 0.02, 20, 300, seed=42, distribution="t",
                        use_jumps=True, lambda_jump=0.1, jump_vol=0.03, dof=5)
    assert a == b


# ============================================================
# 3. 向后兼容（默认行为不变）
# ============================================================

def test_default_matches_old_gbm():
    """_simulate_gbm_paths 与 _simulate_paths(normal, 无跳跃) 同种子同结果"""
    g = _simulate_gbm_paths(100, 0.001, 0.02, 20, 200, seed=42)
    p = _simulate_paths(100, 0.001, 0.02, 20, 200, seed=42,
                        distribution="normal", use_jumps=False)
    assert g == p


def test_quick_forecast_default_no_jumps():
    """默认参数（normal/无跳跃）行为与 v7.6 一致，能正常返回"""
    r = quick_scenario_forecast([100 + i * 0.3 for i in range(60)],
                                horizon_days=10, n_simulations=500)
    assert "expected_return" in r
    assert "var_95" in r
    assert r["detected_regime"] in ("牛市", "熊市", "震荡市", "高波动")


def test_quick_forecast_with_jumps_and_t():
    """t 分布 + 跳跃扩散快速预测正常"""
    r = quick_scenario_forecast([100 + i * 0.3 for i in range(60)],
                                horizon_days=10, n_simulations=500,
                                distribution="t", use_jumps=True,
                                lambda_jump=0.1, jump_vol=0.03, dof=5)
    assert "expected_return" in r
    assert "cvar_95" in r


# ============================================================
# 4. ScenarioSimulator 参数
# ============================================================

def test_simulator_stores_params():
    s = ScenarioSimulator(n_simulations=500, distribution="t", use_jumps=True,
                          lambda_jump=0.1, jump_vol=0.03, dof=5)
    assert s.distribution == "t"
    assert s.use_jumps is True
    assert s.dof == 5


def test_simulator_default_params():
    """默认参数保持 v7.6 行为（normal/无跳跃）"""
    s = ScenarioSimulator()
    assert s.distribution == "normal"
    assert s.use_jumps is False


def test_simulator_scenario_with_params():
    s = ScenarioSimulator(n_simulations=300, distribution="t", use_jumps=True)
    paths = s.simulate_scenario(100.0, "震荡市", horizon_days=10)
    assert len(paths) == 300
    assert all(isinstance(x, float) for x in paths)
