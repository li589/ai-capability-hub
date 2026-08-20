#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""信号共识度分析 (v9.0.0 新增)
============================
十维信号融合时，「信号之间是否一致」本身就是信息。

- 高共识（多数信号同向）：趋势确认，置信度提升
- 高分歧（多空各半）：典型顶/底/转折区域，置信度下降，且历史上
  高分歧后均值回归概率上升

本模块从一组 DimensionSignal 计算共识度，并给出对置信度的调整建议。
纯逻辑，不联网，可对任意 (score, direction) 列表计算。

用法:
    from stock_researcher.fusion.signal_consensus import SignalConsensus
    c = SignalConsensus().compute(dimensions)   # dimensions: List[DimensionSignal]
    print(c.consensus_score, c.dispersion, c.confidence_multiplier)
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence
from dataclasses import dataclass, field


@dataclass
class ConsensusResult:
    """信号共识度结果"""
    consensus_score: float = 0.0     # -100..+100（正=多数看多共识，负=看空共识）
    agreement_ratio: float = 0.0     # 0-1，最大阵营占比（共识强度）
    dispersion: float = 0.0          # 0-100，分歧度（越高越分歧）
    bull_count: int = 0
    bear_count: int = 0
    neutral_count: int = 0
    confidence_multiplier: float = 1.0   # 对置信度的乘数建议 0.6-1.1
    mean_reversion_tilt: float = 0.0     # >0 建议向均值回归倾斜（高分歧时）
    label: str = "中性"                  # 强共识看多/强共识看空/分歧/中性

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层（接受简单 (score,direction) 结构，便于测试）
# ════════════════════════════════════════════════════════════

def _direction_of(score: float) -> int:
    """得分 → 方向：+1 多 / -1 空 / 0 中性。"""
    if score > 8:
        return 1
    if score < -8:
        return -1
    return 0


def compute_consensus(
    scores: Sequence[float],
    directions: Optional[Sequence[int]] = None,
) -> ConsensusResult:
    """从一组信号得分计算共识度。

    Args:
        scores: 各维度得分(-100..+100)
        directions: 可选显式方向(+1/-1/0)；不传则由 score 阈值推断
    """
    s = [float(x) for x in scores if x is not None and math.isfinite(float(x))]
    if not s:
        return ConsensusResult(label="无信号")
    dirs = list(directions) if directions is not None else [_direction_of(x) for x in s]

    bull = sum(1 for d in dirs if d > 0)
    bear = sum(1 for d in dirs if d < 0)
    neutral = sum(1 for d in dirs if d == 0)
    n = len(dirs)

    # 加权共识分（按 |score| 加权方向）
    total_w = sum(abs(x) for x in s) + 1e-9
    signed = sum(s[i] * abs(s[i]) for i in range(len(s)))   # 强化强信号方向
    consensus = signed / total_w if total_w > 1e-9 else 0.0
    consensus = max(-100.0, min(100.0, consensus))

    # 共识强度：最大阵营占比
    agreement = max(bull, bear) / n if n else 0.0

    # 分歧度：1 - agreement（标准化到 0-100），并叠加得分符号的对抗
    if bull + bear > 0:
        balance = abs(bull - bear) / (bull + bear)   # 0=完全对抗, 1=一致
    else:
        balance = 1.0
    dispersion = (1.0 - balance) * 100.0
    # 中性信号多也拉高分歧感
    if neutral / n > 0.5:
        dispersion = max(dispersion, 60.0)

    # 置信度乘数：共识高 → 提升；分歧高 → 下降
    if agreement >= 0.7 and dispersion < 40:
        conf_mult = 1.10
    elif agreement <= 0.5 or dispersion >= 70:
        conf_mult = 0.70
    elif dispersion >= 55:
        conf_mult = 0.85
    else:
        conf_mult = 1.0

    # 均值回归倾斜：高分歧时 >0（历史上高分歧后均值回归概率升）
    mr_tilt = max(0.0, (dispersion - 50.0) / 50.0) if dispersion > 50 else 0.0

    # 标签
    if dispersion >= 70:
        label = "分歧"
    elif consensus > 25 and agreement >= 0.6:
        label = "强共识看多"
    elif consensus < -25 and agreement >= 0.6:
        label = "强共识看空"
    elif consensus > 8:
        label = "偏多共识"
    elif consensus < -8:
        label = "偏空共识"
    else:
        label = "中性"

    return ConsensusResult(
        consensus_score=round(consensus, 1),
        agreement_ratio=round(agreement, 3),
        dispersion=round(dispersion, 1),
        bull_count=bull, bear_count=bear, neutral_count=neutral,
        confidence_multiplier=conf_mult,
        mean_reversion_tilt=round(mr_tilt, 3),
        label=label,
    )


class SignalConsensus:
    """对 fusion.DimensionSignal 列表计算共识度。"""

    def compute(self, dimensions) -> ConsensusResult:
        """dimensions: List[DimensionSignal]（含 score/direction/available）。"""
        scores = []
        dirs = []
        for d in dimensions:
            # 跳过不可用维度
            if hasattr(d, "available") and not d.available:
                continue
            score = getattr(d, "score", 0.0) or 0.0
            direction = getattr(d, "direction", "")
            scores.append(float(score))
            dirs.append(self._dir_from_label(direction, score))
        return compute_consensus(scores, dirs)

    @staticmethod
    def _dir_from_label(direction: str, score: float) -> int:
        d = str(direction)
        if any(k in d for k in ("看多", "积极", "低估", "流入", "利多", "买入")):
            return 1
        if any(k in d for k in ("看空", "消极", "高估", "流出", "利空", "卖出")):
            return -1
        return _direction_of(score)


def consensus_from_scores(scores: Sequence[float]) -> ConsensusResult:
    """便捷函数：纯得分列表 → 共识度。"""
    return compute_consensus(scores)
