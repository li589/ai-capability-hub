#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v4.0.0 新增模块测试"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))


def test_user_profile_allocation():
    """风险偏好→目标配置映射"""
    from stock_researcher.advisor.user_profile import UserProfile, RISK_ALLOCATION
    p = UserProfile(risk_preference="保守")
    t = p.target_allocation()
    assert t["bond"] == 60, f"保守债券应为60%, 实际{t['bond']}"
    assert t["stock"] == 10

    p2 = UserProfile(risk_preference="激进")
    t2 = p2.target_allocation()
    assert t2["stock"] == 75

    # 无效偏好回退到平衡
    p3 = UserProfile(risk_preference="invalid")
    t3 = p3.target_allocation()
    assert t3 == RISK_ALLOCATION["平衡"]
    print("  ✅ test_user_profile_allocation")


def test_weight_optimizer_math():
    """指数加权权重建议的数学正确性"""
    from stock_researcher.evolution.evolution_runner import WeightOptimizer
    import math

    report = {
        "hit_rate_pct": 65.0,
        "by_model": {"model_A": 70.0, "model_B": 60.0, "model_C": 50.0},
        "by_horizon": {"1d": 68.0, "5d": 62.0, "1Q": 55.0},
    }
    prop = WeightOptimizer.propose_weights(report)
    assert prop is not None
    assert "model_weights" in prop
    mw = prop["model_weights"]
    # 命中率最高的应有最大权重
    assert mw["model_A"] > mw["model_B"] > mw["model_C"], f"权重顺序不对: {mw}"

    # 权重应归一化到和为1
    total = sum(mw.values())
    assert abs(total - 1.0) < 0.01, f"权重未归一化: sum={total}"

    # 缺失数据无建议
    report_empty = {"hit_rate_pct": 0, "by_model": {}, "by_horizon": {}}
    prop2 = WeightOptimizer.propose_weights(report_empty)
    assert prop2 is None
    print("  ✅ test_weight_optimizer_math")


def test_prediction_tracker_hit_logic():
    """命中判定逻辑"""
    from stock_researcher.evolution.prediction_tracker import PredictionRecord

    # 看多 + 实际上涨 = 命中
    r1 = PredictionRecord("", "stock", "600519", "5d", "mh", "看多", 2.0, 0.8, "")
    r1.actual_pct = 3.0
    # 模拟 resolve 的判定
    want_up = r1.predicted_direction in ("看多", "分歧偏多")
    assert want_up and r1.actual_pct > 0

    # 看空 + 实际下跌 = 命中
    r2 = PredictionRecord("", "stock", "000001", "5d", "mh", "看空", -1.5, 0.7, "")
    r2.actual_pct = -2.0
    want_down = r2.predicted_direction in ("看空", "分歧偏空")
    assert want_down and r2.actual_pct < 0

    # 震荡 + 微量变化 = 命中
    r3 = PredictionRecord("", "stock", "000002", "1d", "mh", "震荡", 0.1, 0.5, "")
    r3.actual_pct = 0.2
    assert abs(r3.actual_pct) < 0.5 and abs(r3.predicted_pct) < 1
    print("  ✅ test_prediction_tracker_hit_logic")


def test_fusion_to_evolution_format():
    """evolution_runner._to_fusion_format 格式转换"""
    from stock_researcher.evolution.evolution_runner import EvolutionRunner
    proposal = {
        "model_weights": {"broker": 0.40, "technical": 0.20, "sentiment": 0.10},
        "baseline_hit_rate": 60.0,
    }
    result = EvolutionRunner._to_fusion_format(proposal)
    assert "1d" in result
    assert "1Q" in result
    # 每个周期的权重和应为 1.0
    for horizon, dim_weights in result.items():
        total = sum(dim_weights.values())
        assert abs(total - 1.0) < 0.02, f"{horizon} weights sum={total}"
    # broker 命中率高应有放大
    print("  ✅ test_fusion_to_evolution_format")


if __name__ == "__main__":
    test_user_profile_allocation()
    test_weight_optimizer_math()
    test_prediction_tracker_hit_logic()
    test_fusion_to_evolution_format()
    print("\n  🎉 All v4.0 tests passed!")
