#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""recommendation 包 — 投资推荐引擎 (v4.0.0 新增)

- recommendation_engine: 基于融合预测的短/中/长期板块+个股推荐(带具体理由)
- fund_recommender: 基金推荐(复用 fund_analyzer 评分+归因)
"""
from .recommendation_engine import RecommendationEngine, get_recommendations
from .fund_recommender import FundRecommender, get_fund_recommendations

__all__ = [
    "RecommendationEngine", "get_recommendations",
    "FundRecommender", "get_fund_recommendations",
]
