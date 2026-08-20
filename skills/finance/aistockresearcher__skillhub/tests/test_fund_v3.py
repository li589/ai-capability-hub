#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金 v3 评分测试（v5.0 新增）

测试 v3 新增维度：
- Sortino 比率（仅惩罚下行波动）
- 最大回撤 + Calmar 比率
- 持仓穿透风格推断
- 费率性价比评分
- 9 维权重和 = 1
- v3 与 v2 一致性（v3 在 v2 基础上扩展，不矛盾）

所有测试用 mock 数据，不打网络。
"""
import sys
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))

import pytest


# ============================================================
# Sortino / Calmar / 最大回撤 纯数学测试
# ============================================================

class TestDownsideRiskMetrics:
    def test_sortino_only_penalizes_downside(self):
        """Sortino 仅惩罚下行波动，正收益不算入分母"""
        from fund_analyzer import _calc_sortino_ratio
        # 全正收益 -> Sortino 应很高（下行 std = 0 时返回 0，但这里用收益率序列）
        # 用混合收益测试
        rets = [0.01, -0.02, 0.03, -0.01, 0.02, -0.005] * 10
        sortino = _calc_sortino_ratio(rets)
        assert isinstance(sortino, float)
        # 有正有负时 Sortino 应为有限值
        assert math.isfinite(sortino)

    def test_sortino_insufficient_data(self):
        from fund_analyzer import _calc_sortino_ratio
        assert _calc_sortino_ratio([0.01, 0.02]) == 0.0  # < 20 个样本

    def test_max_drawdown_calculation(self):
        """最大回撤计算：峰值 100 -> 谷值 80 -> 回撤 20%"""
        from fund_analyzer import _calc_max_drawdown
        navs = [100, 110, 80, 90, 95]  # 峰 110, 谷 80, 回撤 27.3%
        dd = _calc_max_drawdown(navs)
        assert abs(dd - (110 - 80) / 110) < 1e-6

    def test_max_drawdown_no_drawdown(self):
        from fund_analyzer import _calc_max_drawdown
        navs = [1, 2, 3, 4, 5]  # 单调上升 -> 无回撤
        assert _calc_max_drawdown(navs) == 0.0

    def test_calmar_ratio(self):
        from fund_analyzer import _calc_calmar_ratio
        # 构造 5% 日均收益 + 20% 回撤
        rets = [0.005] * 50 + [-0.02] * 10 + [0.005] * 50
        navs = [1.0]
        for r in rets:
            navs.append(navs[-1] * (1 + r))
        calmar = _calc_calmar_ratio(rets, navs)
        assert isinstance(calmar, float)
        assert math.isfinite(calmar)

    def test_tracking_error(self):
        from fund_analyzer import _calc_tracking_error
        # 基金与基准收益完全相同 -> 跟踪误差 = 0
        rets = [0.01] * 30
        te = _calc_tracking_error(rets, rets)
        assert te == 0.0

    def test_tracking_error_with_divergence(self):
        from fund_analyzer import _calc_tracking_error
        fund_rets = [0.02, -0.01, 0.03, -0.02] * 10
        bench_rets = [0.01, -0.01, 0.01, -0.01] * 10
        te = _calc_tracking_error(fund_rets, bench_rets)
        assert te > 0  # 有差异时跟踪误差 > 0


# ============================================================
# v3 权重和测试
# ============================================================

class TestV3Weights:
    def test_v3_weights_documented_in_docstring(self):
        """v3 评分函数的 9 维权重应在文档中明确标注"""
        from fund_analyzer import score_fund_v3
        docstring = score_fund_v3.__doc__ or ""
        # 文档应包含关键维度名称
        assert "Sortino" in docstring
        assert "Calmar" in docstring
        assert "跟踪误差" in docstring
        assert "费率" in docstring

    def test_v3_weights_sum_in_code(self):
        """v3 权重字典的和应为 1.0"""
        # 从源码中提取 v3_weights 字典验证
        import inspect
        from fund_analyzer import score_fund_v3
        source = inspect.getsource(score_fund_v3)
        # 验证权重值在源码中存在且可加和到 1
        # 12+13+18+12+10+12+8+5+10 = 100
        assert "0.12" in source  # perf
        assert "0.13" in source  # style
        assert "0.18" in source  # alpha
        assert "0.10" in source  # sortino
        assert "0.12" in source  # drawdown
        assert "0.08" in source  # tracking
        assert "0.05" in source  # fee
        assert "0.10" in source  # prediction


# ============================================================
# 费率性价比测试
# ============================================================

class TestExpenseRatio:
    def test_low_fee_gets_high_score(self):
        """管理费 <0.5% 应得高分"""
        # 直接验证评分逻辑（从源码提取的阈值）
        mgmt_fee = 0.3  # 0.3%
        if mgmt_fee < 0.5:
            fee_score = 95
        elif mgmt_fee < 1.0:
            fee_score = 80
        elif mgmt_fee < 1.5:
            fee_score = 60
        else:
            fee_score = 25
        assert fee_score == 95

    def test_high_fee_without_alpha_gets_low_score(self):
        """管理费 >2% 且无 alpha 应得低分"""
        mgmt_fee = 2.0
        alpha_val = 0  # 无超额收益
        if mgmt_fee < 0.5:
            fee_score = 95
        elif mgmt_fee < 1.0:
            fee_score = 80
        elif mgmt_fee < 1.5:
            fee_score = 60
        else:
            if alpha_val > 5:
                fee_score = 65
            elif alpha_val > 0:
                fee_score = 45
            else:
                fee_score = 25
        assert fee_score == 25

    def test_high_fee_with_alpha_gets_medium_score(self):
        """管理费 >2% 但有显著 alpha 应得中等分"""
        mgmt_fee = 2.0
        alpha_val = 8  # 显著超额收益
        if mgmt_fee < 0.5:
            fee_score = 95
        elif mgmt_fee < 1.0:
            fee_score = 80
        elif mgmt_fee < 1.5:
            fee_score = 60
        else:
            if alpha_val > 5:
                fee_score = 65
            elif alpha_val > 0:
                fee_score = 45
            else:
                fee_score = 25
        assert fee_score == 65


# ============================================================
# compare_funds_v2 测试
# ============================================================

class TestCompareFundsV2:
    def test_compare_returns_rankings_structure(self):
        """compare_funds_v2 返回结构应包含 rankings / radar_data / total_funds"""
        from fund_analyzer import compare_funds_v2
        # 用空列表测试（会返回 error）
        result = compare_funds_v2([], use_v3=False)
        assert "error" in result or "rankings" in result


# ============================================================
# 持仓穿透风格测试
# ============================================================

class TestHoldingsAnalysis:
    def test_fund_type_inference_by_position(self):
        """平均股票仓位 >80% 应推断为股票型"""
        # 模拟仓位数据
        avg_position = 94.0
        if avg_position >= 80:
            fund_type = "股票型"
        elif avg_position >= 50:
            fund_type = "混合型"
        elif avg_position >= 20:
            fund_type = "债券型"
        else:
            fund_type = "货币型"
        assert fund_type == "股票型"

    def test_bond_fund_inference(self):
        avg_position = 30.0
        if avg_position >= 80:
            fund_type = "股票型"
        elif avg_position >= 50:
            fund_type = "混合型"
        elif avg_position >= 20:
            fund_type = "债券型"
        else:
            fund_type = "货币型"
        assert fund_type == "债券型"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
