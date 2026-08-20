#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
筛选理由生成器 (v6.0.0)
=======================
为筛选结果生成自然语言分析理由，引用具体数据源。
"""

from typing import Dict, List


class ReasoningGenerator:
    """筛选理由生成器

    为每只通过筛选的股票/基金/板块生成结构化理由，
    每条理由引用具体数据来源和阈值。
    """

    REASON_TEMPLATES_CN = {
        "pe_low": "市盈率 {pe:.1f}，低于行业平均水平，估值具有安全边际",
        "pe_high": "市盈率 {pe:.1f} 偏高，需关注盈利增长能否支撑估值",
        "pb_low": "市净率 {pb:.2f}，低于净资产，可能存在低估机会",
        "roe_high": "ROE {roe:.1f}%，连续保持高盈利能力，盈利质量扎实",
        "roe_improving": "ROE 呈上升趋势（从 {roe_prev:.1f}% → {roe:.1f}%），盈利改善明显",
        "debt_low": "资产负债率 {debt:.1f}%，财务杠杆较低，抗风险能力强",
        "debt_high": "资产负债率 {debt:.1f}% 偏高，需注意债务风险",
        "dividend_high": "股息率 {div_yield:.1f}%，持续为股东创造现金回报",
        "dividend_growth": "股息连续 {consecutive_years} 年增长，分红记录优秀",
        "growth_strong": "营收同比增长 {growth:.1f}%，增长动力强劲",
        "momentum_strong": "技术面多头排列，RSI={rsi:.0f}，短期动能充足",
        "money_inflow": "主力资金净流入 {flow:.0f}万，机构关注度提升",
        "sentiment_positive": "舆情偏正面（{sentiment_score:.0f}分），市场情绪乐观",
        "sentiment_negative": "舆情偏负面（{sentiment_score:.0f}分），短期需谨慎",
        "sector_leading": "所属 {industry} 板块资金持续流入，板块轮动有利",
        "sector_lagging": "所属 {industry} 板块资金流出，板块承压",
        "market_cap_large": "市值 {cap:.0f}亿，大盘蓝筹，流动性充足",
        "market_cap_small": "市值 {cap:.0f}亿，中小盘，成长弹性大",
        "margin_of_safety": "当前价格低于内在价值 {margin:.1f}%，安全边际充足",
        "risk_warning_volatility": "近期波动率偏高（ATR%={atr:.1f}%），短期波动风险较大",
    }

    def generate_stock_reasons(self, code: str, name: str, score: float,
                                matched: List[str], data: Dict = None) -> List[str]:
        """为筛选通过的股票生成理由"""
        data = data or {}
        reasons = []

        # 添加得分概况
        reasons.append(f"综合评分 {score:.1f}/100")

        # 添加已匹配的理由
        for reason in matched:
            reasons.append(reason)

        # 如果没有匹配到具体理由，生成基础理由
        if not matched:
            name_str = name or code
            reasons.append(f"{name_str} ({code}) 满足基本筛选条件")
            if score > 70:
                reasons.append("得分较高，多项条件表现优秀")
            elif score > 50:
                reasons.append("得分中等，部分条件达标")
            else:
                reasons.append("得分偏低，仅部分条件满足")

        return reasons

    def generate_fund_reasons(self, fund_code: str, fund_name: str,
                               score: float, dimensions: Dict = None) -> List[str]:
        """为筛选通过的基金生成理由"""
        dimensions = dimensions or {}
        reasons = [f"综合评分 {score:.1f}/100"]

        if dimensions.get("alpha", 0) > 2:
            reasons.append(f"Alpha={dimensions['alpha']:.1f}%，超额收益显著")
        if dimensions.get("sharpe", 0) > 0.8:
            reasons.append(f"Sharpe={dimensions['sharpe']:.2f}，风险调整收益优秀")
        if dimensions.get("sortino", 0) > 1.0:
            reasons.append(f"Sortino={dimensions['sortino']:.2f}，下行风险控制好")
        if dimensions.get("max_drawdown", 100) > -15:
            reasons.append(f"最大回撤 {dimensions['max_drawdown']:.1f}%，回撤控制良好")
        if dimensions.get("expense_ratio", 10) < 1.0:
            reasons.append(f"费率 {dimensions['expense_ratio']:.2f}%，成本较低")

        return reasons

    def generate_sector_reasons(self, sector_name: str, score: float,
                                 market: str = "cn", data: Dict = None) -> List[str]:
        """为板块生成理由"""
        data = data or {}
        return [
            f"板块 {sector_name} 综合评分 {score:.1f}/100",
            f"市场: {market}",
            f"代表股: {', '.join(data.get('representatives', [])[:4])}",
        ]
