#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资分析框架（v5.0 新增）

6 大模块 + 决策整合，基于价值投资经典方法论：
- 护城河分析 (MoatAnalyzer)
- 财务健康检查 (FinancialHealthChecker)
- DCF 估值 (DCFValuation)
- 管理层评估 (ManagementAssessment)
- 行业分析 (IndustryAnalyzer)
- 投资决策整合 (ValueInvestingDecision)

辅助模块:
- WACC/CAPM 折现率 (calc_wacc)
"""
from __future__ import annotations

from .wacc import calc_wacc, calc_risk_free_rate, calc_beta, calc_cost_of_equity
from .moat import MoatAnalyzer, MoatResult
from .financial_health import FinancialHealthChecker, HealthResult
from .dcf_valuation import DCFValuation, DCFResult
from .management import ManagementAssessment, ManagementResult
from .industry_analysis import IndustryAnalyzer, IndustryResult, SECTOR_REPS
from .decision_integration import ValueInvestingDecision, DecisionReport

__all__ = [
    "calc_wacc",
    "calc_risk_free_rate",
    "calc_beta",
    "calc_cost_of_equity",
    "MoatAnalyzer",
    "MoatResult",
    "FinancialHealthChecker",
    "HealthResult",
    "DCFValuation",
    "DCFResult",
    "ManagementAssessment",
    "ManagementResult",
    "IndustryAnalyzer",
    "IndustryResult",
    "SECTOR_REPS",
    "ValueInvestingDecision",
    "DecisionReport",
]

__version__ = "6.0.0"
