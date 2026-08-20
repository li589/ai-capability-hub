#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彼得林奇分析 Agent
Peter Lynch Analysis Agent
分析：成长性、GARP、负债率、自由现金流、机构持仓
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class LynchAnalysis:
    """彼得林奇分析结果"""
    # 成长性
    revenue_growth: float = 0    # 营收增长率
    eps_growth: float = 0        # EPS增长率
    cagr: float = 0              # 复合增长率

    # GARP
    pe: float = 0                # 市盈率
    peg: float = 0               # PEG值

    # 基本面
    debt_ratio: float = 0        # 负债率
    operating_margin: float = 0  # 营业利润率
    fcf_quality: float = 0       # 自由现金流质量

    # 机构持仓
    institutional_holding: float = 0  # 机构持仓比例

    # 综合评分
    lynch_score: float = 0       # 林奇综合评分
    signal: str = "中性"         # 信号


class LynchAnalyzer:
    """
    彼得林奇成长股投资分析

    核心原则：
    1. 成长性：营收增长、EPS增长、CAGR
    2. GARP：PEG < 1 为优质，< 2 可接受
    3. 基本面：负债率低、营业利润率高、自由现金流为正
    4. 机构持仓：机构大量持有是积极信号
    """

    def analyze(
        self,
        revenue_history: List[float] = None,  # 营收历史
        eps_history: List[float] = None,      # EPS历史
        years: int = 5,
        pe: float = 0,                        # 市盈率
        price: float = 0,                     # 股价
        bvps: float = 0,                      # 每股净资产
        total_debt: float = 0,                # 总负债
        total_assets: float = 0,              # 总资产
        operating_margin: float = 0,          # 营业利润率
        fcf: float = 0,                       # 自由现金流
        shares_outstanding: float = 0,        # 流通股
        institutional_holding: float = 0,     # 机构持仓比例
    ) -> LynchAnalysis:
        """
        执行彼得林奇风格分析
        """
        revenue_history = revenue_history or []
        eps_history = eps_history or []

        # 1. 成长性 (30%)
        growth_score = 0

        # 营收增长
        if len(revenue_history) >= 2:
            rev_start = revenue_history[0]
            rev_end = revenue_history[-1]
            if rev_start > 0:
                revenue_growth = (rev_end / rev_start - 1) / (len(revenue_history) - 1) * 100
            else:
                revenue_growth = 0
        else:
            revenue_growth = 0

        # EPS增长
        if len(eps_history) >= 2:
            eps_start = eps_history[0]
            eps_end = eps_history[-1]
            if eps_start > 0:
                eps_growth = (eps_end / eps_start - 1) / (len(eps_history) - 1) * 100
            else:
                eps_growth = 0
        else:
            eps_growth = 0

        # 复合增长率
        if len(revenue_history) >= 3 and revenue_history[0] > 0:
            years_count = len(revenue_history) - 1
            cagr = ((revenue_history[-1] / revenue_history[0]) ** (1/years_count) - 1) * 100
        else:
            cagr = 0

        # 成长评分
        if revenue_growth > 20:
            growth_score += 10
        elif revenue_growth > 10:
            growth_score += 5
        elif revenue_growth > 0:
            growth_score += 2

        if eps_growth > 20:
            growth_score += 10
        elif eps_growth > 10:
            growth_score += 5
        elif eps_growth > 0:
            growth_score += 2

        if cagr > 15:
            growth_score += 10
        elif cagr > 10:
            growth_score += 5

        # 2. GARP (25%)
        garp_score = 0
        if eps_growth != 0 and pe > 0:
            peg = pe / max(eps_growth, 0.1)
            if peg < 1:
                garp_score = 25
            elif peg < 1.5:
                garp_score = 20
            elif peg < 2:
                garp_score = 15
            elif peg < 3:
                garp_score = 5

        # 3. 基本面 (20%)
        fundamental_score = 0

        # 负债率
        if total_assets > 0:
            debt_ratio = total_debt / total_assets
            if debt_ratio < 0.3:
                fundamental_score += 8
            elif debt_ratio < 0.5:
                fundamental_score += 4

        # 营业利润率
        if operating_margin > 20:
            fundamental_score += 8
        elif operating_margin > 10:
            fundamental_score += 4

        # 自由现金流
        if fcf > 0:
            fundamental_score += 4
        else:
            fundamental_score -= 5

        # 4. 机构持仓 (15%)
        institution_score = 0
        if institutional_holding > 70:
            institution_score = 15
        elif institutional_holding > 50:
            institution_score = 10
        elif institutional_holding > 30:
            institution_score = 5

        # 5. 情绪 (10%)
        sentiment_score = 0

        # 6. 综合评分
        lynch_score = (
            growth_score * 0.30 +
            garp_score * 0.25 +
            max(0, fundamental_score) * 0.20 +
            institution_score * 0.15 +
            sentiment_score * 0.10
        )
        lynch_score = max(-100, min(100, lynch_score))

        # 7. 信号（v5.0 修复：原代码传 pe 而非 peg，导致 PEG 判断失效）
        peg = pe / max(eps_growth, 0.1) if eps_growth > 0 and pe > 0 else 0
        signal = self._get_signal(lynch_score, pe, peg, cagr)

        return LynchAnalysis(
            revenue_growth=round(revenue_growth, 1),
            eps_growth=round(eps_growth, 1),
            cagr=round(cagr, 1),
            pe=round(pe, 2) if pe > 0 else 0,
            peg=round(pe / max(eps_growth, 0.1), 2) if eps_growth > 0 and pe > 0 else 0,
            debt_ratio=round(debt_ratio * 100, 1) if total_assets > 0 else 0,
            operating_margin=round(operating_margin, 2) if operating_margin > 0 else 0,
            fcf_quality=round(fcf / max(1, price * shares_outstanding) * 100, 2) if fcf > 0 else 0,
            institutional_holding=round(institutional_holding, 1),
            lynch_score=round(lynch_score, 1),
            signal=signal
        )

    @staticmethod
    def _get_signal(score: float, pe: float, peg: float, cagr: float) -> str:
        """生成信号"""
        if score > 60 and peg < 1 and cagr > 10:
            return "强烈买入"
        elif score > 30 and peg < 1.5:
            return "买入"
        elif score < -60 or (pe > 50 and peg > 3):
            return "强烈卖出"
        elif score < -30 or pe > 80:
            return "卖出"
        else:
            return "中性"

    def get_investment_advice(self, analysis: LynchAnalysis) -> Dict:
        """获取林奇风格投资建议"""
        advice = {
            "action": analysis.signal,
            "growth_score": analysis.lynch_score,
            "key_metrics": {}
        }

        advice["key_metrics"] = {
            "revenue_growth": f"{analysis.revenue_growth:.1f}%",
            "eps_growth": f"{analysis.eps_growth:.1f}%",
            "cagr": f"{analysis.cagr:.1f}%",
            "peg": f"{analysis.peg:.2f}" if analysis.peg > 0 else "N/A",
            "debt_ratio": f"{analysis.debt_ratio:.1f}%"
        }

        if analysis.signal == "强烈买入":
            advice["suggestion"] = f"成长性优异(CAGR {analysis.cagr:.1f}%), PEG {analysis.peg:.2f} < 1, 强烈买入"
        elif analysis.signal == "买入":
            advice["suggestion"] = f"成长性良好，PEG {analysis.peg:.2f} < 1.5, 可买入"
        elif analysis.signal == "中性":
            advice["suggestion"] = "成长性一般，观望"
        else:
            advice["suggestion"] = f"估值过高(PE {analysis.pe:.0f}), 谨慎"

        return advice