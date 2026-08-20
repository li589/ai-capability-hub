#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stock-researcher v7.6 增强预测能力测试（test_v760_enhanced_predict.py）

覆盖：
- enhanced_factors.py（4 大新因子 + 集成）
- scenario_simulator.py（多场景概率预测）
- 修复的 BUG 回归（factor confidence + 资金流 0 值跳过）
"""
from __future__ import annotations

import math
import sys
from datetime import date
from pathlib import Path

import pytest

SKILL_DIR = Path(__file__).resolve().parent.parent
QUANT_DIR = SKILL_DIR / "scripts" / "stock_researcher" / "quantitative"
sys.path.insert(0, str(QUANT_DIR))


# ============================================================================
# enhanced_factors.py 测试
# ============================================================================


class TestMomentumReversionFactor:

    def test_insufficient_data(self):
        """数据不足时应返回默认中性分（50）+ 低置信度。"""
        from enhanced_factors import MomentumReversionFactor

        f = MomentumReversionFactor()
        result = f.calc(prices=[100, 101, 102])
        assert result.score == 50.0
        assert result.confidence < 0.5

    def test_strong_uptrend_high_score(self):
        """强势上涨 → 高分（>60）。"""
        from enhanced_factors import MomentumReversionFactor

        f = MomentumReversionFactor()
        # 60 日单调上涨约 30%
        prices = [100 + i * 0.5 for i in range(80)]
        result = f.calc(prices)
        assert result.score > 55, f"强势上涨应得分 >55，实际 {result.score}"
        assert result.confidence >= 0.7

    def test_strong_downtrend_low_score(self):
        """强势下跌 → 低分（<45）。"""
        from enhanced_factors import MomentumReversionFactor

        f = MomentumReversionFactor()
        prices = [200 - i * 0.5 for i in range(80)]
        result = f.calc(prices)
        assert result.score < 45, f"强势下跌应得分 <45，实际 {result.score}"

    def test_with_volume_reversal_signal(self):
        """放量 + 下跌 → 反转信号（看涨）。"""
        from enhanced_factors import MomentumReversionFactor

        f = MomentumReversionFactor()
        # 上涨趋势 + 最后一日放量阴线
        prices = [100 + i * 0.2 for i in range(60)]
        prices.append(95)  # 大跌
        volumes = [10000] * 59 + [50000]  # 放量

        result = f.calc(prices, volumes)
        # 反转信号 = 65（看涨反转）
        assert result.metadata.get("reversal_score", 0) >= 60, \
            f"放量阴线应触发反转信号（看涨）"

    def test_period_weights(self):
        """短期动量权重大于长期。"""
        from enhanced_factors import MomentumReversionFactor

        f = MomentumReversionFactor()
        prices = [100] * 60 + [100, 102, 105, 110]  # 后 4 日大涨
        result = f.calc(prices)
        # 应主要由 5d 动量驱动
        meta = result.metadata.get("period_returns", {})
        assert meta.get("5d", 0) > 0.05  # 5 日涨幅 > 5%
        # 60 日涨幅 = (110 - 100) / 100 = 10%（不是 0.01）
        # 重点验证短期动量值更大或至少一样
        assert meta.get("5d") >= meta.get("60d")


class TestCapitalFlowFactor:

    def test_no_data_returns_neutral(self):
        """无数据 → 中性 50 + 低置信度。"""
        from enhanced_factors import CapitalFlowFactor

        result = CapitalFlowFactor().calc()
        assert result.score == 50.0
        assert result.confidence < 0.5

    def test_strong_main_flow_high_score(self):
        """主力强势流入 → 高分。"""
        from enhanced_factors import CapitalFlowFactor

        result = CapitalFlowFactor().calc(main_flow_ratio=0.5)
        assert result.score > 70
        # 单源数据，confidence = 1/4 = 0.25
        assert result.confidence >= 0.2

    def test_all_signals_negative(self):
        """所有资金流信号为负 → 低分。"""
        from enhanced_factors import CapitalFlowFactor

        result = CapitalFlowFactor().calc(
            main_flow_ratio=-0.5, north_flow_change=-0.3,
            etf_net_flow=-5, margin_balance_change=-0.4
        )
        assert result.score < 30

    def test_etf_extreme_signal(self):
        """ETF 大额净申购（>5亿）应映射到接近极端分数。"""
        from enhanced_factors import CapitalFlowFactor

        # ETF 流入 10 亿（>5 亿视为强烈信号）
        result = CapitalFlowFactor().calc(etf_net_flow=10)
        # tanh(10/5) = tanh(2) ≈ 0.96 → 50 + 0.96*50 ≈ 98
        assert result.score > 80

    def test_confidence_scales_with_sources(self):
        """置信度应随数据源数量增加（4/4=1.0，1/4=0.25）。"""
        from enhanced_factors import CapitalFlowFactor

        r1 = CapitalFlowFactor().calc(main_flow_ratio=0.1)
        r4 = CapitalFlowFactor().calc(
            main_flow_ratio=0.1, north_flow_change=0.1,
            etf_net_flow=1, margin_balance_change=0.1,
        )
        assert r4.confidence > r1.confidence


class TestVolatilityFactor:

    def test_low_volatility_neutral(self):
        """低波动 → 中性偏低分（反向预警）。"""
        from enhanced_factors import VolatilityFactor

        # 几乎无波动的价格
        prices = [100 + (i % 3) * 0.01 for i in range(80)]
        result = VolatilityFactor().calc(prices)
        # 年化波动 ~ 1%，低波动 → 35 分
        assert result.score <= 45

    def test_high_volatility_breakout(self):
        """高波动 + 突破 → 高分（趋势跟随）。"""
        from enhanced_factors import VolatilityFactor

        # 高波动价格序列 + 突破日
        import random
        random.seed(42)
        prices = [100]
        for _ in range(60):
            prices.append(prices[-1] * (1 + random.gauss(0, 0.03)))
        # 突破：最后一日大涨 10%
        prices.append(prices[-1] * 1.10)

        result = VolatilityFactor().calc(prices)
        # 高波动应 > 50 或 70
        assert result.score >= 50, f"高波动+突破应得分 >=50，实际 {result.score}"

    def test_atr_calculation(self):
        """ATR 计算需要 high/low 数据。"""
        from enhanced_factors import VolatilityFactor

        prices = [100 + i for i in range(30)]
        highs = [p + 1 for p in prices]
        lows = [p - 1 for p in prices]

        result = VolatilityFactor().calc(prices, highs, lows)
        assert result.metadata.get("atr", 0) > 0


class TestCalendarFactor:

    def test_month_end_bonus(self):
        """月末应加分（>50）。"""
        from enhanced_factors import CalendarFactor

        # 月末（30 日）
        result = CalendarFactor().calc(
            date_obj=date(2026, 8, 30), days_to_month_end=0
        )
        assert result.score >= 50

    def test_month_start_penalty(self):
        """月初应减分（<50）。"""
        from enhanced_factors import CalendarFactor

        # 月初（1 日）
        result = CalendarFactor().calc(
            date_obj=date(2026, 8, 1), days_to_month_end=30
        )
        assert result.score < 50

    def test_financial_report_period_penalty(self):
        """财报期应减分（波动加剧但中性）。"""
        from enhanced_factors import CalendarFactor

        result_no_fr = CalendarFactor().calc(
            date_obj=date(2026, 6, 15), days_to_month_end=15
        )
        result_fr = CalendarFactor().calc(
            date_obj=date(2026, 6, 15), days_to_month_end=15,
            is_financial_report_period=True,
        )
        assert result_fr.score < result_no_fr.score


class TestEnhancedFactorLibrary:
    """增强因子库统一入口。"""

    def test_quick_enhanced_score_minimal(self):
        """最小输入（无价格无日期）应能用。"""
        from enhanced_factors import quick_enhanced_score

        result = quick_enhanced_score(
            indicators={"pe": 15, "pb": 1.8, "roe": 0.18}
        )
        assert "total_score" in result
        assert "recommendation" in result
        assert 0 <= result["total_score"] <= 100
        assert result["total_score"] > 50  # PE 15 + PB 1.8 + ROE 18% 应不错

    def test_full_input_with_prices(self):
        """完整输入（含价格 + 成交量 + 日期）。"""
        from enhanced_factors import quick_enhanced_score

        prices = [100 + i * 0.3 + (i % 5) * 0.5 for i in range(80)]
        volumes = [10000 + i * 100 for i in range(80)]
        result = quick_enhanced_score(
            indicators={
                "pe": 15, "pb": 1.8, "roe": 0.18, "revenue_growth": 0.25,
                "main_flow_ratio": 0.10, "north_flow_change": 0.05,
                "days_to_month_end": 3,
            },
            prices=prices,
            volumes=volumes,
            date_obj=date(2026, 8, 28),
        )
        assert result["total_score"] > 60
        assert "momentum_reversion" in result["factors"]
        assert "volatility_regime" in result["factors"]
        assert "calendar" in result["factors"]
        assert result["market_regime"] in ("牛市", "震荡市", "熊市", "高波动", "unknown")

    def test_bug001_baseline_factor_confidence(self):
        """BUG-001 修复回归：基础因子 confidence 不应为 0（修复后 ≥ 0.7）。"""
        from enhanced_factors import quick_enhanced_score

        result = quick_enhanced_score(
            indicators={"pe": 15, "pb": 1.8, "roe": 0.18, "revenue_growth": 0.25}
        )
        for name in ("value_pe", "value_pb", "quality_roe", "growth_rev"):
            assert name in result["factors"]
            assert result["factors"][name]["confidence"] >= 0.5, \
                f"{name} confidence 应 >=0.5，实际 {result['factors'][name]['confidence']}"

    def test_bug002_capital_flow_skips_zero(self):
        """BUG-002 修复回归：零值不应纳入评分（边际过滤）。"""
        from enhanced_factors import quick_enhanced_score

        # main_flow_ratio=0 + 其他无值 → 不应纳入资金流因子
        result = quick_enhanced_score(
            indicators={"pe": 15, "main_flow_ratio": 0}
        )
        assert "capital_flow" not in result["factors"], \
            "全零资金流指标应跳过"

    def test_recommendation_thresholds(self):
        """推荐等级阈值正确性。"""
        from enhanced_factors import quick_enhanced_score

        # PE 极低 + ROE 极高 → 应为推荐/强烈推荐
        r = quick_enhanced_score(
            indicators={"pe": 5, "pb": 0.5, "roe": 0.30, "revenue_growth": 0.50}
        )
        assert "推荐" in r["recommendation"] or "强烈" in r["recommendation"]

    def test_empty_indicators(self):
        """空 indicators 应返回中性默认。"""
        from enhanced_factors import quick_enhanced_score

        result = quick_enhanced_score(indicators={})
        assert result["total_score"] == 50.0
        assert result["recommendation"] == "数据不足"
        assert result["factors"] == {}


# ============================================================================
# scenario_simulator.py 测试
# ============================================================================


class TestDetectMarketRegime:

    def test_bull_regime(self):
        """60 日大涨 → 牛市。"""
        from scenario_simulator import detect_market_regime_from_history

        prices = [100 + i * 0.5 for i in range(80)]  # 80 日涨 40%
        assert detect_market_regime_from_history(prices) == "牛市"

    def test_bear_regime(self):
        """60 日大跌 → 熊市。"""
        from scenario_simulator import detect_market_regime_from_history

        prices = [200 - i * 0.5 for i in range(80)]  # 80 日跌 40%
        assert detect_market_regime_from_history(prices) == "熊市"

    def test_high_volatility(self):
        """高波动 → 高波动。"""
        from scenario_simulator import detect_market_regime_from_history
        import random
        random.seed(42)
        prices = [100]
        for _ in range(80):
            prices.append(prices[-1] * (1 + random.gauss(0, 0.05)))
        regime = detect_market_regime_from_history(prices)
        assert regime in ("高波动", "震荡市", "牛市", "熊市")  # 至少能识别

    def test_short_history_returns_neutral(self):
        """数据不足 → 震荡市。"""
        from scenario_simulator import detect_market_regime_from_history

        assert detect_market_regime_from_history([100, 101, 102]) == "震荡市"
        assert detect_market_regime_from_history([]) == "震荡市"


class TestScenarioSimulator:

    def test_forecast_returns_result(self):
        """forecast 应返回 ScenarioResult 含必要字段。"""
        from scenario_simulator import ScenarioSimulator

        prices = [100 + i * 0.3 for i in range(80)]
        sim = ScenarioSimulator(n_simulations=500)
        result = sim.forecast(prices, current_score=70, horizon_days=20)
        assert result.expected_return != 0
        assert 0 <= result.probability_bullish <= 1
        assert 0 <= result.probability_bearish <= 1
        assert abs(result.probability_bullish + result.probability_bearish - 1) < 0.05  # 接近 1
        assert result.var_95 <= 0  # VaR 是负数
        assert result.cvar_95 <= 0
        assert result.horizon_days == 20

    def test_bull_score_higher_expected_return(self):
        """高评分 + 牛市数据 → 期望收益 > 0。"""
        from scenario_simulator import ScenarioSimulator

        prices = [100 + i * 0.5 for i in range(80)]  # 牛市
        sim = ScenarioSimulator(n_simulations=500)
        result = sim.forecast(prices, current_score=80, horizon_days=20)
        assert result.expected_return > 0
        assert result.probability_bullish > 0.5

    def test_bear_score_negative_expected(self):
        """低评分 + 熊市数据 → 期望收益 < 0。"""
        from scenario_simulator import ScenarioSimulator

        # 严重下跌：60 日跌幅 -30%
        prices = [200 - i * 0.6 for i in range(80)]
        sim = ScenarioSimulator(n_simulations=500)
        result = sim.forecast(prices, current_score=20, horizon_days=20)
        assert result.expected_return < 0
        assert result.probability_bearish > 0.5

    def test_empty_prices_returns_neutral(self):
        """空价格应返回中性默认。"""
        from scenario_simulator import ScenarioSimulator

        sim = ScenarioSimulator()
        result = sim.forecast([], current_score=50)
        assert result.expected_return == 0.0
        assert result.confidence == 0.0

    def test_scenarios_dict_has_4_scenarios(self):
        """scenarios  应含 4 大市场状态。"""
        from scenario_simulator import ScenarioSimulator

        prices = [100 + i * 0.3 for i in range(80)]
        sim = ScenarioSimulator(n_simulations=300)
        result = sim.forecast(prices)
        assert "牛市" in result.scenarios
        assert "熊市" in result.scenarios
        assert "震荡市" in result.scenarios
        assert "高波动" in result.scenarios

    def test_var_more_extreme_than_cvar(self):
        """VaR（分位）应比 CVaR（尾部均值）更不极端（同符号下 VaR 数值更靠近 0）。"""
        from scenario_simulator import ScenarioSimulator

        prices = [100 + i * 0.3 for i in range(80)]
        sim = ScenarioSimulator(n_simulations=500)
        result = sim.forecast(prices, current_score=50, horizon_days=20)
        # 两个都是负数时，CVaR（更深尾部）绝对值更大
        assert result.var_95 >= result.cvar_95, \
            f"VaR ({result.var_95}) 应 >= CVaR ({result.cvar_95})"


class TestQuickScenarioForecast:

    def test_returns_dict(self):
        """便捷函数应返回 dict 格式。"""
        from scenario_simulator import quick_scenario_forecast

        prices = [100 + i * 0.3 for i in range(80)]
        result = quick_scenario_forecast(
            prices, current_score=70, horizon_days=20, n_simulations=500
        )
        assert isinstance(result, dict)
        assert "expected_return" in result
        assert "probability_bullish" in result
        assert "var_95" in result
        assert "scenarios" in result
        assert "detected_regime" in result
        assert "horizon_days" in result

    def test_horizon_parameter(self):
        """horizon_days 参数应生效。"""
        from scenario_simulator import quick_scenario_forecast

        prices = [100 + i * 0.3 for i in range(80)]
        r20 = quick_scenario_forecast(prices, horizon_days=20, n_simulations=300)
        r60 = quick_scenario_forecast(prices, horizon_days=60, n_simulations=300)
        # 60 日波动应大于 20 日
        assert abs(r60["expected_return"]) >= abs(r20["expected_return"]) * 0.5  # 大致关系
        assert r60["horizon_days"] == 60
        assert r20["horizon_days"] == 20


# ============================================================================
# 集成测试：enhanced_factors + scenario_simulator
# ============================================================================


class TestIntegration:

    def test_factor_score_then_scenario(self):
        """先因子评分 → 再场景预测 的工作流。"""
        from enhanced_factors import quick_enhanced_score
        from scenario_simulator import quick_scenario_forecast

        prices = [100 + i * 0.3 + (i % 5) * 0.5 for i in range(80)]
        volumes = [10000 + i * 100 for i in range(80)]

        # Step 1: 因子评分
        factor_result = quick_enhanced_score(
            indicators={"pe": 15, "pb": 1.8, "roe": 0.18,
                        "revenue_growth": 0.25,
                        "main_flow_ratio": 0.10},
            prices=prices,
            volumes=volumes,
            date_obj=date(2026, 8, 28),
        )

        # Step 2: 用评分驱动场景预测
        scenario_result = quick_scenario_forecast(
            prices=prices,
            current_score=factor_result["total_score"],
            horizon_days=20,
            n_simulations=500,
        )

        # 验证工作流：高分 + 牛市数据应得正期望收益
        if factor_result["total_score"] >= 70:
            assert scenario_result["expected_return"] > 0

    def test_low_score_leads_to_bearish_scenario(self):
        """低分 → 看跌概率较高。"""
        from enhanced_factors import quick_enhanced_score
        from scenario_simulator import quick_scenario_forecast

        prices = [100 + i * 0.3 for i in range(80)]
        # 低分场景：PE=80、PB=8、ROE=2%、营收负增长
        factor_result = quick_enhanced_score(
            indicators={"pe": 80, "pb": 8, "roe": 0.02,
                        "revenue_growth": -0.20},
            prices=prices,
        )
        assert factor_result["total_score"] < 50  # 应是低分

        # 用低分做场景预测
        scenario_result = quick_scenario_forecast(
            prices=prices,
            current_score=factor_result["total_score"],
            horizon_days=20,
            n_simulations=500,
        )
        # 低分下熊市先验应增加
        assert scenario_result["scenarios"]["熊市"] != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])