#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""advisor 包 — 用户画像与投资顾问 (v4.0.0 新增)

- user_profile:    用户画像模型(风险偏好/预期收益/投资时长/总金额) + 持久化
- portfolio_analyzer: 持仓组合级分析(Beta/行业暴露/集中度/波动/最大回撤)
- rebalance_advisor: 调仓建议引擎(画像 vs 持仓 gap → 具体动作+理由)
"""
from .user_profile import UserProfile, load_profile, save_profile
from .portfolio_analyzer import PortfolioAnalyzer
from .rebalance_advisor import RebalanceAdvisor, RebalanceAction

__all__ = [
    "UserProfile", "load_profile", "save_profile",
    "PortfolioAnalyzer",
    "RebalanceAdvisor", "RebalanceAction",
]
