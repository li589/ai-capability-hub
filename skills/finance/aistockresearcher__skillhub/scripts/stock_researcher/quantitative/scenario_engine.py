#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""宏观情景引擎 (v9.0.0 新增)
========================
命名宏观情景分析 —— 把「单一基准预测」升级为「多情景概率加权」。

未来不可单点预测，但可枚举关键宏观情景并赋概率：
  - 软着陆（Soft Landing）：通胀回落、增长温和、风险偏好升
  - 硬着陆（Hard Landing）：衰退、风险偏好骤降
  - 通胀超预期（Inflation Surprise）：加息压力、成长股承压
  - 地缘升级（Geopolitical Escalation）：避险、商品涨
  - 政策刺激（Policy Stimulus）：流动性宽松、周期受益
  - 衰退（Recession）：防御为王

每个情景 → 对资产收益分布的偏移参数（漂移/波动/跳跃）。引擎输出：
  - 各情景下的预期收益与波动
  - 概率加权基准情景
  - 尾部风险（最差情景的下行）

纯逻辑（情景参数 + 蒙特卡洛可选），可对任意资产通用。

用法:
    from stock_researcher.quantitative.scenario_engine import MacroScenarioEngine
    rep = MacroScenarioEngine().analyze(base_return=0.10, base_vol=0.18)
    print(rep.base_case, rep.tail_risk)
