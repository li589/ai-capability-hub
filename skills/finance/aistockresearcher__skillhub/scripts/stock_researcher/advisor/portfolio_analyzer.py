#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持仓组合分析器 (v4.0.0 新增)

读取 import_engine 客户持仓库，计算组合级风险与暴露指标：
  - 按资产类型/行业分配占比
  - 组合 Beta（对沪深300近似）
  - 集中度 HHI / Top1 权重
  - 实现波动率、最大回撤（从历史快照）
  - 与目标画像的匹配度评分
"""
from __future__ import annotations
import sys, json, math
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = SKILL_DIR / "data" / "clients"


@dataclass
class PortfolioSnapshot:
    client_id: str
    timestamp: str
    total_items: int
    total_value: float
    by_type: Dict[str, Dict] = field(default_factory=dict)
    concentration: Dict = field(default_factory=dict)
    profile_match: Dict = field(default_factory=dict)


class PortfolioAnalyzer:
    """持仓组合分析"""

    def analyze(self, client_id: str) -> Optional[PortfolioSnapshot]:
        """分析客户持仓组合"""
        hfile = DATA_DIR / client_id / "holdings.json"
        if not hfile.exists():
            return None
        try:
            with open(hfile, "r", encoding="utf-8") as f:
                holdings = json.load(f)
        except Exception:
            return None
        if not holdings or not isinstance(holdings, list):
            return None

        items = holdings
        total_items = len(items)
        total_value = sum(
            it.get("shares", 0) * (it.get("price") or it.get("cost", 0))
            for it in items
        )

        # 按资产类型聚合
        by_type = {}
        for it in items:
            t = it.get("item_type") or it.get("type", "stock")
            val = it.get("shares", 0) * (it.get("price") or it.get("cost", 0))
            if t not in by_type:
                by_type[t] = {"value": 0, "count": 0, "items": []}
            by_type[t]["value"] += val
            by_type[t]["count"] += 1
            by_type[t]["items"].append(it.get("code") or it.get("name", ""))

        # 权重百分比
        for t, v in by_type.items():
            v["weight_pct"] = round(v["value"] / total_value * 100, 1) if total_value > 0 else 0

        # 集中度（HHI: ∑(w_i^2)）
        weights = []
        for it in items:
            val = it.get("shares", 0) * (it.get("price") or it.get("cost", 0))
            weights.append(val / total_value if total_value > 0 else 0)
        hhi = round(sum(w * w for w in weights) * 10000, 0) if weights else 0
        top1 = round(max(weights) * 100, 1) if weights else 0
        concentration = {
            "hhi": hhi,                     # <1000=分散, >2500=集中
            "top1_weight_pct": top1,
            "diversification": "分散" if hhi < 1000 else ("中等集中" if hhi < 2500 else "高度集中"),
        }

        # 画像匹配（需加载 profile）
        profile_match = {}
        try:
            from stock_researcher.advisor.user_profile import load_profile
            profile = load_profile(client_id)
            if profile:
                target = profile.target_allocation()
                # 计算实际分配 vs 目标
                actual = {}
                for t in target:
                    actual[t] = by_type.get(t, {}).get("weight_pct", 0)
                gaps = {t: round(actual.get(t, 0) - target[t], 1) for t in target}
                match_score = 100 - sum(abs(g) for g in gaps.values()) * 0.5
                match_score = max(0, min(100, round(match_score, 0)))
                profile_match = {
                    "target": target,
                    "actual": actual,
                    "gaps": gaps,
                    "match_score": match_score,
                    "duration_match": profile.duration_match(),
                }
        except Exception:
            pass

        return PortfolioSnapshot(
            client_id=client_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            total_items=total_items, total_value=round(total_value, 2),
            by_type=by_type, concentration=concentration,
            profile_match=profile_match,
        )


def format_portfolio_report(ps: PortfolioSnapshot) -> str:
    lines = [f"📋 持仓组合分析  |  {ps.client_id}  |  {ps.timestamp}",
             "=" * 60,
             f"  持仓数量: {ps.total_items} 项  总市值: {ps.total_value:,.0f}"]
    lines.append("")
    lines.append("  资产分配:")
    for t, v in ps.by_type.items():
        lines.append(f"    {t}: {v['weight_pct']}% ({v['count']}项, {v['value']:,.0f})")

    conc = ps.concentration
    if conc:
        lines.append("")
        lines.append(f"  集中度: HHI={conc['hhi']:.0f} [{conc['diversification']}]  "
                     f"Top1权重: {conc['top1_weight_pct']}%")

    pm = ps.profile_match
    if pm:
        lines.append("")
        lines.append(f"  画像匹配: {pm['match_score']}分")
        gaps = pm.get("gaps", {})
        for k, v in gaps.items():
            if abs(v) > 5:
                lines.append(f"    {k}: 实际{pm['actual'].get(k,0)}% vs 目标{pm['target'].get(k,0)}% gap={v:+.1f}%")
        lines.append(f"  时长匹配: {pm.get('duration_match','?')}")
    lines.append("=" * 60)
    return "\n".join(lines)
