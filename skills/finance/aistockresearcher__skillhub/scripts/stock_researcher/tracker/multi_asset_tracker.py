#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多资产持仓跟踪器
Multi-Asset Portfolio Tracker

扩展原PortfolioTracker，支持：
- 股票 (stock)
- 债券 (bond)
- 指数 (index)
- 基金 (fund)

每类资产有独立的跟踪逻辑和量化指标
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date, timedelta


class MultiAssetTracker:
    """
    多资产持仓跟踪器

    支持股票、债券、指数、基金四类资产的统一跟踪管理。
    每类资产独立存储，统一查询和报告。
    """

    ASSET_TYPES = {"stock", "bond", "index", "fund"}

    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[3] / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.portfolio_file = self.data_dir / "portfolio.json"
        self.history_dir = self.data_dir / "tracking_history"
        self.history_dir.mkdir(exist_ok=True)

        self.portfolio = self._load_portfolio()

    def _load_portfolio(self) -> Dict:
        """加载持仓数据"""
        if self.portfolio_file.exists():
            try:
                with open(self.portfolio_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "stocks": {},    # 股票持仓
            "bonds": {},     # 债券持仓
            "indices": {},   # 指数跟踪
            "funds": {},     # 基金持仓
            "alerts": [],
            "snapshots": {}  # 每日快照
        }

    def _save_portfolio(self):
        """保存持仓数据"""
        self.portfolio_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.portfolio_file, "w", encoding="utf-8") as f:
            json.dump(self.portfolio, f, ensure_ascii=False, indent=2)

    # ---- 添加/移除 ----

    def add_asset(self, asset_type: str, code: str, name: str = None,
                  cost: float = None, shares: float = None,
                  stop_loss: float = None, take_profit: float = None,
                  **extra) -> bool:
        """
        添加跟踪资产

        Args:
            asset_type: 资产类型 (stock/bond/index/fund)
            code: 代码
            name: 名称
            cost: 成本价
            shares: 持有份额
            stop_loss: 止损价
            take_profit: 止盈价
            **extra: 额外参数（如 bond_coupon, bond_maturity, index_weight等）
        """
        if asset_type not in self.ASSET_TYPES:
            print(f"不支持的资产类型: {asset_type}，支持: {self.ASSET_TYPES}")
            return False

        container = self.portfolio.get(f"{asset_type}s", {})
        container[code] = {
            "code": code,
            "name": name or code,
            "type": asset_type,
            "cost": cost,
            "shares": shares,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "added_date": datetime.now().strftime("%Y-%m-%d"),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "last_price": None,
            "last_change_pct": None,
            "alerts_triggered": [],
            **extra
        }
        self.portfolio[f"{asset_type}s"] = container
        self._save_portfolio()
        print(f"✅ 已添加 {asset_type}: {code} {name or ''}")
        return True

    def add_stock(self, code: str, name: str = None, cost: float = None,
                  shares: float = None, **kwargs) -> bool:
        """添加股票"""
        code = str(code).zfill(6)
        return self.add_asset("stock", code, name, cost, shares, **kwargs)

    def add_bond(self, code: str, name: str = None, cost: float = None,
                 shares: float = None, coupon: float = None,
                 maturity: str = None, bond_type: str = "可转债", **kwargs) -> bool:
        """
        添加债券

        Args:
            coupon: 票面利率 (%)
            maturity: 到期日 (YYYY-MM-DD)
            bond_type: 债券类型 (可转债/国债/企业债/城投债等)
        """
        extra = {"coupon": coupon, "maturity": maturity, "bond_type": bond_type}
        extra.update(kwargs)
        return self.add_asset("bond", code, name, cost, shares, **extra)

    def add_index(self, code: str, name: str = None,
                  weight: float = None, **kwargs) -> bool:
        """
        添加指数跟踪

        Args:
            weight: 基准权重 (%)
        """
        extra = {"weight": weight}
        extra.update(kwargs)
        return self.add_asset("index", code, name, cost=0, shares=0, **extra)

    def add_fund(self, code: str, name: str = None, cost: float = None,
                 shares: float = None, **kwargs) -> bool:
        """添加基金"""
        return self.remove_asset("fund", code) or True  # 先移除再添加，避免重复
        return self.add_asset("fund", code, name, cost, shares, **kwargs)

    def remove_asset(self, asset_type: str, code: str) -> bool:
        """移除跟踪资产"""
        container = self.portfolio.get(f"{asset_type}s", {})
        if code in container:
            del container[code]
            self._save_portfolio()
            print(f"🗑️ 已移除 {asset_type}: {code}")
            return True
        return False

    # ---- 查询 ----

    def get_assets(self, asset_type: str = None) -> List[Dict]:
        """获取跟踪资产列表"""
        if asset_type:
            return list(self.portfolio.get(f"{asset_type}s", {}).values())
        # 返回所有资产
        all_assets = []
        for at in self.ASSET_TYPES:
            all_assets.extend(self.portfolio.get(f"{at}s", {}).values())
        return all_assets

    def get_stocks(self) -> List[Dict]:
        return self.get_assets("stock")

    def get_bonds(self) -> List[Dict]:
        return self.get_assets("bond")

    def get_indices(self) -> List[Dict]:
        return self.get_assets("index")

    def get_funds(self) -> List[Dict]:
        return self.get_assets("fund")

    # ---- 更新 ----

    def update_price(self, asset_type: str, code: str, price: float, change_pct: float = None):
        """更新资产价格"""
        container = self.portfolio.get(f"{asset_type}s", {})
        if code in container:
            container[code]["last_price"] = price
            container[code]["last_change_pct"] = change_pct
            container[code]["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    def update_all_prices(self, price_data: Dict[str, Dict]):
        """
        批量更新价格

        Args:
            price_data: {asset_type:code: {price, change_pct, ...}}
        """
        for key, data in price_data.items():
            parts = key.split(":", 1)
            if len(parts) == 2:
                asset_type, code = parts
                self.update_price(asset_type, code,
                                  data.get("price", 0),
                                  data.get("change_pct"))
        self._save_portfolio()

    # ---- 警报 ----

    def check_alerts(self, asset_type: str, code: str, current_price: float,
                     extra_data: Dict = None) -> List[Dict]:
        """检查价格警报"""
        container = self.portfolio.get(f"{asset_type}s", {})
        if code not in container:
            return []

        asset = container[code]
        alerts = []

        # 止损检查
        stop_loss = asset.get("stop_loss")
        if stop_loss and current_price <= stop_loss:
            alerts.append({
                "type": "stop_loss", "asset_type": asset_type, "code": code,
                "name": asset.get("name", code),
                "message": f"触及止损价 {stop_loss:.4f}，当前价格 {current_price:.4f}",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "建议减仓或止损"
            })

        # 止盈检查
        take_profit = asset.get("take_profit")
        if take_profit and current_price >= take_profit:
            alerts.append({
                "type": "take_profit", "asset_type": asset_type, "code": code,
                "name": asset.get("name", code),
                "message": f"触及止盈价 {take_profit:.4f}，当前价格 {current_price:.4f}",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "action": "建议考虑获利了结"
            })

        # 成本价亏损检查
        cost = asset.get("cost")
        if cost and cost > 0:
            pnl_pct = (current_price - cost) / cost * 100
            if pnl_pct <= -10:
                alerts.append({
                    "type": "loss_warning", "asset_type": asset_type, "code": code,
                    "name": asset.get("name", code),
                    "message": f"亏损 {pnl_pct:.1f}%，成本 {cost:.4f}，现价 {current_price:.4f}",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "action": "注意风险"
                })

        # 债券特有: 到期提醒
        if asset_type == "bond":
            maturity = asset.get("maturity")
            if maturity:
                try:
                    mat_date = datetime.strptime(maturity, "%Y-%m-%d").date()
                    days_to_mat = (mat_date - date.today()).days
                    if 0 < days_to_mat <= 30:
                        alerts.append({
                            "type": "maturity_warning", "asset_type": "bond", "code": code,
                            "name": asset.get("name", code),
                            "message": f"距离到期仅剩 {days_to_mat} 天 ({maturity})",
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "action": "注意转股/赎回/到期处理"
                        })
                    elif days_to_mat <= 0:
                        alerts.append({
                            "type": "matured", "asset_type": "bond", "code": code,
                            "name": asset.get("name", code),
                            "message": f"已到期 ({maturity})",
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "action": "请处理到期/赎回"
                        })
                except ValueError:
                    pass

        if alerts:
            if "alerts_triggered" not in asset:
                asset["alerts_triggered"] = []
            asset["alerts_triggered"].extend(alerts)
            self._save_portfolio()

        return alerts

    # ---- 快照 ----

    def save_snapshot(self, analysis_data: Dict = None):
        """保存每日持仓快照"""
        today = date.today().strftime("%Y-%m-%d")
        snapshot = {
            "date": today,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "assets": {},
            "summary": {},
            "analysis": analysis_data
        }

        for asset_type in self.ASSET_TYPES:
            container = self.portfolio.get(f"{asset_type}s", {})
            if container:
                snapshot["assets"][asset_type] = dict(container)

        # 汇总
        snapshot["summary"] = self.get_summary()

        snapshot_file = self.history_dir / f"portfolio_{today}.json"
        with open(snapshot_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)

        self.portfolio["snapshots"][today] = str(snapshot_file)
        self._save_portfolio()
        return snapshot_file

    # ---- 汇总 ----

    def get_summary(self) -> Dict:
        """获取持仓汇总"""
        summary = {
            "total_assets": 0,
            "by_type": {},
            "total_cost": 0,
            "total_value": 0,
            "total_pnl": 0,
            "total_pnl_pct": 0,
            "assets": []
        }

        for asset_type in self.ASSET_TYPES:
            container = self.portfolio.get(f"{asset_type}s", {})
            if not container:
                continue

            type_cost = 0
            type_value = 0
            type_count = len(container)

            for code, asset in container.items():
                cost = asset.get("cost") or 0
                price = asset.get("last_price") or cost
                shares = asset.get("shares") or 0

                asset_cost = cost * shares
                asset_value = price * shares
                asset_pnl = asset_value - asset_cost if cost > 0 else 0

                type_cost += asset_cost
                type_value += asset_value

                summary["assets"].append({
                    "type": asset_type,
                    "code": code,
                    "name": asset.get("name", code),
                    "cost": cost,
                    "price": price,
                    "shares": shares,
                    "value": asset_value,
                    "pnl": asset_pnl,
                    "pnl_pct": asset_pnl / asset_cost * 100 if asset_cost > 0 else 0,
                    "last_change_pct": asset.get("last_change_pct")
                })

            type_pnl = type_value - type_cost
            summary["by_type"][asset_type] = {
                "count": type_count,
                "cost": type_cost,
                "value": type_value,
                "pnl": type_pnl,
                "pnl_pct": type_pnl / type_cost * 100 if type_cost > 0 else 0
            }

            summary["total_assets"] += type_count
            summary["total_cost"] += type_cost
            summary["total_value"] += type_value

        summary["total_pnl"] = summary["total_value"] - summary["total_cost"]
        if summary["total_cost"] > 0:
            summary["total_pnl_pct"] = summary["total_pnl"] / summary["total_cost"] * 100

        return summary

    def get_bond_quant_metrics(self, code: str) -> Optional[Dict]:
        """获取债券量化指标"""
        bond = self.portfolio.get("bonds", {}).get(code)
        if not bond:
            return None
        return {
            "code": code,
            "name": bond.get("name", ""),
            "coupon": bond.get("coupon"),
            "maturity": bond.get("maturity"),
            "bond_type": bond.get("bond_type", ""),
            "cost": bond.get("cost"),
            "last_price": bond.get("last_price"),
            # 其他量化指标由quantitative engine计算
        }

    def get_index_tracking_metrics(self, code: str) -> Optional[Dict]:
        """获取指数跟踪指标"""
        index = self.portfolio.get("indices", {}).get(code)
        if not index:
            return None
        return {
            "code": code,
            "name": index.get("name", ""),
            "weight": index.get("weight"),
            "last_price": index.get("last_price"),
            "last_change_pct": index.get("last_change_pct"),
            # 其他跟踪指标（跟踪误差、beta等）由quantitative engine计算
        }

    def get_all_alerts(self) -> List[Dict]:
        """获取所有资产的警报"""
        alerts = []
        for asset_type in self.ASSET_TYPES:
            for asset in self.portfolio.get(f"{asset_type}s", {}).values():
                alerts.extend(asset.get("alerts_triggered", []))
        return alerts

    def clear_alerts(self, asset_type: str = None, code: str = None):
        """清除警报"""
        if asset_type and code:
            container = self.portfolio.get(f"{asset_type}s", {})
            if code in container:
                container[code]["alerts_triggered"] = []
        elif asset_type:
            for asset in self.portfolio.get(f"{asset_type}s", {}).values():
                asset["alerts_triggered"] = []
        else:
            for at in self.ASSET_TYPES:
                for asset in self.portfolio.get(f"{at}s", {}).values():
                    asset["alerts_triggered"] = []
        self._save_portfolio()

    def get_portfolio_report(self) -> str:
        """生成持仓报告文本"""
        summary = self.get_summary()
        lines = [
            "=" * 50,
            "📊 持仓概览",
            "=" * 50,
            f"总资产数: {summary['total_assets']}",
            f"总成本: ¥{summary['total_cost']:,.2f}",
            f"总市值: ¥{summary['total_value']:,.2f}",
            f"总盈亏: ¥{summary['total_pnl']:,.2f} ({summary['total_pnl_pct']:+.2f}%)",
            ""
        ]

        for asset_type, type_data in summary.get("by_type", {}).items():
            if type_data["count"] == 0:
                continue
            type_names = {"stock": "股票", "bond": "债券", "index": "指数", "fund": "基金"}
            lines.append(f"【{type_names.get(asset_type, asset_type)}】{type_data['count']}只")
            lines.append(f"  成本: ¥{type_data['cost']:,.2f}  市值: ¥{type_data['value']:,.2f}  盈亏: ¥{type_data['pnl']:,.2f} ({type_data['pnl_pct']:+.2f}%)")
            lines.append("")

        # 明细
        lines.append("-" * 50)
        lines.append("持仓明细:")
        for a in summary.get("assets", []):
            emoji = "🟢" if (a.get("pnl", 0) >= 0) else "🔴"
            type_tag = {"stock": "📈", "bond": "📋", "index": "📊", "fund": "💰"}.get(a["type"], "")
            lines.append(f"  {type_tag} {a['code']} {a['name']} | 成本:{a['cost']:.4f} 现价:{a['price']:.4f} {emoji}盈亏:{a['pnl']:.2f}({a['pnl_pct']:+.2f}%)")

        return "\n".join(lines)
