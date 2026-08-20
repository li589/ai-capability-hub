#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金流向数据获取
Money Flow Data Fetching
"""

import time
from typing import Dict, List, Optional

from .market import MarketData


class MoneyFlowData:
    """
    资金流向分析

    数据来源：腾讯财经实时行情
    - main_net_flow: 主力净流入(万)
    - turnover: 换手率
    """

    def __init__(self):
        self.market = MarketData()

    def _fetch_em_main_flow(self, codes: List[str]) -> Dict[str, float]:
        """v8.0: 东财 push2 批量取主力净流入（f62，万元），失败返回空 dict（保持腾讯 0）。"""
        try:
            import json
            import urllib.request
            out: Dict[str, float] = {}
            for code in codes:
                mkt = "1" if code.startswith(("6", "5", "9")) else "0"
                url = (f"https://push2.eastmoney.com/api/qt/stock/get?invt=2&fltt=1"
                       f"&fields=f62,f184&secid={mkt}.{code}")
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                d = data.get("data") or {}
                if d.get("f62") is not None:
                    out[code] = float(d["f62"])  # 主力净流入（万元）
            return out
        except Exception:
            return {}

    def get_money_flow(self, codes: List[str]) -> Dict[str, Dict]:
        """
        获取资金流向数据

        Args:
            codes: 股票代码列表

        Returns:
            Dict[code, money_flow_data]
        """
        rt_data = self.market.fetch_realtime(codes)
        # v8.0: 腾讯行情无主力净流入 → 用东财 f62 补齐真实值（失败保持 0 + unavailable 标记）
        em_flow = self._fetch_em_main_flow(codes)

        result = {}
        for code, data in rt_data.items():
            main_net = em_flow.get(code, data.get("main_net_flow", 0))
            main_net = float(main_net or 0)
            mkt_cap = data.get("mkt_cap", 1) or 1
            turnover = data.get("turnover", 0)
            amount = data.get("amount", 0)  # 成交额(万)
            volume = data.get("volume", 0)   # 成交量

            # 计算净流入占比
            flow_ratio = main_net / mkt_cap * 100 if mkt_cap else 0

            # 资金评分
            score = 0
            if abs(flow_ratio) > 0.5:
                score = 20 if flow_ratio > 0 else -20
            elif abs(flow_ratio) > 0.1:
                score = 10 if flow_ratio > 0 else -10

            result[code] = {
                "main_net_flow": round(main_net, 2),
                "flow_ratio": round(flow_ratio, 4),
                "turnover": turnover,
                "amount": amount,
                "volume": volume,
                "score": score,
                "direction": "流入" if main_net > 0 else "流出" if main_net < 0 else "中性",
                "data_quality": "actual" if code in em_flow else "unavailable",
            }

        return result

    def analyze_money_flow_trend(self, code: str, days: int = 5) -> Dict:
        """
        分析资金流向趋势

        Args:
            code: 股票代码
            days: 分析天数

        Returns:
            Dict: 趋势分析结果
        """
        # 获取近期数据
        kline = self.market.fetch_history(code, days=30)  # 获取更多天数用于分析
        if not kline or not kline.get("dates"):
            return {}

        closes = kline.get("closes", [])
        if len(closes) < days:
            return {}

        # v8.0: 基于真实成交量 + 价格方向估算资金流（腾讯无逐日资金流接口），
        # 用量价配合的相对值替代此前的编造 `direction*(i+1)*1000`，并诚实标注 estimated。
        volumes = kline.get("volumes", [])
        daily_flows = []
        for i in range(1, min(len(closes), days + 1)):
            price_change = closes[i] - closes[i - 1] if i > 0 else 0
            vol = volumes[i] if i < len(volumes) else 0
            direction = 1 if price_change >= 0 else -1
            # 量价配合：放量上涨视为流入、放量下跌视为流出（相对值，无量纲）
            daily_flows.append(direction * vol * abs(price_change))

        # 汇总
        total_flow = sum(daily_flows)
        avg_flow = total_flow / len(daily_flows) if daily_flows else 0

        # 趋势判断
        if len(daily_flows) >= 3:
            recent = daily_flows[-3:]
            if sum(recent) > 0:
                trend = "加速流入"
            elif sum(recent) < 0:
                trend = "加速流出"
            else:
                trend = "平稳"
        else:
            trend = "数据不足"

        return {
            "total_flow": round(total_flow, 2),
            "avg_daily_flow": round(avg_flow, 2),
            "trend": trend,
            "recent_3days": [round(f, 2) for f in daily_flows[-3:]] if len(daily_flows) >= 3 else [],
            "quality": "estimated",  # v8.0: 诚实标注为估算（量价近似）
        }

    def get_sector_money_flow(self, sector_codes: Dict[str, List[str]]) -> Dict[str, Dict]:
        """
        获取板块资金流向

        Args:
            sector_codes: Dict[板块名, [股票代码列表]]

        Returns:
            Dict[板块名, money_flow_data]
        """
        result = {}

        for sector_name, codes in sector_codes.items():
            # 批量获取资金流向
            flows = self.get_money_flow(codes)

            # 汇总
            total_net_flow = sum(f.get("main_net_flow", 0) for f in flows.values())
            avg_turnover = sum(f.get("turnover", 0) for f in flows.values()) / len(flows) if flows else 0

            # 板块评分
            avg_flow = total_net_flow / len(codes) if codes else 0
            score = 20 if avg_flow > 1000 else (-20 if avg_flow < -1000 else 0)

            result[sector_name] = {
                "total_net_flow": round(total_net_flow, 2),
                "avg_turnover": round(avg_turnover, 2),
                "stock_count": len(codes),
                "score": score,
                "direction": "流入" if total_net_flow > 0 else "流出" if total_net_flow < 0 else "中性"
            }

            time.sleep(0.3)  # 避免请求过快

        return result