#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""基金推荐引擎 (v4.0.0 新增)

基于 pkg/fund_analyzer 评分+风格漂移检测+超额收益归因，
对国内主流基金池进行短/中/长期推荐，每项附带评分依据。

基金池覆盖股票型、混合型、指数型主流标的。
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

SKILL_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SKILL_DIR / "pkg"))
from fund_analyzer import score_fund, score_fund_v2, score_fund_v3  # noqa: E402

FUND_POOL = {
    "股票型": ["110022", "000083", "519069", "001410", "001717",
               "050001", "160626", "512800"],
    "混合型": ["163406", "519736", "001875", "001112", "005827",
               "162102", "000390", "001590"],
    "指数型": ["510050", "510300", "510500", "159915", "588000",
               "159949", "512880", "513050"],
}

CATEGORY_NAMES = {"股票型": "股票型基金", "混合型": "混合型基金", "指数型": "指数/ETF"}


@dataclass
class FundRecommendation:
    code: str
    name: str
    category: str
    score: int          # 0~100
    grade: str          # A/B/C/D
    style: str
    alpha: Optional[float]     # 超额收益
    sharpe: Optional[float]    # 夏普比率
    reasons: List[str]


class FundRecommender:
    """基金推荐器"""

    def recommend(
        self, category: str = "all", top_n: int = 8,
        scoring_version: str = "v2"
    ) -> List[FundRecommendation]:
        """
        基金推荐（v5.0 升级：支持 v2/v3 评分版本）。

        Args:
            category: all/股票型/混合型/指数型
            top_n: 返回数量
            scoring_version: v1/v2/v3 评分版本（默认 v2）
        """
        cats = list(FUND_POOL.keys()) if category == "all" else [category]
        recs = []
        for cat in cats:
            for code in FUND_POOL.get(cat, [])[:10]:
                try:
                    # v5.0: 根据 scoring_version 选择评分函数
                    if scoring_version == "v3":
                        r = score_fund_v3(code)
                    elif scoring_version == "v2":
                        r = score_fund_v2(code)
                    else:
                        r = score_fund(code)
                    recs.append(FundRecommendation(
                        code=code, name=r.get("name", code),
                        category=cat, score=r.get("score", 50),
                        grade=r.get("grade", "C"),
                        style=r.get("style", {}).get("current_style", ""),
                        alpha=r.get("attribution", {}).get("alpha"),
                        sharpe=r.get("attribution", {}).get("sharpe_ratio"),
                        reasons=r.get("details", []),
                    ))
                except Exception:
                    pass
        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:top_n]

    def recommend_by_horizon(
        self, top_n: int = 5,
        scoring_version: str = "v2"
    ) -> Dict[str, List[FundRecommendation]]:
        """短/中/长期分别推荐（v5.0: 支持 v2/v3 评分版本）
        短期: 偏指数型(流动性好)
        中期: 偏混合型(风格均衡)
        长期: 偏股票型(超额收益潜力)
        """
        all_recs = self.recommend("all", top_n=20, scoring_version=scoring_version)
        result = {}
        # 短期：取指数型 Top + 高分混合
        idx = [r for r in all_recs if r.category == "指数型"][:top_n]
        mix = [r for r in all_recs if r.category == "混合型"][:2]
        result["short"] = (idx + mix)[:top_n]
        # 中期：混合型为主
        result["mid"] = [r for r in all_recs if r.category in ("混合型", "股票型")][:top_n]
        # 长期：股票型为主
        result["long"] = [r for r in all_recs if r.category in ("股票型", "混合型")][:top_n]
        return result


def get_fund_recommendations(category: str = "all", top_n: int = 8) -> List[Dict]:
    recs = FundRecommender().recommend(category, top_n)
    return [
        {
            "code": r.code, "name": r.name, "category": r.category,
            "score": r.score, "grade": r.grade, "style": r.style,
            "alpha": f"{r.alpha:+.1f}%" if r.alpha else "N/A",
            "sharpe": r.sharpe,
            "reasons": r.reasons,
        }
        for r in recs
    ]


def format_fund_recommendations(recs: List[FundRecommendation]) -> str:
    lines = [f"💰 基金推荐  |  {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "=" * 65]
    for i, r in enumerate(recs, 1):
        alpha_str = f"{r.alpha:+.1f}%" if r.alpha else "N/A"
        shrp_str = f"{r.sharpe:.2f}" if r.sharpe else "N/A"
        lines.append(
            f"  #{i} [{r.code}] {r.name}  {r.grade}({r.score})  "
            f"α={alpha_str}  Sharpe={shrp_str}  {r.style}"
        )
        for re in r.reasons[:2]:
            lines.append(f"       → {re}")
        lines.append("")
    lines.append("=" * 65)
    return "\n".join(lines)
