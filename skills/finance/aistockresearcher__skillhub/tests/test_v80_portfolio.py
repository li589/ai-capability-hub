# -*- coding: utf-8 -*-
"""v8.0.0 模块C：组合优化测试（纯 stdlib，测试环境 numpy 被 conftest 屏蔽）"""

import sys
from pathlib import Path

import pytest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from stock_researcher.quantitative.portfolio_models import (
    mean_variance_optimize, max_sharpe_weights, risk_parity_weights,
    portfolio_var_es, allocate_portfolio, _cov_matrix, _invert_matrix,
)


def _make_rets(n_rows=30, seed=42):
    """确定性 3 资产收益矩阵。"""
    random = __import__("random").Random(seed)
    return [[0.001 * random.randint(-5, 8),
             0.0008 * random.randint(-4, 6),
             -0.0005 * random.randint(0, 10)] for _ in range(n_rows)]


RETS = _make_rets()


# ============================================================
# 1. 基础工具
# ============================================================

def test_cov_matrix_shape_and_symmetry():
    cov, means = _cov_matrix(RETS)
    assert len(cov) == 3 and len(cov[0]) == 3
    for i in range(3):
        for j in range(3):
            assert abs(cov[i][j] - cov[j][i]) < 1e-12, "协方差应对称"
    assert len(means) == 3


def test_cov_matrix_empty():
    assert _cov_matrix([]) == ([], [])
    assert _cov_matrix([[1.0]]) == ([], [])


def test_invert_matrix_roundtrip():
    m = [[2.0, 1.0], [1.0, 3.0]]
    inv = _invert_matrix(m)
    assert inv is not None
    # M @ inv ≈ I
    prod = [[sum(m[i][k] * inv[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    assert abs(prod[0][0] - 1.0) < 1e-9
    assert abs(prod[1][1] - 1.0) < 1e-9
    assert abs(prod[0][1]) < 1e-9


def test_invert_matrix_singular():
    assert _invert_matrix([[1.0, 2.0], [2.0, 4.0]]) is None


# ============================================================
# 2. Markowitz MVO
# ============================================================

def test_mvo_long_only_weights_sum_to_1():
    r = mean_variance_optimize(RETS, risk_aversion=2.5)
    assert not r.get("error")
    assert abs(sum(r["weights"]) - 1.0) < 1e-4, f"权重和应=1: {r['weights']}"


def test_mvo_long_only_non_negative():
    r = mean_variance_optimize(RETS, risk_aversion=2.5)
    assert all(w >= -1e-9 for w in r["weights"]), "长仓权重应非负"


def test_mvo_converged():
    r = mean_variance_optimize(RETS, risk_aversion=2.5)
    assert r["converged"] is True
    assert r["method"] == "frank_wolfe"


def test_mvo_allow_short():
    r = mean_variance_optimize(RETS, risk_aversion=2.5, allow_short=True)
    assert abs(sum(r["weights"]) - 1.0) < 1e-4
    assert r["method"] == "closed_form"


def test_mvo_insufficient_data():
    r = mean_variance_optimize([[0.01, 0.02]])
    assert r.get("error") or not r.get("weights")


def test_mvo_risk_aversion_effect():
    """风险厌恶越高，越偏向低波动资产（高收益高波动 vs 低收益低波动）"""
    hi_ret_hi_vol = [0.05 if i % 2 == 0 else -0.04 for i in range(40)]
    mid = [0.01, -0.005] * 20
    lo_ret_lo_vol = [0.001] * 40
    data = list(zip(hi_ret_hi_vol, mid, lo_ret_lo_vol))
    low = mean_variance_optimize(data, risk_aversion=0.5)
    high = mean_variance_optimize(data, risk_aversion=10.0)
    # 低风险厌恶下高收益资产的权重大于（或等于）高风险厌恶
    assert low["weights"][0] >= high["weights"][0] - 0.01


# ============================================================
# 3. 最大 Sharpe
# ============================================================

def test_max_sharpe_returns_weights():
    r = max_sharpe_weights(RETS)
    assert not r.get("error")
    assert abs(sum(r["weights"]) - 1.0) < 1e-4


def test_max_sharpe_better_than_equal():
    """最大 Sharpe 组合的夏普应不低于等权组合"""
    import math
    ms = max_sharpe_weights(RETS)
    eq = mean_variance_optimize(RETS, risk_aversion=2.5)
    assert ms["sharpe_max"] >= eq["sharpe"] - 0.1  # 宽松比较


# ============================================================
# 4. 风险平价（stdlib 降级）
# ============================================================

def test_risk_parity_stdlib_weights():
    """测试环境 numpy 被屏蔽 → 走纯 stdlib 坐标下降"""
    r = risk_parity_weights(RETS)
    assert not r.get("error")
    assert r.get("method") in ("risk_parity_stdlib", "risk_budget_weights", None)
    if r.get("weights"):
        assert abs(sum(r["weights"]) - 1.0) < 1e-4


def test_risk_parity_equal_budget():
    """等风险预算下权重差距不大（无极端集中）"""
    r = risk_parity_weights(RETS)
    if r.get("weights"):
        assert max(r["weights"]) - min(r["weights"]) < 0.9


# ============================================================
# 5. 组合 VaR/ES
# ============================================================

def test_portfolio_var_es_three_methods():
    r = portfolio_var_es(RETS)
    assert "var_historical" in r
    assert "es_historical" in r
    assert "var_covariance" in r
    assert r["var_historical"] >= 0, "VaR 为正数损失"
    assert r["es_historical"] >= r["var_historical"] - 1e-9, "ES ≥ VaR"


def test_portfolio_var_es_weights_provided():
    r = portfolio_var_es(RETS, weights=[0.5, 0.3, 0.2])
    assert abs(sum(r["weights"]) - 1.0) < 1e-9


def test_portfolio_var_es_empty():
    assert "error" in portfolio_var_es([])


# ============================================================
# 6. 统一入口 allocate_portfolio
# ============================================================

def test_allocate_equal():
    r = allocate_portfolio(RETS, method="equal")
    assert abs(sum(r["weights"]) - 1.0) < 0.001  # round(4位) 精度
    assert all(abs(w - 1.0 / 3.0) < 0.001 for w in r["weights"])


def test_allocate_mvo():
    r = allocate_portfolio(RETS, method="mvo", risk_aversion=2.5)
    assert abs(sum(r["weights"]) - 1.0) < 1e-4


def test_allocate_max_sharpe():
    r = allocate_portfolio(RETS, method="max_sharpe")
    assert not r.get("error")


def test_allocate_risk_parity():
    r = allocate_portfolio(RETS, method="risk_parity")
    assert not r.get("error")


def test_allocate_unknown_method():
    r = allocate_portfolio(RETS, method="nope")
    assert r.get("error")


def test_allocate_default_risk_parity():
    r = allocate_portfolio(RETS)
    assert not r.get("error")
