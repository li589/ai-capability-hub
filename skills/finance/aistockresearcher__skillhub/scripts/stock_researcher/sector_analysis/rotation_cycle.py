#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""板块轮动周期阶段检测 (v9.0.0 新增)
====================================
经典美林时钟 / Martin Pring 风格的经济周期板块轮动模型。

不同经济周期阶段（早周期 / 中周期 / 晚周期 / 衰退）受益板块不同：
  - 早周期（复苏）：可选消费、金融、地产、工业、原材料（经济触底回升）
  - 中周期（扩张）：科技、通信、资本品、工业（增长强劲，风险偏好高）
  - 晚周期（过热）：能源、大宗、必需消费、公用事业（通胀升温，防御资源）
  - 衰退：公用事业、医疗、必需消费、债券（避险为主）

本模块综合「全球风险偏好 + 利率/通胀趋势 + 板块相对强度结构」推断当前
所处阶段概率，给出受益/回避板块与配置倾斜建议。

注意：阶段判定基于公开宏观与价格信号的启发式综合，非精确预测，仅供决策参考。

用法:
    from stock_researcher.sector_analysis.rotation_cycle import RotationCycleDetector
    stage = RotationCycleDetector().detect(market="cn")
    print(stage.stage, stage.favored_sectors)
"""

from __future__ import annotations

from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ── 周期阶段 → 受益/回避板块（A 股口径，跨市场可近似） ──
CYCLE_SECTOR_MAP = {
    "早周期": {
        "favored": ["可选消费", "汽车", "房地产", "非银金融", "银行", "化工", "有色金属", "机械设备"],
        "avoid": ["公用事业", "必需消费", "医药生物"],
        "rationale": "经济触底复苏，利率低位，周期与可选消费领先",
    },
    "中周期": {
        "favored": ["电子", "计算机", "通信", "传媒", "新能源", "军工", "机械设备"],
        "avoid": ["公用事业", "房地产"],
        "rationale": "扩张期增长强劲、风险偏好高，成长与科技跑赢",
    },
    "晚周期": {
        "favored": ["有色金属", "化工", "能源", "食品饮料", "医药生物", "银行"],
        "avoid": ["可选消费", "房地产", "军工"],
        "rationale": "通胀升温、利率走高，资源品与防御价值占优",
    },
    "衰退": {
        "favored": ["公用事业", "医药生物", "食品饮料", "银行", "通信"],
        "avoid": ["可选消费", "有色金属", "化工", "军工", "房地产"],
        "rationale": "经济下行、避险为主，必需消费与稳定现金流板块抗跌",
    },
}

STAGE_KEYS = ["早周期", "中周期", "晚周期", "衰退"]


@dataclass
class CycleStageResult:
    """轮动周期阶段结果"""
    market: str = "cn"
    stage: str = "中周期"              # 早周期/中周期/晚周期/衰退
    probabilities: Dict[str, float] = field(default_factory=dict)  # 各阶段概率 0-1
    confidence: float = 0.0           # 置信度 0-1
    favored_sectors: List[str] = field(default_factory=list)
    avoid_sectors: List[str] = field(default_factory=list)
    rationale: str = ""
    signals: Dict = field(default_factory=dict)   # 原始信号明细
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数：从信号 → 阶段概率（离线可测）
# ════════════════════════════════════════════════════════════

def stage_probabilities(
    growth_signal: float,
    inflation_signal: float,
    risk_appetite: float,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """由增长/通胀/风险偏好三信号推断各周期阶段概率。

    Args:
        growth_signal: 增长动能，>0 扩张、<0 收缩（如 PMI-50、或工业产出趋势）
        inflation_signal: 通胀趋势，>0 上行、<0 下行（如 CPI 同比变化）
        risk_appetite: 风险偏好，>0 risk-on、<0 risk-off（如全球风险偏好分）
        weights: 可选阶段权重先验

    Returns:
        {阶段: 概率}，四阶段之和=1
    逻辑（简化美林时钟）：
        早周期: 增长回升(+)、通胀低(-)、风险偏好回升(+) → growth↑, infl<=0
        中周期: 增长强(++)、通胀温和、risk-on(++) → growth>0 & risk>0
        晚周期: 增长见顶、通胀高(++)、风险偏好见顶 → infl>0
        衰退: 增长下行(--)、通胀回落、risk-off(--) → growth<0 & risk<0
    """
    g = float(growth_signal)
    i = float(inflation_signal)
    r = float(risk_appetite)

    raw = {
        "早周期": max(0.05, 0.2 + 0.5 * g - 0.3 * i + 0.3 * r),
        "中周期": max(0.05, 0.2 + 0.4 * g + 0.1 * i + 0.5 * r),
        "晚周期": max(0.05, 0.2 - 0.1 * g + 0.6 * i + 0.1 * r),
        "衰退":   max(0.05, 0.2 - 0.5 * g - 0.2 * i - 0.5 * r),
    }
    # 应用先验权重
    if weights:
        for k in raw:
            raw[k] *= weights.get(k, 1.0)
    total = sum(raw.values())
    if total <= 0:
        return {k: 0.25 for k in STAGE_KEYS}
    return {k: round(v / total, 3) for k, v in raw.items()}


def pick_stage(probs: Dict[str, float]) -> tuple:
    """选概率最高阶段。返回 (stage, confidence)。"""
    if not probs:
        return "中周期", 0.0
    stage = max(probs, key=probs.get)
    return stage, probs[stage]


# ════════════════════════════════════════════════════════════
# 数据接线层
# ════════════════════════════════════════════════════════════

class RotationCycleDetector:
    """板块轮动周期阶段检测器。"""

    def detect(self, market: str = "cn") -> CycleStageResult:
        growth = self._growth_signal(market)
        inflation = self._inflation_signal(market)
        risk = self._risk_signal()
        signals = {
            "growth_signal": round(growth, 3),
            "inflation_signal": round(inflation, 3),
            "risk_appetite": round(risk, 3),
        }
        probs = stage_probabilities(growth, inflation, risk)
        stage, conf = pick_stage(probs)
        cfg = CYCLE_SECTOR_MAP.get(stage, CYCLE_SECTOR_MAP["中周期"])

        return CycleStageResult(
            market=market, stage=stage, probabilities=probs,
            confidence=round(conf, 3),
            favored_sectors=list(cfg["favored"]),
            avoid_sectors=list(cfg["avoid"]),
            rationale=cfg["rationale"],
            signals=signals,
            note="基于宏观+风险偏好+板块结构的启发式综合",
        )

    # ── 增长信号：PMI-50（>0 扩张）；失败降级 0 ──
    def _growth_signal(self, market: str) -> float:
        try:
            from stock_researcher.data.macro import MacroData
            md = MacroData()
            pmi = md.fetch_macro_indicator("pmi") or {}
            val = float(pmi.get("value", 0) or 0)
            if val > 0:
                return val - 50.0  # PMI 围绕 50 荣枯线
        except Exception:
            pass
        return 0.0

    # ── 通胀信号：CPI 同比变化方向（>0 上行）；失败降级 0 ──
    def _inflation_signal(self, market: str) -> float:
        try:
            from stock_researcher.data.macro import MacroData
            md = MacroData()
            cpi = md.fetch_macro_indicator("cpi") or {}
            val = float(cpi.get("value", 0) or 0)
            prev = float(cpi.get("previous", 0) or 0)
            # 用同比绝对水平 + 环比变化方向
            return (val - 2.0) / 2.0 + (val - prev) / 1.0  # 偏离 2% 目标 + 环比
        except Exception:
            pass
        return 0.0

    # ── 风险偏好：全球风险偏好分（-100..+100 归一） ──
    def _risk_signal(self) -> float:
        try:
            from stock_researcher.data.global_market import get_global_risk_appetite
            ra = get_global_risk_appetite() or {}
            score = float(ra.get("score", 0) or 0)
            return score / 100.0  # 归一到 -1..+1
        except Exception:
            pass
        return 0.0

    @staticmethod
    def format(r: CycleStageResult) -> str:
        probs = " ".join(f"{k}:{v:.0%}" for k, v in r.probabilities.items())
        return (
            f"周期阶段: {r.stage} (置信{r.confidence:.0%}) | {probs}\n"
            f"  受益: {', '.join(r.favored_sectors)}\n"
            f"  回避: {', '.join(r.avoid_sectors)}\n"
            f"  逻辑: {r.rationale}"
        )


def detect_cycle_stage(market: str = "cn") -> CycleStageResult:
    """便捷函数：当前轮动周期阶段。"""
    return RotationCycleDetector().detect(market=market)
