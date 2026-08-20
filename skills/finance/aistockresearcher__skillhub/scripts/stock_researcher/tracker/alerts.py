#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
警报系统
Alert System
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date


class AlertSystem:
    """
    警报系统

    功能：
    - 定义警报规则
    - 触发警报条件
    - 记录和通知警报
    """

    # 警报类型
    ALERT_TYPES = {
        "price_breakout": "价格突破",
        "indicator_worse": "指标恶化",
        "money_outflow": "资金大幅流出",
        "stop_loss": "触及止损",
        "take_profit": "触及止盈",
        "trend_reversal": "趋势反转",
        "news_negative": "负面新闻",
        "rsis_overbought": "RSI超买",
        "rsis_oversold": "RSI超卖",
    }

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[3] / "data"
        self.data_dir = Path(data_dir)
        self.alerts_file = self.data_dir / "alerts_history.json"
        self.alerts = self._load_alerts()

    def _load_alerts(self) -> List[Dict]:
        """加载历史警报"""
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_alerts(self):
        """保存警报"""
        with open(self.alerts_file, "w", encoding="utf-8") as f:
            json.dump(self.alerts, f, ensure_ascii=False, indent=2)

    def create_alert(
        self,
        code: str,
        name: str,
        alert_type: str,
        message: str,
        current_value: float = None,
        threshold: float = None,
        action: str = None
    ) -> Dict:
        """
        创建警报

        Args:
            code: 股票代码
            name: 股票名称
            alert_type: 警报类型
            message: 警报消息
            current_value: 当前值
            threshold: 阈值
            action: 建议操作

        Returns:
            Dict: 警报对象
        """
        alert = {
            "id": len(self.alerts) + 1,
            "code": code,
            "name": name,
            "type": alert_type,
            "type_name": self.ALERT_TYPES.get(alert_type, alert_type),
            "message": message,
            "current_value": current_value,
            "threshold": threshold,
            "action": action or "请关注",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "date": date.today().strftime("%Y-%m-%d"),
            "processed": False
        }

        self.alerts.append(alert)
        self._save_alerts()

        return alert

    def check_price_breakout(self, code: str, name: str, current_price: float,
                             bb_upper: float, bb_lower: float, prev_price: float = None) -> Optional[Dict]:
        """
        检查价格突破

        Args:
            code: 股票代码
            name: 股票名称
            current_price: 当前价格
            bb_upper: 布林带上轨
            bb_lower: 布林带下轨
            prev_price: 前一价格

        Returns:
            Optional[Dict]: 警报或None
        """
        if current_price > bb_upper:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="price_breakout",
                message=f"价格突破布林带上轨，现价 {current_price:.2f} > 上轨 {bb_upper:.2f}",
                current_value=current_price,
                threshold=bb_upper,
                action="注意回调风险，可考虑减仓"
            )
        elif current_price < bb_lower:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="price_breakout",
                message=f"价格跌破布林带下轨，现价 {current_price:.2f} < 下轨 {bb_lower:.2f}",
                current_value=current_price,
                threshold=bb_lower,
                action="关注反弹机会，可考虑买入"
            )
        return None

    def check_rsi_alert(self, code: str, name: str, rsi: float, threshold: float = 70) -> Optional[Dict]:
        """
        检查RSI警报

        Args:
            code: 股票代码
            name: 股票名称
            rsi: RSI值
            threshold: 超买/超卖阈值（默认70）

        Returns:
            Optional[Dict]: 警报或None
        """
        if rsi > 80:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="rsis_overbought",
                message=f"RSI严重超买 {rsi:.0f}，注意回调风险",
                current_value=rsi,
                threshold=80,
                action="建议减仓或观望"
            )
        elif rsi > threshold:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="rsis_overbought",
                message=f"RSI超买 {rsi:.0f}",
                current_value=rsi,
                threshold=threshold,
                action="注意回调风险"
            )
        elif rsi < 20:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="rsis_oversold",
                message=f"RSI严重超卖 {rsi:.0f}，关注反弹机会",
                current_value=rsi,
                threshold=20,
                action="可关注买入机会"
            )
        elif rsi < 30:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="rsis_oversold",
                message=f"RSI超卖 {rsi:.0f}",
                current_value=rsi,
                threshold=30,
                action="关注反弹机会"
            )
        return None

    def check_money_outflow(self, code: str, name: str, main_net_flow: float,
                            mkt_cap: float, days: int = 3) -> Optional[Dict]:
        """
        检查资金大幅流出

        Args:
            code: 股票代码
            name: 股票名称
            main_net_flow: 主力净流入
            mkt_cap: 市值
            days: 连续流出天数

        Returns:
            Optional[Dict]: 警报或None
        """
        flow_ratio = main_net_flow / mkt_cap * 100 if mkt_cap > 0 else 0

        if flow_ratio < -1:  # 净流出超过市值1%
            return self.create_alert(
                code=code,
                name=name,
                alert_type="money_outflow",
                message=f"主力大幅净流出 {abs(main_net_flow):.0f}万，占比 {abs(flow_ratio):.2f}%",
                current_value=main_net_flow,
                threshold=-mkt_cap * 0.01,
                action="注意风险，可能继续下跌"
            )
        elif flow_ratio < -0.5:
            return self.create_alert(
                code=code,
                name=name,
                alert_type="money_outflow",
                message=f"主力净流出 {abs(main_net_flow):.0f}万",
                current_value=main_net_flow,
                threshold=-mkt_cap * 0.005,
                action="关注资金流向"
            )
        return None

    def check_trend_reversal(self, code: str, name: str, ma_status: str, prev_status: str) -> Optional[Dict]:
        """
        检查趋势反转

        Args:
            code: 股票代码
            name: 股票名称
            ma_status: 当前均线状态
            prev_status: 前一均线状态

        Returns:
            Optional[Dict]: 警报或None
        """
        if prev_status == "多头排列" and ma_status == "空头排列":
            return self.create_alert(
                code=code,
                name=name,
                alert_type="trend_reversal",
                message=f"均线状态从多头排列转为空头排列，趋势可能反转",
                current_value=0,
                threshold=0,
                action="注意减仓或止损"
            )
        elif prev_status == "空头排列" and ma_status == "多头排列":
            return self.create_alert(
                code=code,
                name=name,
                alert_type="trend_reversal",
                message=f"均线状态从空头排列转为多头排列，趋势转好",
                current_value=0,
                threshold=0,
                action="可考虑加仓"
            )
        return None

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """
        获取最近警报

        Args:
            hours: 最近几小时的警报

        Returns:
            List[Dict]: 警报列表
        """
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent = []
        for alert in reversed(self.alerts):
            alert_time = datetime.strptime(alert["time"], "%Y-%m-%d %H:%M")
            if alert_time >= cutoff_time:
                recent.append(alert)

        return recent

    def get_unprocessed_alerts(self) -> List[Dict]:
        """获取未处理的警报"""
        return [a for a in self.alerts if not a.get("processed", False)]

    def mark_processed(self, alert_id: int):
        """标记警报为已处理"""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["processed"] = True
                alert["processed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                break
        self._save_alerts()

    def clear_old_alerts(self, days: int = 30):
        """清除旧警报"""
        from datetime import timedelta
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        self.alerts = [a for a in self.alerts if a.get("date", "") >= cutoff_date]
        self._save_alerts()