#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资分析框架测试（v5.0 新增）

测试 6 模块的核心数学计算：
- WACC/CAPM (beta, cost_of_equity, wacc)
- 护城河评分 (moat_score, moat_type)
- 财务健康 (Altman Z, Piotroski F, Beneish M)
- DCF 估值 (intrinsic_value, sensitivity matrix)
- 管理层评分 (6 维加权)
- 行业分析 (Porter 五力)
- 决策整合 (6 模块加权 + verdict 映射)
- 数据不足降级路径

所有测试用 mock 财务数据（fixture 字典），不打网络。
"""
import sys
import math
from pathlib import Path

# 确保项目根在 sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "pkg"))

import pytest


# ============================================================
# Mock 财务数据 fixtures
# ============================================================

MOCK_INCOME = [
    {"report_date": "2024-12-31", "TOTAL_OPERATE_INCOME": 1500e8, "OPERATE_INCOME": 1500e8,
     "OPERATE_COST": 130e8, "PARENT_NETPROFIT": 700e8, "NETPROFIT": 700e8,
     "BASIC_EPS": 55.0, "ROE": 30.0, "GROSS_MARGIN": 91.3, "XSJLL": 91.3,
     "REVENUE_GROWTH": 15.0, "PROFIT_GROWTH": 18.0,
     "OPERATE_PROFIT": 850e8, "TOTAL_PROFIT": 850e8,
     "FINANCE_EXPENSE": 5e8, "RESEARCH_EXPENSE": 2e8,
     "SALE_EXPENSE": 50e8, "MANAGE_EXPENSE": 30e8, "INCOME_TAX": 150e8},
    {"report_date": "2023-12-31", "TOTAL_OPERATE_INCOME": 1300e8, "OPERATE_INCOME": 1300e8,
     "OPERATE_COST": 115e8, "PARENT_NETPROFIT": 600e8, "NETPROFIT": 600e8,
     "BASIC_EPS": 48.0, "ROE": 28.0, "GROSS_MARGIN": 91.2, "XSJLL": 91.2,
     "REVENUE_GROWTH": 14.0, "PROFIT_GROWTH": 16.0,
     "OPERATE_PROFIT": 730e8, "TOTAL_PROFIT": 730e8,
     "FINANCE_EXPENSE": 4e8, "RESEARCH_EXPENSE": 1.8e8,
     "SALE_EXPENSE": 45e8, "MANAGE_EXPENSE": 28e8, "INCOME_TAX": 130e8},
    {"report_date": "2022-12-31", "TOTAL_OPERATE_INCOME": 1140e8, "OPERATE_INCOME": 1140e8,
     "OPERATE_COST": 100e8, "PARENT_NETPROFIT": 520e8, "NETPROFIT": 520e8,
     "BASIC_EPS": 42.0, "ROE": 27.0, "GROSS_MARGIN": 91.2, "XSJLL": 91.2,
     "REVENUE_GROWTH": 13.0, "PROFIT_GROWTH": 15.0,
     "OPERATE_PROFIT": 640e8, "TOTAL_PROFIT": 640e8,
     "FINANCE_EXPENSE": 3e8, "RESEARCH_EXPENSE": 1.5e8,
     "SALE_EXPENSE": 40e8, "MANAGE_EXPENSE": 25e8, "INCOME_TAX": 120e8},
    {"report_date": "2021-12-31", "TOTAL_OPERATE_INCOME": 1000e8, "OPERATE_INCOME": 1000e8,
     "OPERATE_COST": 90e8, "PARENT_NETPROFIT": 450e8, "NETPROFIT": 450e8,
     "BASIC_EPS": 36.0, "ROE": 26.0, "GROSS_MARGIN": 91.0, "XSJLL": 91.0,
     "REVENUE_GROWTH": 12.0, "PROFIT_GROWTH": 14.0,
     "OPERATE_PROFIT": 550e8, "TOTAL_PROFIT": 550e8,
     "FINANCE_EXPENSE": 2.5e8, "RESEARCH_EXPENSE": 1.2e8,
     "SALE_EXPENSE": 35e8, "MANAGE_EXPENSE": 22e8, "INCOME_TAX": 100e8},
    {"report_date": "2020-12-31", "TOTAL_OPERATE_INCOME": 890e8, "OPERATE_INCOME": 890e8,
     "OPERATE_COST": 80e8, "PARENT_NETPROFIT": 400e8, "NETPROFIT": 400e8,
     "BASIC_EPS": 32.0, "ROE": 25.0, "GROSS_MARGIN": 91.0, "XSJLL": 91.0,
     "REVENUE_GROWTH": 11.0, "PROFIT_GROWTH": 13.0,
     "OPERATE_PROFIT": 490e8, "TOTAL_PROFIT": 490e8,
     "FINANCE_EXPENSE": 2e8, "RESEARCH_EXPENSE": 1e8,
     "SALE_EXPENSE": 30e8, "MANAGE_EXPENSE": 20e8, "INCOME_TAX": 90e8},
]

MOCK_BALANCE = [
    {"report_date": "2024-12-31", "TOTAL_ASSETS": 2500e8, "TOTAL_LIABILITIES": 400e8,
     "TOTAL_EQUITY": 2100e8, "TOTAL_PARENT_EQUITY": 2100e8,
     "TOTAL_CURRENT_ASSETS": 1800e8, "TOTAL_CURRENT_LIAB": 240e8,
     "FIXED_ASSET": 200e8, "CASH": 800e8, "MONETARY_FUNDS": 800e8,
     "ACCOUNTS_RECE": 5e8, "INVENTORY": 300e8, "GOODWILL": 10e8,
     "SHORT_LOAN": 50e8, "LONG_LOAN": 100e8, "BOND_PAYABLE": 0,
     "UNDISTRIBUTED_PROFIT": 1500e8, "RETAINED_EARNINGS": 1500e8,
     "CURRENT_RATIO": 750, "DEBT_ASSET_RATIO": 16.0, "ZCFZL": 16.0, "LDBL": 750},
    {"report_date": "2023-12-31", "TOTAL_ASSETS": 2200e8, "TOTAL_LIABILITIES": 380e8,
     "TOTAL_EQUITY": 1820e8, "TOTAL_PARENT_EQUITY": 1820e8,
     "TOTAL_CURRENT_ASSETS": 1600e8, "TOTAL_CURRENT_LIAB": 230e8,
     "FIXED_ASSET": 190e8, "CASH": 700e8, "MONETARY_FUNDS": 700e8,
     "ACCOUNTS_RECE": 4e8, "INVENTORY": 280e8, "GOODWILL": 10e8,
     "SHORT_LOAN": 45e8, "LONG_LOAN": 90e8, "BOND_PAYABLE": 0,
     "UNDISTRIBUTED_PROFIT": 1300e8, "RETAINED_EARNINGS": 1300e8,
     "CURRENT_RATIO": 696, "DEBT_ASSET_RATIO": 17.3, "ZCFZL": 17.3, "LDBL": 696},
    {"report_date": "2022-12-31", "TOTAL_ASSETS": 1900e8, "TOTAL_LIABILITIES": 350e8,
     "TOTAL_EQUITY": 1550e8, "TOTAL_PARENT_EQUITY": 1550e8,
     "TOTAL_CURRENT_ASSETS": 1400e8, "TOTAL_CURRENT_LIAB": 210e8,
     "FIXED_ASSET": 180e8, "CASH": 600e8, "MONETARY_FUNDS": 600e8,
     "ACCOUNTS_RECE": 3.5e8, "INVENTORY": 250e8, "GOODWILL": 10e8,
     "SHORT_LOAN": 40e8, "LONG_LOAN": 80e8, "BOND_PAYABLE": 0,
     "UNDISTRIBUTED_PROFIT": 1100e8, "RETAINED_EARNINGS": 1100e8,
     "CURRENT_RATIO": 667, "DEBT_ASSET_RATIO": 18.4, "ZCFZL": 18.4, "LDBL": 667},
    {"report_date": "2021-12-31", "TOTAL_ASSETS": 1600e8, "TOTAL_LIABILITIES": 320e8,
     "TOTAL_EQUITY": 1280e8, "TOTAL_PARENT_EQUITY": 1280e8,
     "TOTAL_CURRENT_ASSETS": 1200e8, "TOTAL_CURRENT_LIAB": 190e8,
     "FIXED_ASSET": 170e8, "CASH": 500e8, "MONETARY_FUNDS": 500e8,
     "ACCOUNTS_RECE": 3e8, "INVENTORY": 220e8, "GOODWILL": 10e8,
     "SHORT_LOAN": 35e8, "LONG_LOAN": 70e8, "BOND_PAYABLE": 0,
     "UNDISTRIBUTED_PROFIT": 900e8, "RETAINED_EARNINGS": 900e8,
     "CURRENT_RATIO": 632, "DEBT_ASSET_RATIO": 20.0, "ZCFZL": 20.0, "LDBL": 632},
    {"report_date": "2020-12-31", "TOTAL_ASSETS": 1300e8, "TOTAL_LIABILITIES": 300e8,
     "TOTAL_EQUITY": 1000e8, "TOTAL_PARENT_EQUITY": 1000e8,
     "TOTAL_CURRENT_ASSETS": 1000e8, "TOTAL_CURRENT_LIAB": 180e8,
     "FIXED_ASSET": 160e8, "CASH": 400e8, "MONETARY_FUNDS": 400e8,
     "ACCOUNTS_RECE": 2.5e8, "INVENTORY": 200e8, "GOODWILL": 10e8,
     "SHORT_LOAN": 30e8, "LONG_LOAN": 60e8, "BOND_PAYABLE": 0,
     "UNDISTRIBUTED_PROFIT": 700e8, "RETAINED_EARNINGS": 700e8,
     "CURRENT_RATIO": 556, "DEBT_ASSET_RATIO": 23.1, "ZCFZL": 23.1, "LDBL": 556},
]

MOCK_CASHFLOW = [
    {"report_date": "2024-12-31", "NETCASH_OPERATE": 600e8, "NETCASH_INVEST": -100e8,
     "NETCASH_FINANCE": -200e8, "BUY_FIX_ASSET_OTHER": 100e8},
    {"report_date": "2023-12-31", "NETCASH_OPERATE": 550e8, "NETCASH_INVEST": -90e8,
     "NETCASH_FINANCE": -180e8, "BUY_FIX_ASSET_OTHER": 90e8},
    {"report_date": "2022-12-31", "NETCASH_OPERATE": 500e8, "NETCASH_INVEST": -80e8,
     "NETCASH_FINANCE": -160e8, "BUY_FIX_ASSET_OTHER": 80e8},
    {"report_date": "2021-12-31", "NETCASH_OPERATE": 450e8, "NETCASH_INVEST": -70e8,
     "NETCASH_FINANCE": -140e8, "BUY_FIX_ASSET_OTHER": 70e8},
    {"report_date": "2020-12-31", "NETCASH_OPERATE": 400e8, "NETCASH_INVEST": -60e8,
     "NETCASH_FINANCE": -120e8, "BUY_FIX_ASSET_OTHER": 60e8},
]

MOCK_INDICATORS = [
    {"report_date": "2024-12-31", "ROE": 30.0, "ROEJQ": 30.0, "ROA": 25.0,
     "GROSS_PROFIT_RATIO": 91.3, "XSJLL": 91.3, "DEBT_ASSET_RATIO": 16.0,
     "ZCFZL": 16.0, "CURRENT_RATIO": 750, "LDBL": 750,
     "REVENUE_GROWTH": 15.0, "PROFIT_GROWTH": 18.0,
     "TOTAL_OPERATE_INCOME": 1500e8, "PARENT_NETPROFIT": 700e8, "TOTAL_ASSETS": 2500e8},
    {"report_date": "2023-12-31", "ROE": 28.0, "ROEJQ": 28.0, "ROA": 24.0,
     "GROSS_PROFIT_RATIO": 91.2, "XSJLL": 91.2, "DEBT_ASSET_RATIO": 17.3,
     "ZCFZL": 17.3, "CURRENT_RATIO": 696, "LDBL": 696,
     "REVENUE_GROWTH": 14.0, "PROFIT_GROWTH": 16.0,
     "TOTAL_OPERATE_INCOME": 1300e8, "PARENT_NETPROFIT": 600e8, "TOTAL_ASSETS": 2200e8},
    {"report_date": "2022-12-31", "ROE": 27.0, "ROEJQ": 27.0, "ROA": 23.0,
     "GROSS_PROFIT_RATIO": 91.2, "XSJLL": 91.2, "DEBT_ASSET_RATIO": 18.4,
     "ZCFZL": 18.4, "CURRENT_RATIO": 667, "LDBL": 667,
     "REVENUE_GROWTH": 13.0, "PROFIT_GROWTH": 15.0,
     "TOTAL_OPERATE_INCOME": 1140e8, "PARENT_NETPROFIT": 520e8, "TOTAL_ASSETS": 1900e8},
    {"report_date": "2021-12-31", "ROE": 26.0, "ROEJQ": 26.0, "ROA": 22.0,
     "GROSS_PROFIT_RATIO": 91.0, "XSJLL": 91.0, "DEBT_ASSET_RATIO": 20.0,
     "ZCFZL": 20.0, "CURRENT_RATIO": 632, "LDBL": 632,
     "REVENUE_GROWTH": 12.0, "PROFIT_GROWTH": 14.0,
     "TOTAL_OPERATE_INCOME": 1000e8, "PARENT_NETPROFIT": 450e8, "TOTAL_ASSETS": 1600e8},
    {"report_date": "2020-12-31", "ROE": 25.0, "ROEJQ": 25.0, "ROA": 21.0,
     "GROSS_PROFIT_RATIO": 91.0, "XSJLL": 91.0, "DEBT_ASSET_RATIO": 23.1,
     "ZCFZL": 23.1, "CURRENT_RATIO": 556, "LDBL": 556,
     "REVENUE_GROWTH": 11.0, "PROFIT_GROWTH": 13.0,
     "TOTAL_OPERATE_INCOME": 890e8, "PARENT_NETPROFIT": 400e8, "TOTAL_ASSETS": 1300e8},
]

MOCK_FINANCIALS = {
    "income": MOCK_INCOME,
    "balance": MOCK_BALANCE,
    "cashflow": MOCK_CASHFLOW,
    "indicators": MOCK_INDICATORS,
    "shareholders": {"top10": [{"name": "大股东", "pct": 55.0}], "controller": "大股东", "institutional_pct": 15.0, "latest_date": "2024-12-31"},
    "dividends": [{"report_date": "2024-12-31", "total_amount": 200e8}, {"report_date": "2023-12-31", "total_amount": 180e8}],
    "management": {"board_size": 11, "independent_directors": 4, "independent_pct": 36.4, "top3_salary": 500e4, "exec_list": []},
}


# ============================================================
# WACC 测试
# ============================================================

class TestWACC:
    def test_beta_with_sufficient_data(self):
        from stock_researcher.value_investing.wacc import calc_beta
        # 构造完全正相关的收益序列
        stock_rets = [0.01 * i for i in range(1, 31)]
        bench_rets = [0.01 * i for i in range(1, 31)]
        beta = calc_beta(stock_rets, bench_rets, window=60)
        assert 0.9 <= beta <= 1.1  # 完全正相关 beta 应接近 1

    def test_beta_insufficient_data_returns_default(self):
        from stock_researcher.value_investing.wacc import calc_beta
        beta = calc_beta([0.01, 0.02, 0.03], [0.01, 0.02, 0.03], window=60)
        assert beta == 1.0  # 数据不足返回默认 1.0

    def test_cost_of_equity_capm(self):
        from stock_researcher.value_investing.wacc import calc_cost_of_equity
        ke = calc_cost_of_equity(beta=1.2, rf=0.03, erp=0.06)
        assert abs(ke - 0.102) < 1e-6  # 3% + 1.2 × 6% = 10.2%

    def test_cost_of_debt_with_valid_data(self):
        from stock_researcher.value_investing.wacc import calc_cost_of_debt
        kd = calc_cost_of_debt(interest_expense=5e8, total_debt=100e8, tax_rate=0.25)
        # 5% 税前 × 0.75 = 3.75%
        assert abs(kd - 0.0375) < 1e-6

    def test_cost_of_debt_zero_debt(self):
        from stock_researcher.value_investing.wacc import calc_cost_of_debt
        assert calc_cost_of_debt(5e8, 0, 0.25) == 0.0

    def test_wacc_clipped_to_range(self):
        from stock_researcher.value_investing.wacc import calc_wacc
        # 极高 beta + 高负债 -> WACC 应被 clip 到 [6%, 15%]
        result = calc_wacc(
            code="TEST",
            stock_returns=[0.05 * i for i in range(1, 61)],
            benchmark_returns=[0.001] * 60,
            interest_expense=1e10,
            total_debt=1e12,
            market_cap=1e10,
        )
        assert 0.06 <= result["wacc"] <= 0.15


# ============================================================
# 护城河测试
# ============================================================

class TestMoat:
    def test_moat_analysis_with_mock_data(self):
        from stock_researcher.value_investing.moat import MoatAnalyzer
        analyzer = MoatAnalyzer(years=5)
        result = analyzer.analyze("TEST", financials=MOCK_FINANCIALS)
        assert not result.insufficient_data
        assert 0 <= result.moat_score <= 100
        assert result.moat_type in ("宽护城河", "窄护城河", "无显著护城河")
        assert len(result.sub_scores) > 0
        assert len(result.evidence) > 0

    def test_moat_high_gross_margin_gets_high_score(self):
        """毛利率 91% 的公司应有较高护城河分"""
        from stock_researcher.value_investing.moat import MoatAnalyzer
        analyzer = MoatAnalyzer(years=5)
        result = analyzer.analyze("TEST", financials=MOCK_FINANCIALS)
        # 91% 毛利率 + 高稳定性 -> 高分
        assert result.moat_score >= 60
        assert "毛利率" in result.evidence[0]

    def test_moat_insufficient_data(self):
        from stock_researcher.value_investing.moat import MoatAnalyzer
        analyzer = MoatAnalyzer(years=5)
        result = analyzer.analyze("TEST", financials={"income": [], "balance": []})
        assert result.insufficient_data


# ============================================================
# 财务健康测试
# ============================================================

class TestFinancialHealth:
    def test_altman_z_safe_company(self):
        """高现金流/低负债公司 Altman Z 应在安全区（>2.99）"""
        from stock_researcher.value_investing.financial_health import FinancialHealthChecker
        checker = FinancialHealthChecker(years=5)
        z = checker.calc_altman_z(MOCK_BALANCE, MOCK_INCOME, market_cap=2e12)
        assert z is not None
        assert z > 2.99  # 安全区

    def test_piotroski_f_strong_company(self):
        """营收/利润/现金流均增长的公司 F-score 应较高"""
        from stock_researcher.value_investing.financial_health import FinancialHealthChecker
        checker = FinancialHealthChecker(years=5)
        f = checker.calc_piotroski_f(MOCK_INDICATORS, MOCK_BALANCE, MOCK_INCOME, MOCK_CASHFLOW)
        assert f is not None
        assert 5 <= f <= 9  # 中到强

    def test_beneish_m_skipped_when_sga_missing(self):
        """当 SALE_EXPENSE/MANAGE_EXPENSE 为 0 时 Beneish 应返回 None"""
        from stock_researcher.value_investing.financial_health import FinancialHealthChecker
        checker = FinancialHealthChecker(years=5)
        # 构造无 SGA 数据的利润表
        income_no_sga = [
            {**MOCK_INCOME[0], "SALE_EXPENSE": 0, "MANAGE_EXPENSE": 0},
            {**MOCK_INCOME[1], "SALE_EXPENSE": 0, "MANAGE_EXPENSE": 0},
        ]
        m = checker.calc_beneish_m(income_no_sga, MOCK_BALANCE[:2], MOCK_CASHFLOW[:2])
        assert m is None  # 关键字段缺失时返回 None

    def test_health_check_with_mock_data(self):
        from stock_researcher.value_investing.financial_health import FinancialHealthChecker
        checker = FinancialHealthChecker(years=5)
        result = checker.check("TEST", market_cap=2e12, financials=MOCK_FINANCIALS)
        assert not result.insufficient_data
        assert 0 <= result.score <= 100
        assert result.grade in ("A", "B", "C", "D")
        assert "altman_z" in result.sub_scores
        assert "piotroski_f" in result.sub_scores

    def test_health_red_flags_for_distressed_company(self):
        """负债率 >80% + 低市值 + 亏损的公司 Altman Z 应在危险区（<1.81）"""
        from stock_researcher.value_investing.financial_health import FinancialHealthChecker
        checker = FinancialHealthChecker(years=5)
        # 构造全维度恶化的困境公司
        bad_balance = [{
            "TOTAL_ASSETS": 100e8, "TOTAL_LIABILITIES": 90e8,
            "TOTAL_EQUITY": 10e8, "TOTAL_PARENT_EQUITY": 10e8,
            "TOTAL_CURRENT_ASSETS": 20e8, "TOTAL_CURRENT_LIAB": 70e8,
            "FIXED_ASSET": 70e8, "CASH": 5e8, "MONETARY_FUNDS": 5e8,
            "ACCOUNTS_RECE": 10e8, "INVENTORY": 5e8, "GOODWILL": 0,
            "SHORT_LOAN": 50e8, "LONG_LOAN": 30e8, "BOND_PAYABLE": 10e8,
            "UNDISTRIBUTED_PROFIT": -20e8, "RETAINED_EARNINGS": -20e8,
            "CURRENT_RATIO": 28.6, "DEBT_ASSET_RATIO": 90.0, "ZCFZL": 90.0, "LDBL": 28.6,
        }]
        bad_income = [{
            "TOTAL_OPERATE_INCOME": 50e8, "OPERATE_INCOME": 50e8,
            "OPERATE_COST": 45e8, "PARENT_NETPROFIT": -5e8, "NETPROFIT": -5e8,
            "OPERATE_PROFIT": -2e8, "TOTAL_PROFIT": -5e8,
            "FINANCE_EXPENSE": 8e8,  # 高利息支出
        }]
        z = checker.calc_altman_z(bad_balance, bad_income, market_cap=5e8)
        assert z < 1.81  # 危险区


# ============================================================
# DCF 估值测试
# ============================================================

class TestDCFValuation:
    def test_dcf_intrinsic_value_positive(self):
        """FCF > 0 时内在价值应为正"""
        from stock_researcher.value_investing.dcf_valuation import DCFValuation
        valuator = DCFValuation(forecast_years=5)
        result = valuator.valuate(
            "TEST", current_price=1000, shares_outstanding=12.5e8,
            market_cap=1.25e12, financials=MOCK_FINANCIALS,
        )
        assert not result.insufficient_data
        assert result.intrinsic_value_per_share > 0
        assert len(result.fair_value_range) == 3
        assert len(result.sensitivity) == 3  # WACC ±1%

    def test_dcf_sensitivity_matrix(self):
        """敏感性矩阵应有 3×3 = 9 个值"""
        from stock_researcher.value_investing.dcf_valuation import DCFValuation
        valuator = DCFValuation(forecast_years=5)
        result = valuator.valuate(
            "TEST", current_price=1000, shares_outstanding=12.5e8,
            market_cap=1.25e12, financials=MOCK_FINANCIALS,
        )
        for wacc_key, row in result.sensitivity.items():
            assert len(row) == 3  # 终值增长 ±0.5%

    def test_dcf_shares_from_eps(self):
        """未提供 shares_outstanding 时从 EPS + 净利润推导"""
        from stock_researcher.value_investing.dcf_valuation import DCFValuation
        valuator = DCFValuation(forecast_years=5)
        result = valuator.valuate(
            "TEST", current_price=1000, shares_outstanding=0,
            market_cap=0, financials=MOCK_FINANCIALS,
        )
        # EPS=55, 净利润=700e8 -> shares = 700e8/55 ≈ 12.73e8
        # 内在价值应为正
        assert result.intrinsic_value_per_share > 0

    def test_dcf_insufficient_data(self):
        from stock_researcher.value_investing.dcf_valuation import DCFValuation
        valuator = DCFValuation(forecast_years=5)
        result = valuator.valuate("TEST", financials={"cashflow": []})
        assert result.insufficient_data


# ============================================================
# 管理层评估测试
# ============================================================

class TestManagement:
    def test_management_score_with_mock_data(self):
        from stock_researcher.value_investing.management import ManagementAssessment
        assessor = ManagementAssessment(years=5)
        result = assessor.assess("TEST", financials=MOCK_FINANCIALS)
        assert not result.insufficient_data
        assert 0 <= result.score <= 100
        assert result.verdict in ("优秀", "良好", "一般", "较差")
        assert "roe_roic_trend" in result.sub_scores

    def test_dupont_breakdown(self):
        from stock_researcher.value_investing.management import ManagementAssessment
        assessor = ManagementAssessment(years=5)
        result = assessor.assess("TEST", financials=MOCK_FINANCIALS)
        if result.dupont_breakdown:
            assert "net_margin" in result.dupont_breakdown
            assert "asset_turnover" in result.dupont_breakdown
            assert "equity_multiplier" in result.dupont_breakdown


# ============================================================
# 决策整合测试
# ============================================================

class TestDecisionIntegration:
    def test_decision_weights_sum_to_one(self):
        from stock_researcher.value_investing.decision_integration import ValueInvestingDecision
        total = sum(ValueInvestingDecision.WEIGHTS.values())
        assert abs(total - 1.0) < 1e-6

    def test_dcf_to_score_mapping(self):
        from stock_researcher.value_investing.decision_integration import ValueInvestingDecision
        from stock_researcher.value_investing.dcf_valuation import DCFResult
        # 安全边际 60% -> 高分
        dcf = DCFResult(code="TEST", margin_of_safety_pct=60, intrinsic_value_per_share=1000, insufficient_data=False)
        score = ValueInvestingDecision._dcf_to_score(dcf)
        assert score == 100
        # 安全边际 -50% -> 低分
        dcf2 = DCFResult(code="TEST", margin_of_safety_pct=-50, intrinsic_value_per_share=1000, insufficient_data=False)
        score2 = ValueInvestingDecision._dcf_to_score(dcf2)
        assert score2 == 10

    def test_signal_agreement(self):
        from stock_researcher.value_investing.decision_integration import ValueInvestingDecision
        # 6 个模块全部 >65（看多）-> 一致性 = 1
        breakdown = {k: {"score": 80, "weight": 0.15} for k in ["dcf", "moat", "health", "mgmt", "industry", "factor"]}
        agreement = ValueInvestingDecision._signal_agreement(breakdown)
        assert agreement == 1.0
        # 3 看多 + 3 看空 -> 一致性 = 0
        breakdown2 = {}
        for i, k in enumerate(["dcf", "moat", "health", "mgmt", "industry", "factor"]):
            breakdown2[k] = {"score": 80 if i < 3 else 20, "weight": 0.15}
        agreement2 = ValueInvestingDecision._signal_agreement(breakdown2)
        assert agreement2 == 0.0


# ============================================================
# 数据不足降级测试
# ============================================================

class TestInsufficientData:
    def test_moat_degrades_gracefully(self):
        """只有 1 年数据时，护城河分析应降级（仅用可用维度），不报 insufficient_data"""
        from stock_researcher.value_investing.moat import MoatAnalyzer
        analyzer = MoatAnalyzer(years=5)
        # 只有 1 年数据 -> 部分维度（毛利率稳定性/ROIC一致性等需3年）不可用
        # 但 pricing_power/market_share 仅需 1 年 -> 仍可计算
        result = analyzer.analyze("TEST", financials={
            "income": MOCK_INCOME[:1], "balance": MOCK_BALANCE[:1], "indicators": MOCK_INDICATORS[:1]
        })
        # 应使用降级模式：子评分维度 < 7（部分维度不可用）
        assert len(result.sub_scores) < 7
        # 仍应输出评分（不因部分数据缺失而完全失败）
        assert 0 <= result.moat_score <= 100

    def test_moat_empty_data_returns_insufficient(self):
        """空数据时应返回 insufficient_data"""
        from stock_researcher.value_investing.moat import MoatAnalyzer
        analyzer = MoatAnalyzer(years=5)
        result = analyzer.analyze("TEST", financials={"income": [], "balance": []})
        assert result.insufficient_data

    def test_health_degrades_gracefully(self):
        from stock_researcher.value_investing.financial_health import FinancialHealthChecker
        checker = FinancialHealthChecker(years=5)
        result = checker.check("TEST", financials={"income": [], "balance": [], "cashflow": [], "indicators": []})
        assert result.insufficient_data

    def test_dcf_degrades_gracefully(self):
        from stock_researcher.value_investing.dcf_valuation import DCFValuation
        valuator = DCFValuation(forecast_years=5)
        result = valuator.valuate("TEST", financials={"cashflow": MOCK_CASHFLOW[:2], "income": [], "balance": []})
        assert result.insufficient_data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
