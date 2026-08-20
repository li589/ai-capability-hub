#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.1 多资产分析与推演模块"""
import sys
sys.dont_write_bytecode = True

from .five_dim_analyzer import FiveDimAnalyzer, quick_five_dim
from .asset_forecaster import AssetForecaster, quick_forecast, detect_asset_type
# v9.0 自上而下整合
from .top_down import TopDownReport, TopDownResult, build_topdown

__all__ = [
    "FiveDimAnalyzer", "quick_five_dim",
    "AssetForecaster", "quick_forecast", "detect_asset_type",
    # v9.0
    "TopDownReport", "TopDownResult", "build_topdown",
]