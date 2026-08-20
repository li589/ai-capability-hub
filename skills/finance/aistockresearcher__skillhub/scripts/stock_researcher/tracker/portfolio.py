#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓跟踪模块
Portfolio Tracker
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date


class PortfolioTracker:
    """
    持仓跟踪器

    功能：
    - 跟踪用户持仓股票
    - 记录每次分析结果
    - 监控价格/指标变化
    - 触发提醒
    """

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[3] / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.tracking_file = self.data_dir / "stock_tracking.json"
        self.history_dir = self.data_dir / "tracking_history"
        self.history_dir.mkdir(exist_ok=True)

        self.tracked_stocks = self._load_tracking()

    def _load_tracking(self) -> Dict:
        """加载跟踪数据"""
        if self.tracking_file.exists():
            try:
                with open(self.tracking_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"stocks": {}, "alerts": []}

    def _save_tracking(self):
        """保存跟踪数据"""
        with open(self.tracking_file, "w", encoding="utf-8") as f:
            json.dump(self.tracked_stocks, f, ensure_ascii=False, indent=2)

    def add_stock(self, code: str, name: str = None, cost: float = None,
                  shares: float = None, stop_loss: float = None, take_profit: float = None) -> bool:
        """
        添加跟踪股票

        Args:
            code: 股票代码
            name: 股票名称
            cost: 持仓成本
            shares: 持仓数量
            stop_loss: 止损价
            take_profit: 止盈价

        Returns:
            bool: 是否成功
        """
        code = str(code).zfill(6)

        self.tracked_stocks["stocks"][code] = {
            "code": code,
            "name": name or code,
            "cost": cost,
            "shares": shares,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "last_price": None,
            "last_change_pct": None,
            "alerts_triggered": []
        }

        self._save_tracking()
        print(f"[跟踪] 已添加 {code} {name or ''}")
        return True

    def remove_stock(self, code: str) -> bool:
        """移除跟踪股票"""
        code = str(code).zfill(6)
        if code in self.tracked_stocks["stocks"]:
            del self.tracked_stocks["stocks"][code]
            self._save_tracking()
            print(f"[跟踪] 已移除 {code}")
            return True
        return False

    def get_tracked_stocks(self) -> List[Dict]:
        """获取所有跟踪股票"""
        return list(self.tracked_stocks["stocks"].values())

    def update_stock_price(self, code: str, price: float, change_pct: float = None):
        """
        更新股票价格

        Args:
            code: 股票代码
            price: 当前价格
            change_pct: 涨跌幅
        """
        code = str(code).zfill(6)
        if code in self.tracked_stocks["stocks"]:
            self.tracked_stocks["stocks"][code]["last_price"] = price
            self.tracked_stocks["stocks"][code]["last_change_pct"] = change_pct
            self.tracked_stocks["stocks"][code]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    def check_alerts(self, code: str, current_price: float, tech_data: Dict = None) -> List[Dict]:
        """
        检查是否触发警报

        Args:
            code: 股票代码
            current_price: 当前价格
            tech_data: 技术分析数据

        Returns:
            List[Dict]: 触发的警报列表
        """
        code = str(code).zfill(6)
        if code not in self.tracked_stocks["stocks"]:
            return []

        alerts = []
        stock = self.tracked_stocks["stocks"][code]

        # 检查止损
        stop_loss = stock.get("stop_loss")
        if stop_loss and current_price <= stop_loss:
            alerts.append({
                "type": "stop_loss",
                "code": code,
                "name": stock.get("name", code),
                "message": f"触及止损价 {stop_loss:.2f}，当前价格 {current_price:.2f}",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "建议减仓或止损"
            })

        # 检查止盈
        take_profit = stock.get("take_profit")
        if take_profit and current_price >= take_profit:
            alerts.append({
                "type": "take_profit",
                "code": code,
                "name": stock.get("name", code),
                "message": f"触及止盈价 {take_profit:.2f}，当前价格 {current_price:.2f}",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "建议考虑获利了结"
            })

        # 检查成本价止损（下跌10%）
        cost = stock.get("cost")
        if cost:
            loss_pct = (current_price - cost) / cost * 100
            if loss_pct <= -10:
                alerts.append({
                    "type": "loss_warning",
                    "code": code,
                    "name": stock.get("name", code),
                    "message": f"亏损 {loss_pct:.1f}%，成本价 {cost:.2f}，当前价格 {current_price:.2f}",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "注意风险，考虑止损"
                })
            elif loss_pct >= 20:
                alerts.append({
                    "type": "profit_warning",
                    "code": code,
                    "name": stock.get("name", code),
                    "message": f"盈利 {loss_pct:.1f}%，成本价 {cost:.2f}，当前价格 {current_price:.2f}",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "注意保护利润"
                })

        # 检查技术信号恶化
        if tech_data:
            rsi = tech_data.get("rsi14", 50)
            if rsi > 80:
                alerts.append({
                    "type": "overbought",
                    "code": code,
                    "name": stock.get("name", code),
                    "message": f"RSI超买 {rsi:.0f}",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "注意回调风险"
                })
            elif rsi < 20:
                alerts.append({
                    "type": "oversold",
                    "code": code,
                    "name": stock.get("name", code),
                    "message": f"RSI超卖 {rsi:.0f}",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "关注反弹机会"
                })

        # 保存警报
        if alerts:
            if "alerts_triggered" not in stock:
                stock["alerts_triggered"] = []
            stock["alerts_triggered"].extend(alerts)
            self._save_tracking()

        return alerts

    def get_all_alerts(self) -> List[Dict]:
        """获取所有未处理的警报"""
        alerts = []
        for stock in self.tracked_stocks["stocks"].values():
            alerts.extend(stock.get("alerts_triggered", []))
        return alerts

    def clear_alerts(self, code: str = None):
        """清除警报"""
        if code:
            code = str(code).zfill(6)
            if code in self.tracked_stocks["stocks"]:
                self.tracked_stocks["stocks"][code]["alerts_triggered"] = []
        else:
            for stock in self.tracked_stocks["stocks"].values():
                stock["alerts_triggered"] = []
        self._save_tracking()

    def save_snapshot(self, code: str, analysis_data: Dict):
        """
        保存分析快照

        Args:
            code: 股票代码
            analysis_data: 分析数据
        """
        code = str(code).zfill(6)
        today = date.today().strftime("%Y-%m-%d")
        snapshot_file = self.history_dir / f"{code}_{today}.json"

        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump({
                "code": code,
                "date": today,
                "analysis": analysis_data
            }, f, ensure_ascii=False, indent=2)

    def get_tracking_summary(self) -> Dict:
        """获取跟踪汇总"""
        stocks = self.tracked_stocks["stocks"]
        total = len(stocks)

        if total == 0:
            return {"total": 0, "stocks": []}

        # 统计
        total_cost = sum(s.get("cost", 0) or 0 for s in stocks.values())
        total_value = sum(s.get("last_price", 0) or 0 for s in stocks.values())

        summary = {
            "total": total,
            "total_cost": total_cost,
            "total_value": total_value,
            "profit_loss": total_value - total_cost,
            "profit_loss_pct": (total_value - total_cost) / total_cost * 100 if total_cost > 0 else 0,
            "stocks": []
        }

        for code, stock in stocks.items():
            cost = stock.get("cost", 0) or 0
            price = stock.get("last_price", 0) or 0
            shares = stock.get("shares", 0) or 0
            value = price * shares
            pnl = value - cost * shares if cost > 0 else 0

            summary["stocks"].append({
                "code": code,
                "name": stock.get("name", code),
                "cost": cost,
                "price": price,
                "shares": shares,
                "value": value,
                "pnl": pnl,
                "pnl_pct": pnl / (cost * shares) * 100 if cost > 0 and shares > 0 else 0
            })

        return summary