#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价值投资决策整合（v5.0 新增）⭐

整合 6 个价值投资子模块 + 量化因子，输出最终投资决策。

加权融合（数据完整时）:
| 模块          | 权重 | 评分来源                          |
|---------------|------|-----------------------------------|
| DCF 估值      | 25%  | 安全边际映射到 0-100              |
| 护城河        | 20%  | moat.MoatAnalyzer.moat_score      |
| 财务健康      | 15%  | financial_health.score            |
| 管理层        | 15%  | management.score                  |
| 行业吸引力    | 15%  | industry_analysis.attractiveness   |
| 量化因子      | 10%  | factor_analysis composite          |

verdict 映射:
- ≥80 强烈买入 / ≥65 买入 / ≥50 持有 / ≥35 卖出 / <35 强烈卖出

confidence = 数据完整度（6 模块可用比例）× 信号一致性（6 模块方向同意度）

输出: DecisionReport(verdict, confidence, fair_value_range, margin_of_safety,
        weighted_score, breakdown, strengths, risks, catalysts, narrative)
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..data.financial_statements import fetch_all_financials
from ..data.market import MarketData
from .moat import MoatAnalyzer, MoatResult
from .financial_health import FinancialHealthChecker, HealthResult
from .dcf_valuation import DCFValuation, DCFResult
from .management import ManagementAssessment, ManagementResult
from .industry_analysis import IndustryAnalyzer, IndustryResult


@dataclass
class DecisionReport:
    """价值投资决策报告"""
    code: str
    name: str = ""
    verdict: str = "持有"               # 强烈买入/买入/持有/卖出/强烈卖出
    confidence: float = 0.0             # 0-100
    weighted_score: float = 0.0         # 0-100
    fair_value_range: tuple = (0.0, 0.0, 0.0)  # (low, mid, high)
    margin_of_safety: float = 0.0       # 百分比
    current_price: float = 0.0
    breakdown: Dict[str, Dict] = field(default_factory=dict)  # 各模块评分明细
    strengths: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    catalysts: List[str] = field(default_factory=list)
    narrative: str = ""
    insufficient_data: bool = False
    raw_results: Dict = field(default_factory=dict)


