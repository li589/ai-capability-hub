#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块轮动分析
Sector Rotation Analysis
"""

from typing import Dict, List, Optional
from .sectors import SectorAnalyzer, SectorResult


class SectorRotation:
    """
    板块轮动分析

    功能：
    - 识别当前强势板块
    - 预测板块轮动方向
    - 提供板块配置建议
    """

    def __init__(self):
        self.sector_analyzer = SectorAnalyzer()

    def identify_leading_sector(self, sectors: List[SectorResult]) -> List[SectorResult]:
        """
        识别领先板块

        Args:
            sectors: 板块分析结果列表

        Returns:
            List[SectorResult]: 领先板块（按评分降序）
        """
        # 筛选条件：
        # 1. 涨幅大于平均
        # 2. 资金净流入
        # 3. 强于大盘信号

        leading = []
        for s in sectors:
            if s.avg_change_pct > 0 and s.total_net_flow > 0 and s.signal == "强于大盘":
                leading.append(s)

        leading.sort(key=lambda x: (x.avg_change_pct, x.total_net_flow), reverse=True)
        return leading

    def predict_rotation_direction(self, sectors: List[SectorResult]) -> Dict:
        """
        预测板块轮动方向

        Args:
            sectors: 板块分析结果列表

        Returns:
            Dict: 轮动预测
        """
        # 分析资金流向
        inflow_sectors = [s for s in sectors if s.total_net_flow > 0]
        outflow_sectors = [s for s in sectors if s.total_net_flow < 0]

        # 计算平均资金流向
        avg_flow = sum(s.total_net_flow for s in sectors) / len(sectors) if sectors else 0

        # 轮动方向判断
        if len(inflow_sectors) > len(outflow_sectors) * 2:
            direction = "资金分散布局，多板块轮动"
        elif len(outflow_sectors) > len(inflow_sectors) * 2:
            direction = "资金集中流出，市场谨慎"
        elif avg_flow > 10000:
            direction = "资金整体流入，市场活跃"
        elif avg_flow < -10000:
            direction = "资金整体流出，观望为主"
        else:
            direction = "资金博弈，板块分化"

        # 热门板块
        hot_sectors = [s.name for s in sectors[:5] if s.avg_change_pct > 1]
        cold_sectors = [s.name for s in sectors[-3:] if s.avg_change_pct < -1]

        return {
            "direction": direction,
            "hot_sectors": hot_sectors,
            "cold_sectors": cold_sectors,
            "avg_net_flow": round(avg_flow, 2),
            "inflow_count": len(inflow_sectors),
            "outflow_count": len(outflow_sectors),
            "recommendation": self._generate_recommendation(sectors)
        }

    def _generate_recommendation(self, sectors: List[SectorResult]) -> Dict:
        """生成板块配置建议"""
        # 强势买入
        strong_buy = [s.name for s in sectors[:3] if s.score > 15 and s.avg_change_pct > 1.5]

        # 观望
        neutral = [s.name for s in sectors[3:7] if s.score > -10]

        # 回避
        avoid = [s.name for s in sectors[-3:] if s.score < -15 and s.avg_change_pct < -1]

        return {
            "strong_buy": strong_buy,
            "neutral": neutral,
            "avoid": avoid
        }

    def get_rotation_opportunities(self) -> List[Dict]:
        """
        获取轮动机会

        Returns:
            List[Dict]: 轮动机会列表
        """
        sectors = self.sector_analyzer.get_sector_ranking()
        leading = self.identify_leading_sector(sectors)
        prediction = self.predict_rotation_direction(sectors)

        opportunities = []

        for sector in leading[:3]:
            opportunities.append({
                "sector": sector.name,
                "type": "强势板块",
                "reason": f"涨幅{sector.avg_change_pct:.1f}%，资金净流入{sector.total_net_flow:.0f}万",
                "action": "可考虑介入，注意止损"
            })

        # 超跌反弹机会
        oversold = [s for s in sectors if s.avg_change_pct < -2 and s.total_net_flow > 0]
        for sector in oversold[:2]:
            opportunities.append({
                "sector": sector.name,
                "type": "超跌反弹",
                "reason": f"跌幅{sector.avg_change_pct:.1f}%，但有资金流入",
                "action": "关注反弹机会，设置止损"
            })

        return opportunities

    def print_rotation_report(self):
        """打印轮动报告"""
        sectors = self.sector_analyzer.get_sector_ranking()
        prediction = self.predict_rotation_direction(sectors)
        opportunities = self.get_rotation_opportunities()

        print(f"\n{'='*70}")
        print(f"  板块轮动报告  {__import__('time').strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}")

        print(f"\n轮动方向: {prediction['direction']}")
        print(f"平均资金流向: {prediction['avg_net_flow']:.0f}万")
        print(f"流入板块数: {prediction['inflow_count']}, 流出板块数: {prediction['outflow_count']}")

        if prediction['hot_sectors']:
            print(f"\n热门板块: {', '.join(prediction['hot_sectors'])}")
        if prediction['cold_sectors']:
            print(f"冷门板块: {', '.join(prediction['cold_sectors'])}")

        if opportunities:
            print(f"\n轮动机会:")
            for i, op in enumerate(opportunities, 1):
                print(f"  {i}. {op['sector']} ({op['type']})")
                print(f"     原因: {op['reason']}")
                print(f"     建议: {op['action']}")

        rec = prediction['recommendation']
        if rec['strong_buy']:
            print(f"\n强势板块: {', '.join(rec['strong_buy'])}")
        if rec['avoid']:
            print(f"回避板块: {', '.join(rec['avoid'])}")

        print(f"{'='*70}")