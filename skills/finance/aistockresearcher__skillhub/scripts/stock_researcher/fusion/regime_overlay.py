#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""体制条件化预测权重叠加层 (v9.0.0 新增)
==========================================
让预测融合层（multi_horizon_forecaster）「看懂」市场体制。

核心问题：v8.0 的 _fuse_scores 用固定权重线性融合十维信号，对体制盲。
但同一信号在不同体制下含义相反——
  - 牛市：技术动量延续（trend-following 有效），情绪/资金助推
  - 熊市：技术动量均值回归（超买即卖点），宏观/政策/估值主导
  - 震荡：动量衰减，估值/政策更关键

本模块提供：
  - REGIME_WEIGHTS：各体制×各周期×各维度的权重覆盖（克隆 ASSET_TYPE_WEIGHTS 形状）
  - apply_regime_weights()：把体制权重并入默认权重（体制优先）
  - momentum_dampening()：非牛市对动量类信号打折扣（保守，默认不翻号）
  - flip_momentum (opt-in)：熊市动量信号反转（激进均值回归模式）

设计：regime=None 时全部返回 None / 原样 → 调用方默认行为不变（向后兼容）。

用法:
    from stock_researcher.fusion.regime_overlay import RegimeOverlay
    w = RegimeOverlay.weights_for("熊市", "1M")      # 体制权重覆盖
    score = RegimeOverlay.momentum_dampening(30, "technical", "熊市")
