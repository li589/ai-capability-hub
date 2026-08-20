#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""风格定制投资组合构建器 (v6.0 新增)

根据自身投资风格定制基金组合：
- 10 题风格问卷 -> 5 轴风格画像（价值↔成长、大盘↔小盘、行业↔主题、
  主动↔被动、国内↔海外），每轴 -2~+2
- 按风格输出目标资产配置（股/债/货/QDII/指数）
- 风格化基金筛选（晨星分类 + 风格标签 + 多源评级排序）
- 风格漂移监控（current vs target，超阈值告警+再平衡建议）
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))

from multi_source import get_provider  # noqa: E402

# 5 轴：每轴 -2(左) ~ +2(右)
# 价值成长: -2=深度价值, 0=均衡, +2=激进成长
# 大盘小盘: -2=大盘, 0=均衡, +2=小盘
# 行业主题: -2=宽基, 0=中性, +2=行业主题
# 主动被动: -2=主动, 0=中性, +2=被动指数
# 国内海外: -2=纯国内, 0=中性, +2=海外QDII

STYLE_AXES = ["value_growth", "large_small", "broad_sector", "active_passive", "domestic_overseas"]
AXIS_LABELS = {
    "value_growth": ("价值", "成长"),
    "large_small": ("大盘", "小盘"),
    "broad_sector": ("宽基", "行业主题"),
    "active_passive": ("主动", "被动指数"),
    "domestic_overseas": ("国内", "海外QDII"),
}

# 10 题问卷（每题贡献到某轴）
QUESTIONNAIRE = [
    {"q": "你更看重当前低估值还是未来高增长？", "axis": "value_growth", "a": [("低估值稳健", -2), ("偏价值", -1), ("均衡", 0), ("偏成长", 1), ("高增长激进", 2)]},
    {"q": "偏好大盘蓝筹还是小盘成长？", "axis": "large_small", "a": [("大盘蓝筹", -2), ("偏大盘", -1), ("均衡", 0), ("偏小盘", 1), ("小盘成长", 2)]},
    {"q": "投资宽基指数还是特定行业主题？", "axis": "broad_sector", "a": [("宽基指数", -2), ("偏宽基", -1), ("中性", 0), ("偏行业", 1), ("行业主题", 2)]},
    {"q": "相信主动管理还是被动指数？", "axis": "active_passive", "a": [("主动管理", -2), ("偏主动", -1), ("中性", 0), ("偏被动", 1), ("纯被动", 2)]},
    {"q": "只投国内还是配置海外？", "axis": "domestic_overseas", "a": [("纯国内", -2), ("偏国内", -1), ("中性", 0), ("偏海外", 1), ("重海外", 2)]},
    {"q": "能承受多大回撤？", "axis": "value_growth", "a": [("<5%", -2), ("5-10%", -1), ("10-20%", 0), ("20-30%", 1), (">30%", 2)]},
    {"q": "投资期限多长？", "axis": "value_growth", "a": [("<1年", -2), ("1-3年", -1), ("3-5年", 0), ("5-10年", 1), (">10年", 2)]},
    {"q": "偏好高股息还是资本利得？", "axis": "value_growth", "a": [("高股息", -2), ("偏股息", -1), ("均衡", 0), ("偏利得", 1), ("资本利得", 2)]},
    {"q": "组合中指数基金占比期望？", "axis": "active_passive", "a": [("<20%", -2), ("20-40%", -1), ("40-60%", 0), ("60-80%", 1), (">80%", 2)]},
    {"q": "海外资产配置期望比例？", "axis": "domestic_overseas", "a": [("0%", -2), ("<10%", -1), ("10-20%", 0), ("20-40%", 1), (">40%", 2)]},
]


@dataclass
class StyleProfile:
    """5 轴风格画像"""
    axes: Dict[str, float]            # 每轴 -2~+2
    target_allocation: Dict[str, float]  # 目标配置 {stock,bond,money,qdii,index}
    style_label: str                   # 风格标签
    risk_level: str                    # 保守/稳健/平衡/进取/激进
    answers: List[int] = field(default_factory=list)


