#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票监控器
Stock Monitor
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, date

from ..data.market import MarketData
from .portfolio import PortfolioTracker
from .alerts import AlertSystem


class StockMonitor:
    """
    股票监控器

    功能：
    - 每日监控跟踪股票
    - 检查警报触发条件
    - 生成监控报告
    """

    def __init__(self, data_dir: str = None):
        self.market = MarketData()
        self.portfolio = PortfolioTracker(data_dir)
        self.alerts = AlertSystem(data_dir)

    def daily_check(self) -> Dict:
        """
        执行每日检查

        Returns:
            Dict: 检查结果
        """
        tracked_stocks = self.portfolio.get_tracked_stocks()

        if not tracked_stocks:
            return {"status": "no_tracking", "message": "没有跟踪的股票"}

        results = {
            "date": date.today().strftime("%Y-%m-%d"),
            "checked": len(tracked_stocks),
            "alerts": [],
            "stocks": []
        }

        for stock in tracked_stocks:
            code = stock.get("code", "")
            name = stock.get("name", code)

            # 获取实时行情
            rt_data = self.market.fetch_realtime([code])
            if code not in rt_data:
                continue

            price_data = rt_data[code]
            current_price = price_data.get("price", 0)
            change_pct = price_data.get("change_pct", 0)

            # 更新持仓价格
            self.portfolio.update_stock_price(code, current_price, change_pct)

            # 获取技术数据用于警报检查
            kline = self.market.fetch_history(code, days=60)
            tech_data = {}
            if kline and kline.get("closes"):
                closes = kline["closes"]
                if len(closes) >= 20:
                    # 简单计算RSI
                    from ..core.technical import TechnicalAnalyzer
                    analyzer = TechnicalAnalyzer()
                    try:
                        tech = analyzer.analyze(code, closes)
                        tech_data = {
                            "rsi14": tech.rsi14,
                            "macd_hist": tech.macd_hist,
                            "bb_upper": tech.bb_upper,
                            "bb_lower": tech.bb_lower
                        }
                    except Exception:
                        pass

            # 检查警报
            stock_alerts = self.portfolio.check_alerts(code, current_price, tech_data)
            results["alerts"].extend(stock_alerts)

            # 额外检查
            if tech_data:
                # RSI警报
                rsi_alert = self.alerts.check_rsi_alert(code, name, tech_data.get("rsi14", 50))
                if rsi_alert:
                    results["alerts"].append(rsi_alert)

                # 价格突破警报
                breakout_alert = self.alerts.check_price_breakout(
                    code, name, current_price,
                    tech_data.get("bb_upper", 0),
                    tech_data.get("bb_lower", 0)
                )
                if breakout_alert:
                    results["alerts"].append(breakout_alert)

            # 记录股票状态
            results["stocks"].append({
                "code": code,
                "name": name,
                "price": current_price,
                "change_pct": change_pct
            })

            time.sleep(0.3)

        return results

    def get_monitor_summary(self) -> Dict:
        """
        获取监控汇总

        Returns:
            Dict: 汇总信息
        """
        tracking_summary = self.portfolio.get_tracking_summary()
        unprocessed_alerts = self.alerts.get_unprocessed_alerts()
        recent_alerts = self.alerts.get_recent_alerts(hours=24)

        return {
            "tracking": tracking_summary,
            "unprocessed_alerts": len(unprocessed_alerts),
            "recent_alerts": len(recent_alerts),
            "last_check": datetime.now().strftime("%Y-%m-%d %H:%M")
        }

    def run_and_report(self) -> str:
        """
        运行监控并生成报告

        Returns:
            str: 报告文本
        """
        print(f"\n{'='*60}")
        print(f"  股票监控检查 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        # 执行每日检查
        results = self.daily_check()

        report_lines = []
        report_lines.append(f"监控检查 {results.get('date', '')}")
        report_lines.append(f"检查股票数: {results.get('checked', 0)}")

        # 警报
        alerts = results.get("alerts", [])
        if alerts:
            report_lines.append(f"\n触发警报: {len(alerts)}条")
            for alert in alerts:
                report_lines.append(f"  [{alert.get('type_name', alert.get('type'))}] {alert.get('message', '')}")
                report_lines.append(f"    建议: {alert.get('action', '')}")
        else:
            report_lines.append("\n无警报触发")

        # 股票状态
        stocks = results.get("stocks", [])
        if stocks:
            report_lines.append(f"\n持仓状态:")
            for s in stocks:
                change = s.get("change_pct", 0)
                arrow = "▲" if change > 0 else "▼" if change < 0 else "-"
                report_lines.append(f"  {s.get('code')} {s.get('name')}: {s.get('price', 0):.2f} {arrow}{abs(change):.2f}%")

        report = "\n".join(report_lines)
        print(report)
        return report