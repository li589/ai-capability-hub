#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
估值分析引擎
Valuation Analysis Engine
包含：PE/PB/PCF/PS历史分位、估值中枢、Graham Number、DCF内在价值
"""

import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValuationMetrics:
    """估值指标数据"""
    # 当前估值
    pe: float = 0
    pb: float = 0
    pcf: float = 0  # 市现率
    ps: float = 0    # 市销率

    # 历史分位 (0-100)
    pe_percentile: float = 50
    pb_percentile: float = 50
    pcf_percentile: float = 50
    ps_percentile: float = 50

    # 估值信号
    val_signal: str = "中性"
    val_score: float = 0
    val_confidence: float = 0.5

    # 投资价值
    margin_of_safety: float = 0  # 安全边际
    graham_number: float = 0     # 格雷厄姆数值
    dcf_value: float = 0          # DCF内在价值

    # 估值状态
    valuation_state: str = "正常"  # 偏低/正常/偏高/泡沫


class ValuationAnalyzer:
    """估值分析指标计算器"""

    def __init__(self):
        self.industry_pe = {}  # 行业PE中位数

    @staticmethod
    def calc_percentile(values: List[float], current: float) -> float:
        """计算当前值在历史序列中的分位"""
        if not values or len(values) < 5:
            return 50

        valid_values = [v for v in values if v > 0 and v < 10000]  # 过滤异常值
        if not valid_values:
            return 50

        valid_values.sort()
        n = len(valid_values)

        # 线性插值
        rank = sum(1 for v in valid_values if v < current)
        percentile = (rank + 0.5) / n * 100

        return max(0, min(100, percentile))

    @staticmethod
    def calc_valuation_center(values: List[float]) -> Dict[str, float]:
        """计算估值中枢 (均值、中位数)"""
        if not values:
            return {"mean": 0, "median": 0, "std": 0}

        valid_values = [v for v in values if v > 0 and v < 10000]
        if not valid_values:
            return {"mean": 0, "median": 0, "std": 0}

        mean = sum(valid_values) / len(valid_values)
        sorted_vals = sorted(valid_values)
        n = len(sorted_vals)
        median = sorted_vals[n // 2] if n % 2 == 1 else (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2

        variance = sum((v - mean) ** 2 for v in valid_values) / len(valid_values)
        std = math.sqrt(variance)

        return {"mean": round(mean, 2), "median": round(median, 2), "std": round(std, 2)}

    @staticmethod
    def calc_graham_number(eps: float, bvps: float) -> float:
        """
        格雷厄姆数值
        Graham Number = sqrt(22.5 * EPS * Book Value Per Share)
        """
        if eps <= 0 or bvps <= 0:
            return 0
        return math.sqrt(22.5 * eps * bvps)

    @staticmethod
    def calc_ncav(net_current_assets: float, total_liabilities: float) -> float:
        """
        NCAV (Net Current Asset Value) 流动资产净值
        NCAV = 流动资产 - 总负债
        格雷厄姆：市值为NCAV的2/3以下时有安全边际
        """
        return net_current_assets - total_liabilities

    @staticmethod
    def calc_dcf_intrinsic_value(
        fcf: float,           # 自由现金流
        growth_rate: float,    # 增长率
        years: int = 5,        # 预测年数
        discount_rate: float = 0.08,  # 折现率
        terminal_growth: float = 0.025  # 永续增长率
    ) -> float:
        """
        DCF三阶段内在价值计算
        """
        if fcf <= 0 or growth_rate < 0 or growth_rate > 0.5:
            return 0

        # 第一阶段：高增长期（前5年）
        pv_high = 0
        for i in range(1, years + 1):
            fcf_future = fcf * ((1 + growth_rate) ** i)
            pv = fcf_future / ((1 + discount_rate) ** i)
            pv_high += pv

        # 第二阶段：过渡期（6-10年，增长率线性衰减到永续增长率）
        pv_transition = 0
        for i in range(years + 1, years + 5 + 1):
            year_in_phase = i - years
            growth_in_phase = growth_rate * (1 - year_in_phase / 5) + terminal_growth * (year_in_phase / 5)
            if growth_in_phase < terminal_growth:
                growth_in_phase = terminal_growth
            fcf_future = fcf * ((1 + growth_rate) ** years) * ((1 + growth_in_phase) ** (i - years))
            pv = fcf_future / ((1 + discount_rate) ** i)
            pv_transition += pv

        # 第三阶段：永续价值
        fcf_at_year_10 = fcf * ((1 + growth_rate) ** years) * ((1 + terminal_growth) ** 5)
        terminal_value = fcf_at_year_10 * (1 + terminal_growth) / (discount_rate - terminal_growth)
        pv_terminal = terminal_value / ((1 + discount_rate) ** (years + 5))

        return pv_high + pv_transition + pv_terminal

    def analyze(
        self,
        pe: float = 0,
        pb: float = 0,
        pcf: float = 0,
        ps: float = 0,
        eps: float = 0,
        bvps: float = 0,
        fcf: float = 0,
        growth_rate: float = 0.15,
        price: float = 0,
        pe_history: List[float] = None,
        pb_history: List[float] = None,
        pcf_history: List[float] = None,
        ps_history: List[float] = None
    ) -> ValuationMetrics:
        """
        综合估值分析

        Args:
            pe: 市盈率
            pb: 市净率
            pcf: 市现率
            ps: 市销率
            eps: 每股收益
            bvps: 每股净资产
            fcf: 自由现金流
            growth_rate: 增长率
            price: 当前股价
            pe_history: PE历史序列
            pb_history: PB历史序列
            pcf_history: PCF历史序列
            ps_history: PS历史序列
        """
        pe_history = pe_history or []
        pb_history = pb_history or []
        pcf_history = pcf_history or []
        ps_history = ps_history or []

        # 计算历史分位
        pe_pct = self.calc_percentile(pe_history, pe) if pe_history else 50
        pb_pct = self.calc_percentile(pb_history, pb) if pb_history else 50
        pcf_pct = self.calc_percentile(pcf_history, pcf) if pcf_history else 50
        ps_pct = self.calc_percentile(ps_history, ps) if ps_history else 50

        # 计算格雷厄姆数值
        graham_num = self.calc_graham_number(eps, bvps)

        # 计算DCF内在价值
        dcf_value = self.calc_dcf_intrinsic_value(fcf, growth_rate) if fcf > 0 else 0

        # 安全边际
        margin_of_safety = 0
        if graham_num > 0 and price > 0:
            margin_of_safety = (graham_num - price) / price * 100
        elif dcf_value > 0 and price > 0:
            margin_of_safety = (dcf_value - price) / price * 100

        # 估值综合评分
        val_score = self._calc_valuation_score(pe_pct, pb_pct, pcf_pct, ps_pct)

        # 估值状态判断
        valuation_state = self._get_valuation_state(pe, pb, pe_pct, pb_pct)

        # 估值信号
        val_signal = "低估" if val_score > 20 else ("高估" if val_score < -20 else "中性")

        return ValuationMetrics(
            pe=round(pe, 2) if pe > 0 else 0,
            pb=round(pb, 2) if pb > 0 else 0,
            pcf=round(pcf, 2) if pcf > 0 else 0,
            ps=round(ps, 2) if ps > 0 else 0,
            pe_percentile=round(pe_pct, 1),
            pb_percentile=round(pb_pct, 1),
            pcf_percentile=round(pcf_pct, 1),
            ps_percentile=round(ps_pct, 1),
            val_signal=val_signal,
            val_score=round(val_score, 1),
            val_confidence=round(min(0.9, 0.5 + (len(pe_history) + len(pb_history)) / 400), 2),
            margin_of_safety=round(margin_of_safety, 1),
            graham_number=round(graham_num, 2),
            dcf_value=round(dcf_value, 2),
            valuation_state=valuation_state
        )

    def _calc_valuation_score(self, pe_pct: float, pb_pct: float, pcf_pct: float, ps_pct: float) -> float:
        """计算估值综合评分 (-100 ~ +100)"""
        # PE历史分位 (40%)
        score = 0
        if pe_pct < 20:
            score += 40  # 严重低估
        elif pe_pct < 40:
            score += 20
        elif pe_pct > 80:
            score -= 40  # 严重高估
        elif pe_pct > 60:
            score -= 20

        # PB历史分位 (30%)
        if pb_pct < 20:
            score += 30
        elif pb_pct < 40:
            score += 15
        elif pb_pct > 80:
            score -= 30
        elif pb_pct > 60:
            score -= 15

        # PCF和PS各占15%
        if pcf_pct < 30:
            score += 15
        elif pcf_pct > 70:
            score -= 15

        if ps_pct < 30:
            score += 15
        elif ps_pct > 70:
            score -= 15

        return max(-100, min(100, score))

    def _get_valuation_state(self, pe: float, pb: float, pe_pct: float, pb_pct: float) -> str:
        """判断估值状态"""
        if pe <= 0 or pb <= 0:
            return "无法判断"

        # PE和PB都处于历史高位
        if pe_pct > 80 and pb_pct > 80:
            return "泡沫"
        elif pe_pct > 60 and pb_pct > 60:
            return "偏高"

        # PE和PB都处于历史低位
        if pe_pct < 20 and pb_pct < 20:
            return "偏低"
        elif pe_pct < 40 or pb_pct < 40:
            return "偏低"

        # PE极高或极低（绝对值判断）
        if pe > 100:
            return "偏高"
        if pe < 0:
            return "亏损"

        return "正常"

    def get_investment_signal(self, val: ValuationMetrics, price: float = 0) -> Dict:
        """
        获取估值投资信号
        """
        signals = []
        confidence = 0.5

        # Graham Number信号
        if val.graham_number > 0 and price > 0:
            if price < val.graham_number * 0.7:
                signals.append(("强烈买入", 0.8))
            elif price < val.graham_number:
                signals.append(("买入", 0.6))
            elif price > val.graham_number * 1.3:
                signals.append(("卖出", 0.6))

        # 历史分位信号
        if val.pe_percentile < 20:
            signals.append(("低估", 0.7))
        elif val.pe_percentile > 80:
            signals.append(("高估", 0.7))

        if val.pb_percentile < 20:
            signals.append(("低估", 0.6))
        elif val.pb_percentile > 80:
            signals.append(("高估", 0.6))

        # 安全边际信号
        if val.margin_of_safety > 30:
            signals.append(("安全边际高", 0.7))
        elif val.margin_of_safety < -20:
            signals.append(("风险高", 0.6))

        # 综合判断
        buy_signals = [s for s, _ in signals if "买" in s]
        sell_signals = [s for s, _ in signals if "卖" in s or "高估" in s or "风险" in s]

        if buy_signals and not sell_signals:
            action = "买入"
            confidence = min(0.9, len(buy_signals) * 0.25)
        elif sell_signals and not buy_signals:
            action = "卖出"
            confidence = min(0.9, len(sell_signals) * 0.25)
        elif buy_signals and sell_signals:
            if len(buy_signals) > len(sell_signals):
                action = "中性偏买入"
                confidence = 0.5
            else:
                action = "中性偏卖出"
                confidence = 0.5
        else:
            action = "观望"
            confidence = 0.5

        return {
            "action": action,
            "signals": signals,
            "confidence": round(confidence, 2),
            "val_score": val.val_score,
            "val_signal": val.val_signal,
            "valuation_state": val.valuation_state,
            "margin_of_safety": val.margin_of_safety
        }