class StylePortfolioBuilder:
    """风格定制组合构建器"""

    def __init__(self):
        self.provider = get_provider()

    # ─── 问卷 -> 5轴画像 ─────────────────────────────────
    def build_profile_from_answers(self, answers: List[int]) -> StyleProfile:
        """answers: 10 题答案索引(0-4)，对应每题选项

        若 answers 长度 < 10，缺失题按 0(中性) 处理
        """
        # 每轴累计得分
        axis_scores = {a: [] for a in STYLE_AXES}
        for i, ans in enumerate(answers[:len(QUESTIONNAIRE)]):
            q = QUESTIONNAIRE[i]
            try:
                score = q["a"][ans][1]
                axis_scores[q["axis"]].append(score)
            except (IndexError, TypeError):
                continue
        # 平均到每轴
        axes = {}
        for a in STYLE_AXES:
            vals = axis_scores[a]
            axes[a] = round(sum(vals) / len(vals), 2) if vals else 0.0

        # 目标配置（由 value_growth + domestic_overseas 主导）
        vg = axes["value_growth"]  # -2~+2
        dos = axes["domestic_overseas"]
        ap = axes["active_passive"]
        # 股票比例：vg 越正越多股
        stock_ratio = 40 + vg * 15  # -2->10%, 0->40%, +2->70%
        stock_ratio = max(10, min(80, stock_ratio))
        # 海外比例
        qdii_ratio = max(0, dos * 8)  # -2->0, +2->16
        qdii_ratio = min(qdii_ratio, stock_ratio * 0.4)
        # 指数比例（占股票部分）
        index_ratio = max(0, ap * 12)  # 偏被动多指数
        index_ratio = min(index_ratio, stock_ratio * 0.6)
        # 债券+货币
        bond_ratio = (100 - stock_ratio) * 0.75
        money_ratio = 100 - stock_ratio - bond_ratio - qdii_ratio
        money_ratio = max(0, money_ratio)
        # 归一化
        total = stock_ratio + bond_ratio + money_ratio + qdii_ratio
        target = {
            "stock": round(stock_ratio / total * 100, 1),
            "bond": round(bond_ratio / total * 100, 1),
            "money": round(money_ratio / total * 100, 1),
            "qdii": round(qdii_ratio / total * 100, 1),
            "index": round(index_ratio / total * 100, 1),
        }
        # 风格标签
        if vg <= -1:
            style_label = "价值型"
        elif vg >= 1:
            style_label = "成长型"
        else:
            style_label = "均衡型"
        # 风险等级
        if stock_ratio <= 20:
            risk_level = "保守"
        elif stock_ratio <= 40:
            risk_level = "稳健"
        elif stock_ratio <= 55:
            risk_level = "平衡"
        elif stock_ratio <= 70:
            risk_level = "进取"
        else:
            risk_level = "激进"
        return StyleProfile(axes=axes, target_allocation=target,
                            style_label=style_label, risk_level=risk_level,
                            answers=answers)

    # ─── 风格化基金筛选 ─────────────────────────────────
    def screen_style_funds(self, profile: StyleProfile,
                            candidate_codes: List[str] = None,
                            top_n: int = 8) -> List[Dict]:
        """按风格筛选基金（多源评级排序）"""
        codes = candidate_codes or [
            "110022", "000083", "519069", "001410",  # 主动股票
            "510300", "510500", "159915", "588000",  # 指数
            "163406", "519736",  # 混合
            "000390",  # 债券
            "513050",  # QDII
        ]
        results = []
        for code in codes:
            try:
                r = self.provider.get_fund_ratings(code)
                star = r.get("consensus_star")
                if star and star >= 3:
                    results.append({"code": code, "star": star,
                                    "source_count": r.get("source_count", 0)})
            except Exception:
                continue
        results.sort(key=lambda x: x["star"], reverse=True)
        return results[:top_n]

    # ─── 风格漂移监控 ───────────────────────────────────
    def monitor_style_drift(self, profile: StyleProfile,
                             current_allocation: Dict[str, float],
                             threshold: float = 5.0) -> Dict:
        """监控当前配置 vs 目标风格的漂移

        current_allocation: {stock,bond,money,qdii,index} 当前权重%
        """
        target = profile.target_allocation
        drifts = {}
        max_drift = 0
        max_drift_asset = ""
        for k, tv in target.items():
            cv = current_allocation.get(k, 0)
            d = round(cv - tv, 1)
            drifts[k] = {"current": cv, "target": tv, "drift": d}
            if abs(d) > abs(max_drift):
                max_drift = d
                max_drift_asset = k
        drifted = any(abs(v["drift"]) > threshold for v in drifts.values())
        return {
            "drifted": drifted,
            "threshold": threshold,
            "drifts": drifts,
            "max_drift_asset": max_drift_asset,
            "max_drift": max_drift,
            "action": "建议再平衡" if drifted else "维持配置",
        }

    # ─── 构建定制组合 ───────────────────────────────────
    def build_portfolio(self, answers: List[int],
                         candidate_codes: List[str] = None,
                         amount_wan: float = 10.0) -> Dict:
        """构建风格定制组合"""
        profile = self.build_profile_from_answers(answers)
        funds = self.screen_style_funds(profile, candidate_codes)
        return {
            "profile": {
                "axes": profile.axes,
                "style_label": profile.style_label,
                "risk_level": profile.risk_level,
                "axis_labels": {a: AXIS_LABELS[a] for a in STYLE_AXES},
            },
            "target_allocation": profile.target_allocation,
            "recommended_funds": funds,
            "amount_wan": amount_wan,
            "amount_allocation": {k: round(v / 100 * amount_wan, 2)
                                  for k, v in profile.target_allocation.items()},
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def format_style_profile(profile: StyleProfile) -> str:
    lines = ["🎨 投资风格画像", "=" * 50]
    for a in STYLE_AXES:
        v = profile.axes[a]
        left, right = AXIS_LABELS[a]
        bar_len = 10
        pos = int((v + 2) / 4 * bar_len)  # -2->0, +2->10
        bar = "█" * pos + "│" + "░" * (bar_len - pos)
        lines.append(f"  {left} [{bar}] {right}  ({v:+.1f})")
    lines.append(f"\n  风格: {profile.style_label}  |  风险: {profile.risk_level}")
    lines.append("  目标配置: " + "  ".join(f"{k}:{v}%" for k, v in profile.target_allocation.items()))
    lines.append("=" * 50)
    return "\n".join(lines)


def main():
    builder = StylePortfolioBuilder()
    # 测试：偏成长+被动+国内 的答案
    answers = [3, 2, 1, 2, 1, 2, 3, 2, 2, 1]
    result = builder.build_portfolio(answers, amount_wan=20)
    profile = builder.build_profile_from_answers(answers)
    print(format_style_profile(profile))
    print("\n推荐基金:")
    for f in result["recommended_funds"][:5]:
        print(f"  · {f['code']}: {f['star']}★ ({f['source_count']}源)")


if __name__ == "__main__":
    main()