"""

from __future__ import annotations

import math
import random
from typing import Dict, List, Optional
from dataclasses import dataclass, field


# ── 命名情景定义 ──
# 每个情景对「基准收益分布」的偏移：
#   drift_delta: 年化漂移增量（正=更看好）
#   vol_mult:    波动率乘数（>1 更波动）
#   jump_lambda: 跳跃频率（年化，>0 表示有尾部跳跃）
#   jump_mean:   跳跃均值（负=下行跳跃）
#   asset_tilt:  资产偏好（人为参考：哪些资产相对受益/受损）
SCENARIO_DEFS: Dict[str, Dict] = {
    "软着陆": {
        "drift_delta": 0.04, "vol_mult": 0.85, "jump_lambda": 0.0, "jump_mean": 0.0,
        "asset_tilt": {"成长股": +1, "周期股": +1, "债券": 0, "黄金": -1},
        "rationale": "通胀回落+增长温和，风险偏好上升，成长与周期受益",
    },
    "硬着陆": {
        "drift_delta": -0.12, "vol_mult": 1.50, "jump_lambda": 3.0, "jump_mean": -0.08,
        "asset_tilt": {"成长股": -2, "周期股": -2, "债券": +2, "黄金": +1},
        "rationale": "衰退风险，风险资产大幅下行，避险资产受益",
    },
    "通胀超预期": {
        "drift_delta": -0.05, "vol_mult": 1.25, "jump_lambda": 1.5, "jump_mean": -0.04,
        "asset_tilt": {"成长股": -2, "周期股": +1, "债券": -2, "黄金": +1, "商品": +2},
        "rationale": "加息压力升温，长久期成长股与债券承压，商品受益",
    },
    "地缘升级": {
        "drift_delta": -0.06, "vol_mult": 1.40, "jump_lambda": 2.5, "jump_mean": -0.06,
        "asset_tilt": {"股票": -1, "黄金": +2, "原油": +2, "美元": +1},
        "rationale": "避险情绪飙升，黄金/原油/美元受益，全球股票承压",
    },
    "政策刺激": {
        "drift_delta": 0.06, "vol_mult": 1.05, "jump_lambda": 0.5, "jump_mean": 0.03,
        "asset_tilt": {"周期股": +2, "基建": +2, "券商": +2, "债券": -1},
        "rationale": "流动性宽松+财政发力，周期/基建/券商直接受益",
    },
    "衰退": {
        "drift_delta": -0.15, "vol_mult": 1.30, "jump_lambda": 2.0, "jump_mean": -0.07,
        "asset_tilt": {"必需消费": +1, "公用事业": +2, "医药": +1, "周期股": -2, "债券": +2},
        "rationale": "经济下行，必需消费/公用事业/医药等防御板块抗跌",
    },
}

# 默认情景概率（应随宏观信号动态调整；这里给中性先验）
DEFAULT_PROBABILITIES: Dict[str, float] = {
    "软着陆": 0.30, "硬着陆": 0.15, "通胀超预期": 0.15,
    "地缘升级": 0.10, "政策刺激": 0.15, "衰退": 0.15,
}


@dataclass
class ScenarioOutcome:
    """单情景结果"""
    name: str
    probability: float
    expected_return: float    # 年化预期收益（小数）
    expected_vol: float       # 年化波动
    rationale: str = ""
    asset_tilt: Dict = field(default_factory=dict)


@dataclass
class ScenarioReport:
    """多情景分析报告"""
    base_return: float = 0.0
    base_vol: float = 0.0
    probabilities: Dict[str, float] = field(default_factory=dict)
    outcomes: List[ScenarioOutcome] = field(default_factory=list)
    weighted_return: float = 0.0      # 概率加权预期收益
    weighted_vol: float = 0.0
    tail_risk: float = 0.0            # 最差情景的预期收益（下行尾部）
    best_case: float = 0.0
    upside_probability: float = 0.0   # 正收益情景的概率和
    note: str = ""

    def get(self, key, default=None):
        return getattr(self, key, default)


# ════════════════════════════════════════════════════════════
# 纯函数层
# ════════════════════════════════════════════════════════════

def scenario_return(base_return: float, base_vol: float, scenario_name: str) -> tuple:
    """单情景下的 (预期收益, 预期波动)。"""
    s = SCENARIO_DEFS.get(scenario_name)
    if not s:
        return base_return, base_vol
    return base_return + s["drift_delta"], base_vol * s["vol_mult"]


def weighted_outcomes(
    base_return: float, base_vol: float,
    probabilities: Dict[str, float],
) -> List[ScenarioOutcome]:
    """计算所有情景的结果。"""
    out = []
    for name, p in probabilities.items():
        if name not in SCENARIO_DEFS:
            continue
        r, v = scenario_return(base_return, base_vol, name)
        out.append(ScenarioOutcome(
            name=name, probability=p,
            expected_return=round(r, 4),
            expected_vol=round(v, 4),
            rationale=SCENARIO_DEFS[name]["rationale"],
            asset_tilt=SCENARIO_DEFS[name].get("asset_tilt", {}),
        ))
    return out


def blend_report(
    base_return: float, base_vol: float,
    probabilities: Optional[Dict[str, float]] = None,
) -> ScenarioReport:
    """生成概率加权情景报告（纯逻辑）。"""
    probs = dict(probabilities or DEFAULT_PROBABILITIES)
    # 归一化
    tot = sum(probs.values())
    if tot > 0:
        probs = {k: v / tot for k, v in probs.items()}

    outcomes = weighted_outcomes(base_return, base_vol, probs)
    if not outcomes:
        return ScenarioReport(base_return=base_return, base_vol=base_vol, note="无有效情景")

    wr = sum(o.expected_return * o.probability for o in outcomes)
    # 加权波动（简化：线性加权；严格应按混合分布，这里给量级）
    wv = sum(o.expected_vol * o.probability for o in outcomes)
    returns = [o.expected_return for o in outcomes]
    tail = min(returns)
    best = max(returns)
    upside = sum(o.probability for o in outcomes if o.expected_return > 0)

    return ScenarioReport(
        base_return=round(base_return, 4),
        base_vol=round(base_vol, 4),
        probabilities=probs,
        outcomes=outcomes,
        weighted_return=round(wr, 4),
        weighted_vol=round(wv, 4),
        tail_risk=round(tail, 4),
        best_case=round(best, 4),
        upside_probability=round(upside, 3),
        note="概率加权多情景",
    )


def sample_scenario_path(
    base_return: float, base_vol: float, scenario_name: str,
    horizon_days: int = 63, sims: int = 1000,
) -> List[float]:
    """对单情景做跳跃扩散蒙特卡洛，返回各路径期末收益（小数）。

    纯 stdlib；GBM + 泊松跳跃。供尾部风险细化使用。
    """
    s = SCENARIO_DEFS.get(scenario_name, {})
    mu = (base_return + s.get("drift_delta", 0)) / 252.0
    sig = max(1e-6, base_vol * s.get("vol_mult", 1.0)) / math.sqrt(252.0)
    lam = s.get("jump_lambda", 0.0) / 252.0
    jm = s.get("jump_mean", 0.0)
    terminals = []
    for _ in range(sims):
        logp = 0.0
        for _ in range(horizon_days):
            z = random.gauss(0, 1)
            ret = mu - 0.5 * sig * sig + sig * z
            # 跳跃
            if lam > 0 and random.random() < lam:
                ret += jm + random.gauss(0, abs(jm) * 0.5 + 0.01)
            logp += ret
        terminals.append(math.exp(logp) - 1.0)
    return terminals


# ════════════════════════════════════════════════════════════
# 引擎封装
# ════════════════════════════════════════════════════════════

class MacroScenarioEngine:
    """宏观情景引擎。"""

    @staticmethod
    def list_scenarios() -> List[str]:
        return list(SCENARIO_DEFS.keys())

    def analyze(
        self,
        base_return: float = 0.08,
        base_vol: float = 0.20,
        probabilities: Optional[Dict[str, float]] = None,
    ) -> ScenarioReport:
        """生成多情景概率加权报告。

        Args:
            base_return: 基准年化预期收益（小数）
            base_vol: 基准年化波动
            probabilities: 各情景概率（不传用 DEFAULT_PROBABILITIES）
        """
        return blend_report(base_return, base_vol, probabilities)

    def tail_var(
        self, base_return: float, base_vol: float,
        scenario_name: str = "硬着陆", horizon_days: int = 63,
        sims: int = 1000, quantile: float = 0.05,
    ) -> float:
        """某情景下的 VaR（分位数期末收益，负值）。"""
        paths = sample_scenario_path(
            base_return, base_vol, scenario_name, horizon_days, sims,
        )
        if not paths:
            return 0.0
        paths.sort()
        idx = max(0, int(len(paths) * quantile) - 1)
        return paths[idx]

    @staticmethod
    def format(rep: ScenarioReport) -> str:
        lines = [
            f"宏观情景分析 | 基准收益{rep.base_return:+.1%} 波动{rep.base_vol:.1%}",
            f"  概率加权: {rep.weighted_return:+.1%} | 尾部(最差情景){rep.tail_risk:+.1%} "
            f"| 最优{rep.best_case:+.1%} | 正收益概率{rep.upside_probability:.0%}",
            f"  {'情景':<10}{'概率':>6}{'预期收益':>10}{'波动':>8}",
        ]
        for o in rep.outcomes:
            lines.append(f"  {o.name:<10}{o.probability:>5.0%}{o.expected_return:>+9.1%}{o.expected_vol:>7.1%}")
        return "\n".join(lines)


def analyze_scenarios(
    base_return: float = 0.08, base_vol: float = 0.20,
) -> ScenarioReport:
    """便捷函数：多情景分析。"""
    return MacroScenarioEngine().analyze(base_return, base_vol)
