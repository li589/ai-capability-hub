#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块分析
Sector Analysis
申万行业板块分析
"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from ..data.market import MarketData


@dataclass
class SectorResult:
    """板块分析结果"""
    name: str
    code: str  # 板块代码
    stocks: List[str]  # 成分股

    # 行情
    avg_price: float = 0
    avg_change_pct: float = 0
    up_count: int = 0
    down_count: int = 0

    # 资金
    total_net_flow: float = 0  # 主力净流入(万)
    avg_turnover: float = 0

    # 评分
    score: float = 0
    signal: str = "中性"  # 强于大盘/弱于大盘/中性
    rotation_signal: str = "中性"  # 流入/流出/中性

    # v9.0 深度板块增量字段（默认空/0，向后兼容；由 RPS/宽度/离散度分析器填充）
    market: str = "cn"
    data_mode: str = "proxy"      # proxy | full
    rps_score: float = 0.0        # 相对强度 RPS（>0 强于基准）
    breadth_pct: float = 0.0      # %成分股在 MA20 之上
    cohesion: str = ""            # 齐涨/齐跌/分化/中性


class SectorAnalyzer:
    """
    板块分析器

    分析申万一级行业板块
    """

    # 申万一级行业板块（简化版代表股）
    SECTOR_MAP = {
        "银行": ["600036", "601318", "600016", "601166", "600000"],
        "非银金融": ["601601", "600837", "601628", "600030", "000166"],
        "房地产": ["600048", "001979", "600383", "600606", "000002"],
        "医药生物": ["600276", "000538", "600196", "300760", "301560"],
        "食品饮料": ["600519", "000858", "600887", "002304", "603288"],
        "汽车": ["600104", "002594", "000625", "601127", "600741"],
        "电子": ["000725", "002241", "603986", "688041", "002475"],
        "计算机": ["000977", "002230", "601360", "000661", "300033"],
        "通信": ["600570", "000063", "002312", "300498", "603019"],
        "传媒": ["002027", "300058", "603444", "300124", "002558"],
        "军工": ["600760", "000768", "601989", "600893", "002013"],
        "新能源": ["300750", "002594", "600900", "601012", "002466"],
        "化工": ["600309", "000792", "002601", "600989", "601216"],
        "有色金属": ["600111", "000333", "601899", "002460", "600547"],
        "机械设备": ["601669", "600031", "002352", "600585", "300124"],
    }

    # v6.0: 港股行业映射（恒生行业分类）
    HK_SECTOR_MAP = {
        "科技": ["00700", "09988", "03690", "01810", "09618", "09999", "09888", "02015"],
        "金融": ["00005", "00388", "01299", "02318", "02628", "03968", "01398", "00939"],
        "地产建筑": ["00016", "00017", "00688", "01109", "00101", "02007", "06098"],
        "消费": ["02020", "02331", "09633", "02313", "00291", "01876", "06862"],
        "能源": ["00883", "00857", "00386", "02899", "01347", "01088"],
        "医药": ["02269", "01177", "01801", "06185", "02162", "01093", "06160"],
        "汽车": ["01211", "00175", "02015", "09863", "09866", "02333"],
        "电信": ["00941", "00728", "00762", "00788"],
        "公用事业": ["00002", "00003", "00006", "00066", "01038"],
        "原材料": ["02899", "02600", "03993", "01208", "01818"],
        "工业": ["00669", "02338", "01138", "02018"],
    }

    # v6.0: 美股行业映射（GICS 11 大行业）
    US_SECTOR_MAP = {
        "信息技术": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL", "CRM", "ADBE", "CSCO"],
        "金融": ["JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP"],
        "医疗保健": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY", "TMO", "ABT"],
        "可选消费": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "BKNG"],
        "必需消费": ["WMT", "PG", "KO", "PEP", "COST", "PM", "MDLZ"],
        "能源": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY"],
        "工业": ["CAT", "GE", "BA", "UPS", "RTX", "HON", "LMT", "DE"],
        "通信服务": ["GOOGL", "META", "NFLX", "DIS", "T", "VZ", "TMUS"],
        "公用事业": ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"],
        "房地产": ["PLD", "AMT", "CCI", "EQIX", "SPG", "PSA", "O", "WELL"],
        "原材料": ["LIN", "SHW", "APD", "ECL", "FCX", "NEM", "DOW", "NUE"],
    }

    # v6.0: 所有市场板块映射
    ALL_SECTOR_MAPS = {
        "cn": SECTOR_MAP,
        "hk": HK_SECTOR_MAP,
        "us": US_SECTOR_MAP,
    }

    def __init__(self):
        self.market = MarketData()

    def get_sector_map(self, market: str = "cn"):
        """获取指定市场的板块映射"""
        return self.ALL_SECTOR_MAPS.get(market, self.SECTOR_MAP)

    def get_all_sectors(self, market: str = "cn") -> List[str]:
        """获取指定市场的所有板块名称"""
        return list(self.get_sector_map(market).keys())

    def analyze_sector(self, sector_name: str, market: str = "cn") -> SectorResult:
        """
        分析单个板块

        Args:
            sector_name: 板块名称
            market: cn/hk/us（v9.0 修复：此前忽略该参数，恒用 A 股映射）

        Returns:
            SectorResult
        """
        sector_map = self.get_sector_map(market)
        codes = sector_map.get(sector_name, [])
        if not codes:
            return SectorResult(name=sector_name, code=sector_name, stocks=[], market=market)

        # 获取成分股行情
        rt_data = self.market.fetch_realtime(codes)

        if not rt_data:
            return SectorResult(name=sector_name, code=sector_name, stocks=codes, market=market)

        # 统计
        total_change = 0
        up_count = 0
        down_count = 0
        total_flow = 0
        total_turnover = 0

        for code, data in rt_data.items():
            price = data.get("price", 0)
            change = data.get("change_pct", 0)
            turnover = data.get("turnover", 0)
            net_flow = data.get("main_net_flow", 0)

            if price > 0:
                total_change += change
                if change > 0:
                    up_count += 1
                elif change < 0:
                    down_count += 1

            total_flow += net_flow
            total_turnover += turnover

        n = len(rt_data)
        avg_change = total_change / n if n > 0 else 0
        avg_turnover = total_turnover / n if n > 0 else 0

        # 板块评分
        score = 0
        if avg_change > 2:
            score = 20
        elif avg_change > 1:
            score = 10
        elif avg_change < -2:
            score = -20
        elif avg_change < -1:
            score = -10

        # 资金流向评分
        if total_flow > 50000:
            score += 10
        elif total_flow < -50000:
            score -= 10

        signal = "强于大盘" if score > 10 else ("弱于大盘" if score < -10 else "中性")

        return SectorResult(
            name=sector_name,
            code=sector_name,
            stocks=codes,
            market=market,
            avg_price=sum(d.get("price", 0) for d in rt_data.values()) / n if n > 0 else 0,
            avg_change_pct=round(avg_change, 2),
            up_count=up_count,
            down_count=down_count,
            total_net_flow=round(total_flow, 2),
            avg_turnover=round(avg_turnover, 2),
            score=round(score, 1),
            signal=signal,
            rotation_signal="流入" if total_flow > 0 else "流出" if total_flow < 0 else "中性"
        )

    def analyze_all_sectors(self, market: str = "cn") -> List[SectorResult]:
        """
        分析所有板块

        Args:
            market: cn/hk/us（v9.0 修复：此前恒用 A 股）

        Returns:
            List[SectorResult]
        """
        results = []
        for sector_name in self.get_sector_map(market).keys():
            result = self.analyze_sector(sector_name, market=market)
            results.append(result)
            time.sleep(0.3)
        return results

    def get_sector_ranking(self, market: str = "cn") -> List[SectorResult]:
        """
        获取板块强弱排名

        Args:
            market: cn/hk/us（v9.0 修复：此前恒用 A 股）

        Returns:
            List[SectorResult]: 按评分降序
        """
        results = self.analyze_all_sectors(market=market)
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def get_rotation_signal(self, market: str = "cn") -> Dict:
        """
        获取板块轮动信号

        Args:
            market: cn/hk/us（v9.0：支持多市场）

        Returns:
            Dict: 轮动分析结果
        """
        results = self.get_sector_ranking(market=market)

        # 资金流入最多的板块
        inflow_sectors = sorted(results, key=lambda x: x.total_net_flow, reverse=True)

        # 涨幅最大的板块
        up_sectors = sorted(results, key=lambda x: x.avg_change_pct, reverse=True)

        # 轮动判断
        rotation = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M"),
            "rankings": [
                {
                    "name": r.name,
                    "score": r.score,
                    "avg_change": r.avg_change_pct,
                    "net_flow": r.total_net_flow,
                    "signal": r.signal,
                    "rotation": r.rotation_signal
                }
                for r in results[:10]
            ],
            "top_inflow": [s.name for s in inflow_sectors[:3] if s.total_net_flow > 0],
            "top_up": [s.name for s in up_sectors[:3] if s.avg_change_pct > 0],
            "bottom_down": [s.name for s in results[-3:] if s.avg_change_pct < 0]
        }

        return rotation

    def print_analysis(self, results: List[SectorResult] = None):
        """打印板块分析结果"""
        if results is None:
            results = self.get_sector_ranking()

        print(f"\n{'='*80}")
        print(f"  板块分析报告  {time.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*80}")
        print(f"{'板块':<10} {'平均涨跌':>8} {'上涨家数':>8} {'下跌家数':>8} {'主力净流入':>12} {'信号':<10} {'轮动'}")
        print(f"{'-'*80}")

        for r in results:
            arrow = "▲" if r.avg_change_pct > 0 else "▼" if r.avg_change_pct < 0 else "-"
            flow_arrow = "↑" if r.total_net_flow > 0 else "↓" if r.total_net_flow < 0 else "-"
            print(f"{r.name:<10} {arrow}{abs(r.avg_change_pct):>6.1f}% {r.up_count:>6} {r.down_count:>8} {flow_arrow}{abs(r.total_net_flow):>10.0f}万 {r.signal:<10} {r.rotation_signal}")

        print(f"{'='*80}")

        # 轮动信号
        inflow = [r.name for r in results[:5] if r.total_net_flow > 10000]
        outflow = [r.name for r in results[-3:] if r.total_net_flow < -5000]

        if inflow:
            print(f"资金流入板块: {', '.join(inflow)}")
        if outflow:
            print(f"资金流出板块: {', '.join(outflow)}")


# 便捷函数
def analyze_sector(sector_name: str) -> SectorResult:
    """分析单个板块"""
    analyzer = SectorAnalyzer()
    return analyzer.analyze_sector(sector_name)


def get_sector_rankings() -> List[SectorResult]:
    """获取板块排名"""
    analyzer = SectorAnalyzer()
    return analyzer.get_sector_ranking()


def get_rotation_signal() -> Dict:
    """获取轮动信号"""
    analyzer = SectorAnalyzer()
    return analyzer.get_rotation_signal()