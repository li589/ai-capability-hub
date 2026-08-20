#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
格雷厄姆分析 Agent
Benjamin Graham Analysis Agent
分析：盈利稳定性、财务实力、Graham Number、NCAV、安全边际
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class GrahamAnalysis:
    """格雷厄姆分析结果"""
    # 盈利稳定性
    eps_stability: float = 0  # EPS稳定性评分
    eps_growth_trend: float = 0  # EPS增长趋势
    positive_years: int = 0  # 正EPS年数

    # 财务实力
    current_ratio: float = 0  # 流动比率
    debt_ratio: float = 0      # 资产负债率
    dividend_record: float = 0 # 分红记录

    # 估值
    graham_number: float = 0   # 格雷厄姆数值
    ncav: float = 0             # NCAV流动资产净值
    margin_of_safety: float = 0  # 安全边际

    # 综合评分
    graham_score: float = 0     # 格雷厄姆综合评分
    signal: str = "中性"       # 信号


class GrahamAnalyzer:
    """
    格雷厄姆价值投资分析

    核心原则：
    1. 盈利稳定性：正EPS年数多、EPS增长稳定
    2. 财务实力：流动比率>2、资产负债率<50%、有分红记录
    3. 估值：Graham Number、NCAV、安全边际
    """

    def __init__(self):
        self.CURRENT_RATIO_THRESHOLD = 2.0
        self.DEBT_RATIO_THRESHOLD = 0.5

    def analyze(
        self,
        eps_history: List[float] = None,  # EPS历史序列
        current_ratio: float = 0,    # 流动比率
        total_assets: float = 0,     # 总资产
        total_liabilities: float = 0,  # 总负债
        current_assets: float = 0,   # 流动资产
        bvps: float = 0,             # 每股净资产
        price: float = 0,            # 当前股价
        dividend_history: List[float] = None,  # 分红历史
        years: int = 7,             # 分析年数
    ) -> GrahamAnalysis:
        """
        执行格雷厄姆风格分析

        Args:
            eps_history: EPS历史序列
            current_ratio: 流动比率
            total_assets: 总资产
            total_liabilities: 总负债
            current_assets: 流动资产
            bvps: 每股净资产
            price: 当前股价
            dividend_history: 分红历史
            years: 分析年数

        Returns:
            GrahamAnalysis
        """
        eps_history = eps_history or []
        dividend_history = dividend_history or []

        # 1. 盈利稳定性 (4分)
        eps_stability = 0
        if len(eps_history) >= years:
            recent_eps = eps_history[-years:]
            positive_years = sum(1 for e in recent_eps if e > 0)
            eps_stability = positive_years / years * 4

            # EPS增长趋势
            if len(recent_eps) >= 2:
                first_half = sum(recent_eps[:len(recent_eps)//2]) / (len(recent_eps)//2)
                second_half = sum(recent_eps[len(recent_eps)//2:]) / (len(recent_eps) - len(recent_eps)//2)
                if first_half > 0:
                    eps_growth_trend = (second_half / first_half - 1) * 100
                else:
                    eps_growth_trend = 0
            else:
                eps_growth_trend = 0
        else:
            positive_years = sum(1 for e in eps_history if e > 0)
            eps_stability = positive_years / max(1, len(eps_history)) * 4
            eps_growth_trend = 0

        # 2. 财务实力 (5分)
        financial_score = 0

        # 流动比率 >= 2 得2分
        if current_ratio >= self.CURRENT_RATIO_THRESHOLD:
            financial_score += 2
        elif current_ratio >= 1.5:
            financial_score += 1

        # 资产负债率 < 50% 得2分
        if total_assets > 0:
            debt_ratio = total_liabilities / total_assets
            if debt_ratio < self.DEBT_RATIO_THRESHOLD:
                financial_score += 2
            elif debt_ratio < 0.6:
                financial_score += 1
        else:
            debt_ratio = 0

        # 有分红记录 +1
        if dividend_history and sum(dividend_history) > 0:
            financial_score += 1

        # 3. Graham Number
        eps_ttm = eps_history[-1] if eps_history else 0
        graham_number = self._calc_graham_number(eps_ttm, bvps)

        # 4. NCAV
        ncav = self._calc_ncav(current_assets, total_liabilities)

        # 5. 安全边际
        margin_of_safety = 0
        if graham_number > 0 and price > 0:
            margin_of_safety = (graham_number - price) / graham_number * 100
        elif ncav > 0 and price > 0:
            margin_of_safety = (ncav - price) / ncav * 100

        # 6. 综合评分
        # 盈利稳定性 30% + 财务实力 30% + 估值安全边际 40%
        graham_score = (
            eps_stability / 4 * 100 * 0.3 +
            financial_score / 5 * 100 * 0.3 +
            max(0, min(100, margin_of_safety)) * 0.4
        )
        graham_score = max(-100, min(100, graham_score))

        # 7. 信号
        signal = self._get_signal(graham_score, margin_of_safety)

        return GrahamAnalysis(
            eps_stability=round(eps_stability, 2),
            eps_growth_trend=round(eps_growth_trend, 1),
            positive_years=positive_years,
            current_ratio=round(current_ratio, 2) if current_ratio > 0 else 0,
            debt_ratio=round(debt_ratio * 100, 1) if debt_ratio > 0 else 0,
            dividend_record=round(len([d for d in dividend_history if d > 0]) / max(1, len(dividend_history)) * 100, 1),
            graham_number=round(graham_number, 2),
            ncav=round(ncav, 2),
            margin_of_safety=round(margin_of_safety, 1),
            graham_score=round(graham_score, 1),
            signal=signal
        )

    @staticmethod
    def _calc_graham_number(eps: float, bvps: float) -> float:
        """
        Graham Number = sqrt(22.5 * EPS * Book Value Per Share)
        """
        if eps <= 0 or bvps <= 0:
            return 0
        return (22.5 * eps * bvps) ** 0.5

    @staticmethod
    def _calc_ncav(current_assets: float, total_liabilities: float) -> float:
        """
        NCAV = 流动资产 - 总负债
        格雷厄姆认为市值为NCAV的2/3以下时有安全边际
        """
        return current_assets - total_liabilities

    @staticmethod
    def _get_signal(score: float, margin_of_safety: float) -> str:
        """根据评分和安全边际生成信号"""
        if score > 60 and margin_of_safety > 30:
            return "强烈买入"
        elif score > 30 or margin_of_safety > 20:
            return "买入"
        elif score < -60 or margin_of_safety < -30:
            return "强烈卖出"
        elif score < -30 or margin_of_safety < -20:
            return "卖出"
        else:
            return "中性"

    def get_investment_advice(self, analysis: GrahamAnalysis) -> Dict:
        """获取格雷厄姆风格投资建议"""
        advice = {
            "action": analysis.signal,
            "graham_number": analysis.graham_number,
            "ncav": analysis.ncav,
            "margin_of_safety": analysis.margin_of_safety,
            "key_points": []
        }

        # 关键点
        if analysis.graham_number > 0:
            advice["key_points"].append(f"Graham Number: {analysis.graham_number:.2f}")

        if analysis.ncav > 0:
            advice["key_points"].append(f"NCAV: {analysis.ncav:.2f}万")

        if analysis.current_ratio >= self.CURRENT_RATIO_THRESHOLD:
            advice["key_points"].append(f"流动比率 {analysis.current_ratio:.2f} >= {self.CURRENT_RATIO_THRESHOLD}, 财务健康")
        else:
            advice["key_points"].append(f"流动比率 {analysis.current_ratio:.2f} < {self.CURRENT_RATIO_THRESHOLD}")

        if analysis.debt_ratio < 50:
            advice["key_points"].append(f"资产负债率 {analysis.debt_ratio:.1f}% < 50%, 杠杆适中")
        else:
            advice["key_points"].append(f"资产负债率 {analysis.debt_ratio:.1f}% > 50%, 注意债务风险")

        # 建议
        if analysis.signal in ("强烈买入", "买入"):
            advice["suggestion"] = f"安全边际 {analysis.margin_of_safety:.1f}%, 价值投资机会"
        elif analysis.signal == "中性":
            advice["suggestion"] = "估值合理，观望"
        else:
            advice["suggestion"] = f"溢价明显 {abs(analysis.margin_of_safety):.1f}%, 谨慎"

        return advice