class ValueInvestingDecision:
    """价值投资决策整合器"""

    # 6 模块权重
    WEIGHTS = {
        "dcf": 0.25,
        "moat": 0.20,
        "financial_health": 0.15,
        "management": 0.15,
        "industry": 0.15,
        "factor": 0.10,
    }

    def __init__(self, years: int = 5):
        self.years = years
        self.moat_analyzer = MoatAnalyzer(years=years)
        self.health_checker = FinancialHealthChecker(years=years)
        self.dcf_valuator = DCFValuation(forecast_years=5)
        self.mgmt_assessor = ManagementAssessment(years=years)
        self.industry_analyzer = IndustryAnalyzer(years=years)
        self.market = MarketData()

    # ─────────────────────────────────────────────
    # DCF 安全边际 -> 0-100 评分
    # ─────────────────────────────────────────────
    @staticmethod
    def _dcf_to_score(dcf: DCFResult) -> Optional[float]:
        if dcf.insufficient_data or dcf.intrinsic_value_per_share <= 0:
            return None
        # 安全边际 >50% 满分；<0% 严重高估
        m = dcf.margin_of_safety_pct
        if m > 50:
            return 100
        elif m > 30:
            return 90
        elif m > 10:
            return 70
        elif m > -10:
            return 50
        elif m > -30:
            return 30
        else:
            return 10

    # ─────────────────────────────────────────────
    # 因子评分（简化版，避免循环依赖）
    # ─────────────────────────────────────────────
    def _calc_factor_score(self, code: str, financials: dict) -> Optional[float]:
        """
        简化版因子评分：从财务指标提取 ROE/毛利率/营收增长等打分。
        完整版调用 quantitative.factor_analysis，但为避免循环依赖此处用简化版。
        """
        indicators = financials.get("indicators", [])
        if not indicators:
            return None
        ind = indicators[0] if isinstance(indicators, list) and indicators else {}
        roe = float(ind.get("ROE") or ind.get("ROEJQ") or 0)
        gm = float(ind.get("GROSS_PROFIT_RATIO") or ind.get("XSJLL") or 0)
        # 简化评分
        roe_score = max(0, min(100, roe * 4))
        gm_score = max(0, min(100, (gm - 10) / 30 * 100))
        return roe_score * 0.5 + gm_score * 0.5

    # ─────────────────────────────────────────────
    # 信号一致性（各模块方向同意度）
    # ─────────────────────────────────────────────
    @staticmethod
    def _signal_agreement(breakdown: Dict) -> float:
        """
        计算 6 模块信号一致性。
        每个模块方向: >65 看多 (+1), 35-65 中性 (0), <35 看空 (-1)
        一致性 = |Σdirection| / n（1 = 完全一致，0 = 完全分歧）
        """
        n = 0
        sum_dir = 0
        for k, v in breakdown.items():
            score = v.get("score")
            if score is None:
                continue
            n += 1
            if score >= 65:
                sum_dir += 1
            elif score < 35:
                sum_dir -= 1
        if n == 0:
            return 0
        return abs(sum_dir) / n

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────
    def analyze(self, code: str,
                current_price: float = 0.0,
                shares_outstanding: float = 0.0,
                market_cap: float = 0.0,
                stock_returns: Optional[List[float]] = None,
                benchmark_returns: Optional[List[float]] = None,
                financials: Optional[dict] = None) -> DecisionReport:
        """
        执行完整价值投资决策整合分析。

        Args:
            code: 股票代码
            current_price: 现价（用于 DCF 安全边际）
            shares_outstanding: 总股本
            market_cap: 市值
            stock_returns / benchmark_returns: 用于 WACC beta
            financials: 预取的财务数据；None 时自动一次性获取
        """
        # 获取现价（如果未提供）
        if current_price <= 0:
            try:
                rt = self.market.fetch_realtime([code])
                info = rt.get(str(code).zfill(6), {})
                current_price = float(info.get("price", 0))
                if market_cap <= 0:
                    # 腾讯 mkt_cap 字段单位是亿元（实测茅台 ~16218 亿）
                    market_cap = float(info.get("mkt_cap", 0)) * 1e8
                name = info.get("name", "")
            except Exception:
                name = ""
        else:
            name = ""

        # 一次性获取所有财务数据（避免重复网络请求）
        if financials is None:
            financials = fetch_all_financials(code, self.years)

        # 并行执行 6 模块分析（实际上 Python GIL 下顺序执行，但模块内部已并发获取数据）
        # 护城河
        try:
            moat_result = self.moat_analyzer.analyze(code, financials=financials)
        except Exception as e:
            moat_result = MoatResult(code=code, insufficient_data=True,
                                     evidence=[f"护城河分析失败: {e}"])

        # 财务健康
        try:
            health_result = self.health_checker.check(code, market_cap=market_cap,
                                                     financials=financials)
        except Exception as e:
            health_result = HealthResult(code=code, insufficient_data=True,
                                         evidence=[f"财务健康检查失败: {e}"])

        # DCF
        try:
            dcf_result = self.dcf_valuator.valuate(
                code, current_price=current_price,
                shares_outstanding=shares_outstanding,
                market_cap=market_cap,
                stock_returns=stock_returns,
                benchmark_returns=benchmark_returns,
                financials=financials,
            )
        except Exception as e:
            dcf_result = DCFResult(code=code, insufficient_data=True, error=str(e))

        # 管理层
        try:
            mgmt_result = self.mgmt_assessor.assess(code, financials=financials)
        except Exception as e:
            mgmt_result = ManagementResult(code=code, insufficient_data=True,
                                           evidence=[f"管理层评估失败: {e}"])

        # 行业
        try:
            industry_result = self.industry_analyzer.analyze(code)
        except Exception as e:
            industry_result = IndustryResult(code=code, insufficient_data=True)

        # 因子评分
        factor_score = self._calc_factor_score(code, financials)

        # 各模块 0-100 评分
        scores: Dict[str, Optional[float]] = {
            "dcf": self._dcf_to_score(dcf_result),
            "moat": moat_result.moat_score if not moat_result.insufficient_data else None,
            "financial_health": health_result.score if not health_result.insufficient_data else None,
            "management": mgmt_result.score if not mgmt_result.insufficient_data else None,
            "industry": industry_result.attractiveness_score if not industry_result.insufficient_data else None,
            "factor": factor_score,
        }

        # 加权求和（仅用可用维度归一化）
        available = {k: v for k, v in scores.items() if v is not None}
        if not available:
            return DecisionReport(code=code, name=name, insufficient_data=True,
                                  narrative="所有 6 个模块均无数据，无法做出决策")

        weight_sum = sum(self.WEIGHTS[k] for k in available)
        weighted_score = sum(self.WEIGHTS[k] * available[k] for k in available) / max(weight_sum, 1e-9)

        # 数据完整度
        completeness = len(available) / len(self.WEIGHTS)
        # 信号一致性
        breakdown_dict = {k: {"score": v, "weight": self.WEIGHTS[k]} for k, v in available.items()}
        agreement = self._signal_agreement(breakdown_dict)
        # confidence = 完整度 × 一致性
        confidence = completeness * agreement * 100

        # verdict
        if weighted_score >= 80:
            verdict = "强烈买入"
        elif weighted_score >= 65:
            verdict = "买入"
        elif weighted_score >= 50:
            verdict = "持有"
        elif weighted_score >= 35:
            verdict = "卖出"
        else:
            verdict = "强烈卖出"

        # 公允价值区间
        fair_range = dcf_result.fair_value_range if not dcf_result.insufficient_data else (0, 0, 0)
        # 按 confidence 收窄区间
        if confidence > 0 and fair_range[1] > 0:
            mid = fair_range[1]
            shrink = max(0.5, confidence / 100)  # confidence 越高区间越窄
            low = mid * (1 - (mid - fair_range[0]) / mid * shrink) if mid > 0 else 0
            high = mid * (1 + (fair_range[2] - mid) / mid * shrink) if mid > 0 else 0
            fair_range = (round(low, 2), round(mid, 2), round(high, 2))

        margin = dcf_result.margin_of_safety_pct if not dcf_result.insufficient_data else 0

        # 优势 / 风险 / 催化剂
        strengths: List[str] = []
        risks: List[str] = []
        catalysts: List[str] = []

        if scores["moat"] and scores["moat"] >= 70:
            strengths.append(f"护城河稳固（{moat_result.moat_type}，{scores['moat']}分）")
        elif scores["moat"] and scores["moat"] < 40:
            risks.append(f"护城河薄弱（{scores['moat']}分）")

        if scores["financial_health"] and scores["financial_health"] >= 75:
            strengths.append(f"财务健康优秀（{health_result.grade}级）")
        elif scores["financial_health"] and scores["financial_health"] < 50:
            risks.append(f"财务健康堪忧（{health_result.grade}级）")
        if health_result.red_flags:
            risks.extend(health_result.red_flags[:3])  # 最多取 3 条

        if scores["dcf"] and scores["dcf"] >= 70:
            strengths.append(f"估值有吸引力（安全边际 {margin:.1f}%）")
        elif scores["dcf"] and scores["dcf"] < 40:
            risks.append(f"估值偏高（安全边际 {margin:.1f}%）")

        if scores["management"] and scores["management"] >= 70:
            strengths.append(f"管理层质量 {mgmt_result.verdict}（{scores['management']}分）")
        elif scores["management"] and scores["management"] < 50:
            risks.append(f"管理层质量堪忧（{mgmt_result.verdict}）")

        if scores["industry"] and scores["industry"] >= 70:
            catalysts.append(f"行业处于{industry_result.lifecycle_stage}期，吸引力强")
        elif scores["industry"] and scores["industry"] < 40:
            risks.append(f"行业吸引力弱（{industry_result.lifecycle_stage}期）")
        if industry_result.key_drivers:
            catalysts.extend(industry_result.key_drivers[:2])

        # 推演叙述
        narrative_parts: List[str] = []
        narrative_parts.append(f"综合 {len(available)}/6 模块分析，{code} 加权评分 {weighted_score:.1f}/100，")
        narrative_parts.append(f"数据完整度 {completeness*100:.0f}%，信号一致性 {agreement*100:.0f}%，")
        narrative_parts.append(f"整体置信度 {confidence:.0f}/100。")
        if verdict in ("强烈买入", "买入"):
            narrative_parts.append(f"基于 DCF 公允价值区间 ¥{fair_range[0]}-{fair_range[2]}，现价 ¥{current_price}，")
            narrative_parts.append(f"安全边际 {margin:.1f}%。")
            if strengths:
                narrative_parts.append(f"主要优势：{'; '.join(strengths[:2])}。")
        elif verdict == "持有":
            narrative_parts.append("估值基本合理，建议持有等待催化剂。")
        else:
            narrative_parts.append("估值偏高或基本面存在隐忧，建议谨慎。")
            if risks:
                narrative_parts.append(f"主要风险：{'; '.join(risks[:2])}。")

        return DecisionReport(
            code=code,
            name=name,
            verdict=verdict,
            confidence=round(confidence, 1),
            weighted_score=round(weighted_score, 1),
            fair_value_range=fair_range,
            margin_of_safety=round(margin, 1),
            current_price=current_price,
            breakdown={k: {"score": v, "weight": self.WEIGHTS[k]}
                       for k, v in available.items()},
            strengths=strengths,
            risks=risks,
            catalysts=catalysts,
            narrative="".join(narrative_parts),
            insufficient_data=False,
            raw_results={
                "moat": moat_result.__dict__,
                "health": health_result.__dict__,
                "dcf": dcf_result.__dict__,
                "management": mgmt_result.__dict__,
                "industry": industry_result.__dict__,
            },
        )

    @staticmethod
    def format_report(result: DecisionReport) -> str:
        """格式化输出报告（文本 + 末尾 JSON 段）"""
        if result.insufficient_data:
            return f"【{result.code}】价值投资决策：数据不足，跳过\n原因: {result.narrative}"
        labels = {
            "dcf": "DCF 估值",
            "moat": "护城河",
            "financial_health": "财务健康",
            "management": "管理层",
            "industry": "行业吸引力",
            "factor": "量化因子",
        }
        lines = [
            f"【{result.code} {result.name}】价值投资决策 - {result.verdict}",
            f"■ 加权评分: {result.weighted_score}/100   置信度: {result.confidence}/100",
            f"■ 现价: ¥{result.current_price}   公允价值区间: ¥{result.fair_value_range[0]} - ¥{result.fair_value_range[2]}",
            f"■ 安全边际: {result.margin_of_safety}%",
            "",
            "■ 6 模块评分明细:",
        ]
        for k, v in result.breakdown.items():
            score = v.get("score", 0)
            weight = v.get("weight", 0)
            lines.append(f"  • {labels.get(k, k)}: {score}/100（权重 {weight*100:.0f}%）")
        if result.strengths:
            lines.append("")
            lines.append("■ ✅ 核心优势:")
            for s in result.strengths:
                lines.append(f"  • {s}")
        if result.risks:
            lines.append("")
            lines.append("■ ⚠️ 主要风险:")
            for r in result.risks:
                lines.append(f"  • {r}")
        if result.catalysts:
            lines.append("")
            lines.append("■ 🚀 催化剂:")
            for c in result.catalysts:
                lines.append(f"  • {c}")
        lines.append("")
        lines.append("■ 推演叙述:")
        lines.append(f"  {result.narrative}")
        # 末尾追加机器可读 JSON 段
        lines.append("")
        lines.append("<!-- JSON_START")
        json_payload = {
            "code": result.code,
            "name": result.name,
            "verdict": result.verdict,
            "weighted_score": result.weighted_score,
            "confidence": result.confidence,
            "current_price": result.current_price,
            "fair_value_range": list(result.fair_value_range),
            "margin_of_safety": result.margin_of_safety,
            "breakdown": result.breakdown,
            "strengths": result.strengths,
            "risks": result.risks,
            "catalysts": result.catalysts,
        }
        lines.append(json.dumps(json_payload, ensure_ascii=False, indent=2))
        lines.append("JSON_END -->")
        return "\n".join(lines)