"""

from __future__ import annotations

from typing import Dict, Optional


# 动量类维度（在熊市/震荡市需要折扣或反转）
MOMENTUM_DIMS = {"technical", "money_flow", "sentiment", "quant_factor"}
# 防御/基本面类维度（熊市更可靠）
DEFENSIVE_DIMS = {"valuation", "macro", "policy", "broker"}

KNOWN_REGIMES = ("牛市", "熊市", "震荡")


# ── 各体制 × 各周期 × 维度 权重覆盖 ──
# 形状与 multi_horizon_forecaster.ASSET_TYPE_WEIGHTS 一致，便于在同一处合并。
# 仅列出与默认权重的「差异」；未列出的维度沿用默认权重。
REGIME_WEIGHTS: Dict[str, Dict[str, Dict[str, float]]] = {
    "牛市": {
        "1d": {"technical": 0.34, "sentiment": 0.22, "money_flow": 0.22},
        "5d": {"technical": 0.22, "money_flow": 0.18, "sentiment": 0.14},
        "1M": {"technical": 0.18, "money_flow": 0.10, "broker": 0.20, "valuation": 0.16},
    },
    "熊市": {
        # 动量类大幅下调，防御/宏观/估值上调
        "1d": {"technical": 0.12, "sentiment": 0.10, "money_flow": 0.10,
               "macro": 0.18, "valuation": 0.12, "policy": 0.14},
        "5d": {"technical": 0.10, "money_flow": 0.08, "sentiment": 0.08,
               "valuation": 0.18, "macro": 0.18, "policy": 0.16, "broker": 0.14},
        "1M": {"valuation": 0.26, "macro": 0.20, "policy": 0.18,
               "broker": 0.16, "technical": 0.06, "money_flow": 0.04},
        "3M": {"valuation": 0.26, "policy": 0.24, "macro": 0.22,
               "broker": 0.14, "technical": 0.04},
        "6M": {"valuation": 0.28, "policy": 0.26, "macro": 0.24,
               "broker": 0.12, "technical": 0.02},
    },
    "震荡": {
        # 动量折扣，估值/政策主导（均值回归环境）
        "5d": {"technical": 0.12, "money_flow": 0.10, "valuation": 0.16,
               "policy": 0.14, "broker": 0.14},
        "1M": {"valuation": 0.24, "policy": 0.16, "broker": 0.18,
               "technical": 0.10, "macro": 0.14},
        "3M": {"valuation": 0.26, "policy": 0.22, "macro": 0.20,
               "broker": 0.16, "technical": 0.06},
    },
}

# 非牛市对动量类信号的得分折扣（保守：仅缩放，不翻号）
# 熊市动量衰减更狠；震荡温和衰减。
MOMENTUM_DAMPING: Dict[str, float] = {
    "牛市": 1.0,
    "熊市": 0.5,     # 动量信号强度折半
    "震荡": 0.7,
}

# 激进模式：熊市动量信号反转（均值回归）。仅 flip_momentum=True 时启用。
MOMENTUM_FLIP: Dict[str, float] = {
    "牛市": 1.0,
    "熊市": -0.6,    # 翻号并缩放
    "震荡": 0.4,     # 不翻号但大幅衰减
}


class RegimeOverlay:
    """体制条件化权重叠加器。"""

    @staticmethod
    def weights_for(regime: Optional[str], horizon: str) -> Optional[Dict[str, float]]:
        """取某体制某周期的权重覆盖。regime=None/未知 → None（沿用默认）。"""
        if not regime or regime not in REGIME_WEIGHTS:
            return None
        return REGIME_WEIGHTS[regime].get(horizon)

    @staticmethod
    def apply_regime_weights(
        default_weights: Dict[str, float],
        regime: Optional[str],
        horizon: str,
    ) -> Dict[str, float]:
        """把体制权重并入默认权重（体制覆盖优先），重新归一化。

        regime=None → 返回 default_weights 副本（不变）。
        """
        if not regime or regime not in REGIME_WEIGHTS:
            return dict(default_weights)
        overlay = REGIME_WEIGHTS[regime].get(horizon)
        if not overlay:
            return dict(default_weights)
        merged = dict(default_weights)
        merged.update(overlay)   # 体制覆盖
        # 归一化（保证和为 1）
        tot = sum(merged.values())
        if tot > 0:
            merged = {k: v / tot for k, v in merged.items()}
        return merged

    @staticmethod
    def momentum_dampening(
        score: float, dimension: str, regime: Optional[str],
        flip_momentum: bool = False,
    ) -> float:
        """对动量类信号按体制折扣/反转。

        - regime=None 或牛市 → 原样返回（向后兼容）
        - 非牛市的动量类维度 → 按 MOMENTUM_DAMPING 折扣（默认）
          flip_momentum=True 时按 MOMENTUM_FLIP（熊市翻号）
        - 非动量类维度 → 原样返回
        """
        if not regime or regime == "牛市" or regime not in MOMENTUM_DAMPING:
            return score
        if dimension not in MOMENTUM_DIMS:
            return score
        factor = MOMENTUM_FLIP.get(regime, 1.0) if flip_momentum else MOMENTUM_DAMPING.get(regime, 1.0)
        return score * factor

    @staticmethod
    def confidence_adjustment(regime: Optional[str]) -> float:
        """体制对置信度的调整（熊市信号噪声大 → 降置信）。

        返回乘数 0-1。牛市/None → 1.0（不变）。
        """
        if not regime:
            return 1.0
        return {"牛市": 1.0, "熊市": 0.85, "震荡": 0.92}.get(regime, 1.0)

    @staticmethod
    def is_known_regime(regime: Optional[str]) -> bool:
        return regime in KNOWN_REGIMES


# ── 便捷：从价格序列推断体制（复用既有检测器） ──

def detect_regime_from_prices(prices) -> Optional[str]:
    """复用 scenario_simulator.detect_market_regime_from_history。

    返回 牛市/熊市/高波动/震荡市；失败 None。
    """
    try:
        from stock_researcher.quantitative.scenario_simulator import (
            detect_market_regime_from_history,
        )
        return detect_market_regime_from_history(prices)
    except Exception:
        return None


def normalize_regime(regime: Optional[str]) -> Optional[str]:
    """把多种体制标签归一到 {牛市,熊市,震荡}。"""
    if not regime:
        return None
    r = str(regime)
    if "牛" in r or "bull" in r.lower():
        return "牛市"
    if "熊" in r or "bear" in r.lower():
        return "熊市"
    if "高波动" in r or "high" in r.lower():
        return "熊市"   # 高波动常伴下跌，归入熊市侧（保守）
    return "震荡"
