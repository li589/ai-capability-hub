#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
护城河分析（v5.0 新增）⭐

基于价值投资经典理论，从 7 个维度评估企业护城河：
1. 毛利率稳定性（25%）- 高且稳定的毛利率是定价权的直接证据
2. ROIC 一致性（25%）- 高且稳定的 ROIC 是优质业务的标志
3. 定价权代理（15%）- 毛利率 vs 行业中位数
4. 资产轻重趋势（10%）- 资产变轻通常意味着更轻的商业模式
5. 研发/销售费用比（10%）- 持续的研发投入维持技术护城河
6. 市场份额代理（10%）- 营收在行业内的分位
7. Porter 五力简化（5%）- 来自 industry_analysis

输出: 0-100 评分 + 护城河类型（无/窄/宽）+ 证据链
数据不足时降级（仅用可用维度归一化），不伪装默认分。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..data.financial_statements import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_financial_indicators,
    filter_recent_n_years,
)


@dataclass
class MoatResult:
    """护城河分析结果"""
    code: str
    moat_score: float = 0.0           # 0-100
    moat_type: str = "无显著护城河"   # 宽护城河 / 窄护城河 / 无显著护城河
    sub_scores: Dict[str, float] = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    insufficient_data: bool = False


def _safe(val, default=0.0) -> float:
    try:
        f = float(val) if val is not None else default
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


