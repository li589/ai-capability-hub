#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fusion 包 — 多源信号融合与多周期预测编排 (v4.0.0 新增)

子模块：
- signal_collector:        全维度信号归一化收集 -> SignalBundle
- multi_horizon_forecaster: 1d/3d/5d/1M/1Q 多周期预测编排
"""
from .signal_collector import SignalCollector, SignalBundle, DimensionSignal
from .multi_horizon_forecaster import (
    MultiHorizonForecaster, ForecastResult,
    forecast_stock, forecast_sector, HORIZONS
)

__all__ = [
    "SignalCollector", "SignalBundle", "DimensionSignal",
    "MultiHorizonForecaster", "ForecastResult",
    "forecast_stock", "forecast_sector", "HORIZONS",
]
