#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巴菲特分析 Agent
Warren Buffett Analysis Agent
分析：盈利能力、护城河、管理质量、内在价值、安全边际
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class BuffettAnalysis:
    """巴菲特分析结果"""
    # 盈利能力
    roe: float = 0              # 净资产收益率
    operating_margin: float = 0 # 营业利润率
    profit_quality: float = 0   # 盈利质量

    # 护城河
    moat_score: float = 0      # 护城河评分
    roe_consistency: float = 0  # ROE一致性

    # 管理质量
    management_score: float = 0 # 管理评分

    # 价值评估
    intrinsic_value: float = 0  # 内在价值
    margin_of_safety: float = 0  # 安全边际

    # 综合评分
    buffett_score: float = 0    # 巴菲特综合评分 (-100 ~ +100)
    signal: str = "中性"        # 强烈买入/买入/中性/卖出/强烈卖出


class BuffettAnalyzer:
    """
    巴菲特价值投资分析

    核心原则：
    1. 盈利能力：ROE > 15%，营业利润率稳定
    2. 护城河：ROE一致性高、毛利率稳定、研发投入
    3. 管理质量：股票回购、分红、股东权益增长
    4. 内在价值：三阶段DCF模型
    5. 安全边际：价格低于内在价值时有投资价值
    """

    def __init__(self):
        self.ROE_THRESHOLD = 15  # ROE阈值
        self.MARGIN_THRESHOLD = 15  # 营业利润率阈值

    def analyze(
        self,
        roe: float = 0,                  # 净资产收益率
        net_income: float = 0,           # 净利润
        total_assets: float = 0,         # 总资产
        revenue: float = 0,              # 营业收入
        operating_margin: float = 0,    # 营业利润率
        shares_outstanding: float = 0,  # 流通股数
        price: float = 0,                # 当前股价
        bvps: float = 0,                 # 每股净资产
        eps: float = 0,                 # 每股收益
        fcf: float = 0,                 # 自由现金流
        growth_rate: float = 0.15,      # 增长率
        dividend_paid: float = 0,       # 分红金额
        shares_repurchase: float = 0,  # 回购金额
        roe_history: List[float] = None,  # ROE历史序列
        gross_margin_history: List[float] = None,  # 毛利率历史
    ) -> BuffettAnalysis:
        """
        执行巴菲特风格分析

        Args:
            roe: 净资产收益率
            net_income: 净利润
            total_assets: 总资产
            revenue: 营业收入
            operating_margin: 营业利润率
            shares_outstanding: 流通股数
            price: 当前股价
            bvps: 每股净资产
            eps: 每股收益
            fcf: 自由现金流
            growth_rate: 增长率
            dividend_paid: 分红金额
            shares_repurchase: 回购金额
            roe_history: ROE历史序列
            gross_margin_history: 毛利率历史

        Returns:
            BuffettAnalysis: 巴菲特分析结果
        """
        roe_history = roe_history or []
        gross_margin_history = gross_margin_history or []

        # 1. 盈利能力评分 (10分)
        profit_score = 0
        if roe > self.ROE_THRESHOLD:
            profit_score += 4
        elif roe > 10:
            profit_score += 2

        if operating_margin > self.MARGIN_THRESHOLD:
            profit_score += 3
        elif operating_margin > 5:
            profit_score += 1

        # 盈利稳定性
        if len(roe_history) >= 3:
            positive_years = sum(1 for r in roe_history if r > 0)
            consistency = positive_years / len(roe_history)
            if consistency > 0.8:
                profit_score += 3
            elif consistency > 0.5:
                profit_score += 1

        # 2. 护城河评分 (5分)
        moat_score = 0

        # ROE一致性 > 80% 得2分
        if len(roe_history) >= 3:
            roe_std = self._calc_std(roe_history)
            roe_mean = sum(roe_history) / len(roe_history)
            if roe_mean > 0 and roe_std / roe_mean < 0.3:
                moat_score += 2

        # 毛利率稳定（波动<20%）得2分
        if len(gross_margin_history) >= 3:
            gm_std = self._calc_std(gross_margin_history)
            gm_mean = sum(gross_margin_history) / len(gross_margin_history)
            if gm_mean > 0 and gm_std / gm_mean < 0.2:
                moat_score += 2

        # 营业利润率高（>15%）得1分
        if operating_margin > 20:
            moat_score += 1

        # 3. 管理质量评分 (2分)
        mgmt_score = 0

        # 回购股票 +1
        if shares_repurchase > 0:
            mgmt_score += 1

        # 分红 +1
        if dividend_paid > 0:
            mgmt_score += 1

        # 4. 计算内在价值（简化DCF）
        intrinsic_value_total = self._calc_dcf_intrinsic_value(fcf, growth_rate)
        # v5.0 修复：原代码将总值直接与每股 price 比较，导致安全边际计算错误
        # 正确做法：总值 / 总股本 = 每股内在价值
        if shares_outstanding > 0:
            intrinsic_value = intrinsic_value_total / shares_outstanding
        else:
            intrinsic_value = intrinsic_value_total  # 兜底：无股本数据时保留原行为

        # 5. 安全边际
        margin_of_safety = 0
        if intrinsic_value > 0 and price > 0:
            margin_of_safety = (intrinsic_value - price) / intrinsic_value * 100

        # 6. 综合评分
        # 盈利能力 40% + 护城河 25% + 管理 10% + 安全边际 25%
        buffett_score = (
            profit_score * 0.4 * 10 +  # 转换为 -100 ~ +100
            moat_score * 0.25 * 10 +
            mgmt_score * 0.1 * 10 +
            (margin_of_safety / 50 * 100) * 0.25
        )
        buffett_score = max(-100, min(100, buffett_score))

        # 7. 信号
        signal = self._get_signal(buffett_score, margin_of_safety)

        return BuffettAnalysis(
            roe=round(roe, 2) if roe > 0 else 0,
            operating_margin=round(operating_margin, 2) if operating_margin > 0 else 0,
            profit_quality=round(profit_score / 10 * 100, 1),
            moat_score=round(moat_score / 5 * 100, 1),
            roe_consistency=round(sum(roe_history) / len(roe_history) if roe_history else 0, 1),
            management_score=round(mgmt_score / 2 * 100, 1),
            intrinsic_value=round(intrinsic_value, 2),
            margin_of_safety=round(margin_of_safety, 1),
            buffett_score=round(buffett_score, 1),
            signal=signal
        )

    @staticmethod
    def _calc_std(values: List[float]) -> float:
        """计算标准差"""
        if not values:
            return 0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance ** 0.5

    @staticmethod
    def _calc_dcf_intrinsic_value(
        fcf: float,
        growth_rate: float,
        discount_rate: float = 0.08,
        years: int = 5,
        terminal_growth: float = 0.025
    ) -> float:
        """
        简化DCF内在价值计算

        Args:
            fcf: 自由现金流
            growth_rate: 增长率
            discount_rate: 折现率
            years: 预测年数
            terminal_growth: 永续增长率

        Returns:
            内在价值
        """
        if fcf <= 0:
            return 0

        # 简化处理：使用单阶段模型 + 永续价值
        # 第一阶段（前5年）
        pv_high = 0
        for i in range(1, years + 1):
            fcf_future = fcf * ((1 + growth_rate) ** i)
            pv = fcf_future / ((1 + discount_rate) ** i)
            pv_high += pv

        # 永续价值
        terminal_fcf = fcf * ((1 + growth_rate) ** years) * (1 + terminal_growth)
        terminal_value = terminal_fcf / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** years)

        return pv_high + pv_terminal

    @staticmethod
    def _get_signal(score: float, margin_of_safety: float) -> str:
        """根据评分和安全边际生成信号"""
        if score > 60 and margin_of_safety > 20:
            return "强烈买入"
        elif score > 30 or margin_of_safety > 10:
            return "买入"
        elif score < -60 or margin_of_safety < -20:
            return "强烈卖出"
        elif score < -30 or margin_of_safety < -10:
            return "卖出"
        else:
            return "中性"

    def get_investment_advice(self, analysis: BuffettAnalysis) -> Dict:
        """
        获取巴菲特风格投资建议

        Returns:
            Dict: {"action": str, "reason": str, "target_price": float}
        """
        advice = {
            "action": analysis.signal,
            "intrinsic_value": analysis.intrinsic_value,
            "margin_of_safety": analysis.margin_of_safety,
            "key_points": []
        }

        # 关键点
        if analysis.roe > self.ROE_THRESHOLD:
            advice["key_points"].append(f"ROE {analysis.roe:.1f}% > {self.ROE_THRESHOLD}%, 盈利能力强")
        elif analysis.roe > 0:
            advice["key_points"].append(f"ROE {analysis.roe:.1f}% < {self.ROE_THRESHOLD}%, 盈利能力一般")

        if analysis.operating_margin > self.MARGIN_THRESHOLD:
            advice["key_points"].append(f"营业利润率 {analysis.operating_margin:.1f}% > {self.MARGIN_THRESHOLD}%, 护城河宽")

        if analysis.margin_of_safety > 20:
            advice["key_points"].append(f"安全边际 {analysis.margin_of_safety:.1f}%, 价值显著")
        elif analysis.margin_of_safety < 0:
            advice["key_points"].append(f"溢价 {abs(analysis.margin_of_safety):.1f}%, 注意风险")

        # 建议操作
        if analysis.signal == "强烈买入":
            advice["suggestion"] = "当前价格显著低于内在价值，安全边际高，建议积极买入"
            advice["target_price"] = analysis.intrinsic_value * 0.85
        elif analysis.signal == "买入":
            advice["suggestion"] = "价格具有安全边际，可考虑买入"
            advice["target_price"] = analysis.intrinsic_value * 0.9
        elif analysis.signal == "中性":
            advice["suggestion"] = "估值合理，观望为主"
            advice["target_price"] = analysis.intrinsic_value
        elif analysis.signal == "卖出":
            advice["suggestion"] = "价格高于内在价值，建议减仓"
            advice["target_price"] = analysis.intrinsic_value * 1.1
        else:
            advice["suggestion"] = "显著高估，建议清仓"
            advice["target_price"] = analysis.intrinsic_value * 1.2

        return advice