class MoatAnalyzer:
    """
    护城河分析器。

    用法:
        analyzer = MoatAnalyzer()
        result = analyzer.analyze("600519")
    """

    # 7 维权重
    WEIGHTS = {
        "gross_margin_stability": 0.25,
        "roic_consistency": 0.25,
        "pricing_power": 0.15,
        "asset_lightness": 0.10,
        "rd_intensity": 0.10,
        "market_share": 0.10,
        "porter_5_forces": 0.05,
    }

    def __init__(self, years: int = 5):
        self.years = years

    # ─────────────────────────────────────────────
    # 1. 毛利率稳定性
    # ─────────────────────────────────────────────
    def _gross_margin_stability(self, income: List[dict]) -> Optional[Dict]:
        """
        毛利率稳定性：均值 >40% 且 std <5pct 为高分；趋势上升加分。
        """
        margins = []
        for row in income[:min(self.years, len(income))]:
            rev = _safe(row.get("TOTAL_OPERATE_INCOME") or row.get("OPERATE_INCOME"))
            cost = _safe(row.get("OPERATE_COST"))
            if rev > 0:
                margins.append((rev - cost) / rev * 100)
        if len(margins) < 3:
            return None
        mean_m = sum(margins) / len(margins)
        std_m = (sum((m - mean_m) ** 2 for m in margins) / len(margins)) ** 0.5
        # 均值评分：>40% 满分，<10% 低分
        mean_score = max(0, min(100, (mean_m - 10) / 30 * 100))
        # 稳定性评分：std <5pct 满分，>15pct 低分
        std_score = max(0, 100 - std_m * 6)
        # 趋势：后 3 年均值 - 前 3 年均值
        if len(margins) >= 6:
            recent = sum(margins[:3]) / 3
            older = sum(margins[3:6]) / 3
            trend_bonus = max(-10, min(10, (recent - older) * 2))
        else:
            trend_bonus = 0
        score = max(0, min(100, (mean_score * 0.6 + std_score * 0.4) + trend_bonus))
        return {
            "score": score,
            "mean": round(mean_m, 2),
            "std": round(std_m, 2),
            "trend": "上升" if trend_bonus > 0 else "下降" if trend_bonus < 0 else "平稳",
        }

    # ─────────────────────────────────────────────
    # 2. ROIC 一致性
    # ─────────────────────────────────────────────
    def _roic_consistency(self, income: List[dict], balance: List[dict]) -> Optional[Dict]:
        """
        ROIC = NOPLAT / 投入资本
        NOPLAT = 营业利润 × (1 - 税率)
        投入资本 = 股东权益 + 有息负债
        """
        if len(income) < 3 or len(balance) < 3:
            return None
        roics = []
        for i in range(min(len(income), len(balance), self.years)):
            op = _safe(income[i].get("OPERATE_PROFIT"))
            tax = _safe(income[i].get("INCOME_TAX") or income[i].get("INCOME_TAX_EXPENSE"))
            pretax = op + _safe(income[i].get("FINANCE_EXPENSE"))
            tax_rate = tax / max(pretax, 1) if pretax > 0 else 0.25
            noplat = op * (1 - tax_rate)
            equity = _safe(balance[i].get("TOTAL_PARENT_EQUITY"))
            debt = (_safe(balance[i].get("SHORT_LOAN")) + _safe(balance[i].get("LONG_LOAN"))
                    + _safe(balance[i].get("BOND_PAYABLE")))
            invested = equity + debt
            if invested > 0:
                roics.append(noplat / invested * 100)
        if len(roics) < 3:
            return None
        mean_r = sum(roics) / len(roics)
        std_r = (sum((r - mean_r) ** 2 for r in roics) / len(roics)) ** 0.5
        # 均值 >15% 满分；<5% 低分
        mean_score = max(0, min(100, (mean_r - 5) / 10 * 100))
        # 稳定性 std <3pct 满分
        std_score = max(0, 100 - std_r * 10)
        score = max(0, min(100, mean_score * 0.6 + std_score * 0.4))
        return {
            "score": score,
            "mean": round(mean_r, 2),
            "std": round(std_r, 2),
        }

    # ─────────────────────────────────────────────
    # 3. 定价权代理（毛利率 vs 行业中位数）
    # ─────────────────────────────────────────────
    def _pricing_power(self, income: List[dict],
                       industry_median_gm: float = 0.0) -> Optional[Dict]:
        """毛利率 vs 行业中位数（>5pct 溢价 -> 高分）"""
        if not income:
            return None
        rev = _safe(income[0].get("TOTAL_OPERATE_INCOME"))
        cost = _safe(income[0].get("OPERATE_COST"))
        if rev <= 0:
            return None
        gm = (rev - cost) / rev * 100
        # 与行业中位数对比
        if industry_median_gm <= 0:
            # 无行业数据时，用绝对毛利率评分
            score = max(0, min(100, (gm - 10) / 30 * 100))
            return {"score": score, "company_gm": round(gm, 2), "industry_gm": None}
        premium = gm - industry_median_gm
        # 溢价 >10pct 满分；<-10pct 低分
        score = max(0, min(100, 50 + premium * 4))
        return {
            "score": score,
            "company_gm": round(gm, 2),
            "industry_gm": round(industry_median_gm, 2),
            "premium": round(premium, 2),
        }

    # ─────────────────────────────────────────────
    # 4. 资产轻重趋势
    # ─────────────────────────────────────────────
    def _asset_lightness(self, income: List[dict], balance: List[dict]) -> Optional[Dict]:
        """固定资产 / 营收比值 5Y 趋势下降 -> 资产变轻"""
        if len(income) < 3 or len(balance) < 3:
            return None
        ratios = []
        for i in range(min(len(income), len(balance), self.years)):
            fixed = _safe(balance[i].get("FIXED_ASSET"))
            rev = _safe(income[i].get("TOTAL_OPERATE_INCOME"))
            if rev > 0:
                ratios.append(fixed / rev)
        if len(ratios) < 3:
            return None
        # 趋势：用线性回归斜率近似
        n = len(ratios)
        mean_x = (n - 1) / 2
        mean_y = sum(ratios) / n
        num = sum((i - mean_x) * (ratios[i] - mean_y) for i in range(n))
        den = sum((i - mean_x) ** 2 for i in range(n))
        slope = num / den if den > 0 else 0
        # 斜率 <0 表示资产变轻（高分）；>0 表示变重（低分）
        # 同时考虑绝对水平：比率 <0.3 为轻资产（加分）
        recent_ratio = ratios[0]  # 最新（ratios 按报告期降序，最新在前）
        level_score = max(0, 100 - recent_ratio * 100) if recent_ratio < 1 else 0
        trend_score = max(0, min(50, -slope * 200 + 25))
        score = max(0, min(100, level_score * 0.7 + trend_score * 0.3))
        return {
            "score": score,
            "recent_ratio": round(recent_ratio, 3),
            "trend": "变轻" if slope < 0 else "变重" if slope > 0 else "稳定",
        }

    # ─────────────────────────────────────────────
    # 5. 研发/销售费用比
    # ─────────────────────────────────────────────
    def _rd_intensity(self, income: List[dict]) -> Optional[Dict]:
        """研发强度趋势 + 与行业对比"""
        if len(income) < 3:
            return None
        rds = []
        for row in income[:min(self.years, len(income))]:
            rd = _safe(row.get("RESEARCH_EXPENSE"))
            rev = _safe(row.get("TOTAL_OPERATE_INCOME"))
            if rev > 0:
                rds.append(rd / rev * 100)
        if len(rds) < 3:
            return None
        mean_rd = sum(rds) / len(rds)
        # 研发强度 >5% 为高分（科技/医药行业），<1% 为低分
        score = max(0, min(100, mean_rd / 5 * 100))
        # 趋势
        recent = sum(rds[:2]) / 2
        older = sum(rds[-2:]) / 2
        trend = "上升" if recent > older * 1.1 else "下降" if recent < older * 0.9 else "稳定"
        return {"score": score, "mean_rd_pct": round(mean_rd, 2), "trend": trend}

    # ─────────────────────────────────────────────
    # 6. 市场份额代理（行业营收排名）
    # ─────────────────────────────────────────────
    def _market_share(self, income: List[dict],
                      industry_revenue_rank: int = 0,
                      industry_total: int = 0) -> Optional[Dict]:
        """营收在申万同行业的分位排名"""
        if not income:
            return None
        rev = _safe(income[0].get("TOTAL_OPERATE_INCOME"))
        if rev <= 0:
            return None
        # 无行业排名数据时，用绝对规模评分
        if industry_revenue_rank <= 0 or industry_total <= 0:
            # 100 亿营收为满分；1 亿为 30 分
            score = max(0, min(100, 30 + (rev / 1e10 - 1) * 7))
            return {"score": score, "revenue": round(rev / 1e8, 2), "rank": None}
        # 行业排名前 10% 为满分；后 50% 为低分
        percentile = 1 - (industry_revenue_rank / industry_total)
        score = max(0, min(100, percentile * 100))
        return {
            "score": score,
            "revenue": round(rev / 1e8, 2),
            "rank": industry_revenue_rank,
            "percentile": round(percentile * 100, 1),
        }

    # ─────────────────────────────────────────────
    # 7. Porter 五力简化（外部传入）
    # ─────────────────────────────────────────────
    def _porter_score(self, porter_5_forces: Optional[Dict]) -> Optional[Dict]:
        if not porter_5_forces:
            return None
        # 五力平均分（每力 0-5）
        forces = ["supplier_power", "buyer_power", "new_entrant_threat",
                  "substitute_threat", "competitive_intensity"]
        scores = []
        for f in forces:
            v = porter_5_forces.get(f)
            if v is not None:
                # 注意：供应商/客户/新进入者/替代品/竞争强度对在位企业而言越低越好
                # 所以评分 = (5 - score) / 5 * 100
                scores.append((5 - v) / 5 * 100)
        if not scores:
            return None
        avg = sum(scores) / len(scores)
        return {"score": avg, "forces_count": len(scores)}

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────
    def analyze(self, code: str,
                financials: Optional[dict] = None,
                industry_median_gm: float = 0.0,
                industry_revenue_rank: int = 0,
                industry_total: int = 0,
                porter_5_forces: Optional[Dict] = None) -> MoatResult:
        """
        执行护城河分析。

        Args:
            code: 股票代码
            financials: 预取的财务数据；None 时自动获取
            industry_median_gm: 同申万行业毛利率中位数（百分比，如 30.5）
            industry_revenue_rank: 公司在行业内的营收排名（1=最大）
            industry_total: 行业内公司总数
            porter_5_forces: 来自 industry_analysis 的五力评分
        """
        if financials is None:
            financials = {
                "income": fetch_income_statement(code, self.years),
                "balance": fetch_balance_sheet(code, self.years),
                "indicators": fetch_financial_indicators(code, self.years),
            }
        income = filter_recent_n_years(financials.get("income", []), self.years)
        balance = filter_recent_n_years(financials.get("balance", []), self.years)

        if not income or not balance:
            return MoatResult(code=code, insufficient_data=True,
                              evidence=["利润表或资产负债表数据不足"])

        # 7 维评分
        subs: Dict[str, Optional[Dict]] = {
            "gross_margin_stability": self._gross_margin_stability(income),
            "roic_consistency": self._roic_consistency(income, balance),
            "pricing_power": self._pricing_power(income, industry_median_gm),
            "asset_lightness": self._asset_lightness(income, balance),
            "rd_intensity": self._rd_intensity(income),
            "market_share": self._market_share(income, industry_revenue_rank, industry_total),
            "porter_5_forces": self._porter_score(porter_5_forces),
        }

        # 加权求和（仅用可用维度归一化）
        available_scores: Dict[str, float] = {}
        for k, v in subs.items():
            if v is not None and "score" in v:
                available_scores[k] = v["score"]

        if not available_scores:
            return MoatResult(code=code, insufficient_data=True,
                              evidence=["7 个维度均无数据"])

        weight_sum = sum(self.WEIGHTS[k] for k in available_scores)
        score = sum(self.WEIGHTS[k] * available_scores[k] for k in available_scores) / max(weight_sum, 1e-9)

        # 护城河类型
        moat_type = "宽护城河" if score >= 75 else "窄护城河" if score >= 55 else "无显著护城河"

        # 证据链
        evidence: List[str] = []
        if subs["gross_margin_stability"]:
            d = subs["gross_margin_stability"]
            evidence.append(f"毛利率 5Y 均值 {d['mean']}%（std {d['std']}pct，趋势{d['trend']}）")
        if subs["roic_consistency"]:
            d = subs["roic_consistency"]
            evidence.append(f"ROIC 5Y 均值 {d['mean']}%（std {d['std']}pct）")
        if subs["pricing_power"]:
            d = subs["pricing_power"]
            if d.get("industry_gm") is not None:
                evidence.append(f"毛利率 {d['company_gm']}% vs 行业 {d['industry_gm']}%（溢价 {d['premium']}pct）")
            else:
                evidence.append(f"毛利率 {d['company_gm']}%（无行业对比数据）")
        if subs["asset_lightness"]:
            d = subs["asset_lightness"]
            evidence.append(f"固定资产/营收 {d['recent_ratio']}（趋势{d['trend']}）")
        if subs["rd_intensity"]:
            d = subs["rd_intensity"]
            evidence.append(f"研发强度 {d['mean_rd_pct']}%（趋势{d['trend']}）")
        if subs["market_share"]:
            d = subs["market_share"]
            if d.get("rank"):
                evidence.append(f"行业营收排名 #{d['rank']}/{industry_total}（分位 {d['percentile']}%）")
            else:
                evidence.append(f"营收 {d['revenue']} 亿")

        return MoatResult(
            code=code,
            moat_score=round(score, 1),
            moat_type=moat_type,
            sub_scores={k: round(v, 1) for k, v in available_scores.items()},
            evidence=evidence,
            insufficient_data=False,
        )

    @staticmethod
    def format_report(result: MoatResult) -> str:
        if result.insufficient_data:
            return f"【{result.code}】护城河分析：数据不足，跳过"
        lines = [
            f"【{result.code}】护城河分析 - {result.moat_type}（{result.moat_score}/100）",
            "",
            "■ 7 维子评分:",
        ]
        labels = {
            "gross_margin_stability": "毛利率稳定性",
            "roic_consistency": "ROIC 一致性",
            "pricing_power": "定价权",
            "asset_lightness": "资产轻重",
            "rd_intensity": "研发强度",
            "market_share": "市场份额",
            "porter_5_forces": "Porter 五力",
        }
        for k, v in result.sub_scores.items():
            lines.append(f"  • {labels.get(k, k)}: {v}/100")
        lines.append("")
        lines.append("■ 证据链:")
        for ev in result.evidence:
            lines.append(f"  • {ev}")
        return "\n".join(lines)
