#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""research 包 - 券商研报 / 国际宏观信号 / 定期报告解读 (v4.0.0 新增)

子模块：
- broker_research:  券商研究报告 / 机构评级 / 一致预期 / 目标价
- macro_signals:    国际宏观与新闻信号 (美元/美债/大宗/汇率/外围指数)
- financial_report: 定期报告解读 (年报/半年报/季报 同比环比 + 亮点风险)
"""
from .broker_research import BrokerResearcher, analyze_broker_research
from .macro_signals import MacroSignalCollector, get_macro_signals
from .financial_report import (
    FinancialReportInterpreter,
    ReportInterpretation,
    interpret_report,
    format_report,
)

__all__ = [
    "BrokerResearcher",
    "analyze_broker_research",
    "MacroSignalCollector",
    "get_macro_signals",
    "FinancialReportInterpreter",
    "ReportInterpretation",
    "interpret_report",
    "format_report",
]
