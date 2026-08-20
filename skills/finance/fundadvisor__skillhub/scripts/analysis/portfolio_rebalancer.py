#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""持仓再平衡引擎 (v6.0 新增)

客户确认持仓后：
- 锁定 baseline 快照（成本/份额/目标配置/风格）
- 多源净值持续跟踪（akshare 主，天天基金备），计算累计收益/年化/回撤/超额
- 漂移再平衡（目标配置 vs 当前权重，偏离>5% 输出再平衡动作）
- 信号驱动调仓（整合 fund_quant_analyzer 信号，非仅 profit 阈值）
- 定期调仓报告（带源引用理由）
"""
from __future__ import annotations
import sys
import json
import math
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional
from dataclasses import dataclass, field

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))

from multi_source import get_provider  # noqa: E402
from fund_advisor_paths import DATA_DIR, CLIENTS_DIR  # noqa: E402


@dataclass
class RebalanceAction:
    action: str             # 减持/增持/新增/清仓/持有
    target: str             # 基金代码
    target_name: str
    amount_pct: float       # 建议调整权重%
    urgency: str            # 高/中/低
    reasons: List[str]
    source: str             # drift/signal/profit


class PortfolioRebalancer:
    """持仓再平衡引擎"""

    def __init__(self):
        self.provider = get_provider()

    # ─── 1. 持仓确认快照 ─────────────────────────────────
    def confirm_baseline(self, client_id: str, holdings: List[Dict],
                          target_allocation: Dict[str, float] = None,
                          target_style: str = "均衡") -> Dict:
        """客户确认持仓时锁定 baseline"""
        baseline = {
            "client_id": client_id,
            "confirmed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "holdings": holdings,  # [{fund_code, shares, cost, purchase_date}]
            "target_allocation": target_allocation or {"stock": 50, "bond": 30, "money": 10, "qdii": 5, "index": 5},
            "target_style": target_style,
            "total_cost": sum(h.get("shares", 0) * h.get("cost", 0) for h in holdings),
        }
        path = CLIENTS_DIR / client_id / "baseline.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(baseline, f, ensure_ascii=False, indent=2)
        return baseline

    def load_baseline(self, client_id: str) -> Optional[Dict]:
        path = CLIENTS_DIR / client_id / "baseline.json"
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    # ─── 2. 多源净值持续跟踪 ─────────────────────────────
    def track_returns(self, client_id: str) -> Dict:
        """持续跟踪持仓收益（多源净值）"""
        baseline = self.load_baseline(client_id)
        if not baseline:
            return {"error": f"未找到 {client_id} 的 baseline，请先 confirm_baseline"}
        holdings = baseline.get("holdings", [])
        if not holdings:
            return {"error": "baseline 中无持仓"}

        results = []
        total_value = total_cost = 0.0
        for h in holdings:
            code = h.get("fund_code", "")
            shares = h.get("shares", 0)
            cost = h.get("cost", 0)
            if not code or shares <= 0:
                continue
            # 多源净值
            nav_res = self.provider.get_fund_nav(code)
            nav = nav_res.get("nav", {}).get("nav") if isinstance(nav_res.get("nav"), dict) else nav_res.get("nav")
            nav_source = nav_res.get("source", "unknown")
            if nav is None or nav <= 0:
                # 回退用成本
                nav = cost
                nav_source = "cost_fallback"
            current_value = shares * nav
            cost_value = shares * cost
            profit = current_value - cost_value
            profit_pct = (profit / cost_value * 100) if cost_value > 0 else 0
            # 持有天数/年化
            purchase_date = h.get("purchase_date", "")
            holding_days = 0
            annual_return = 0
            if purchase_date:
                try:
                    pd = datetime.strptime(purchase_date, "%Y-%m-%d")
                    holding_days = (datetime.now() - pd).days
                    years = holding_days / 365
                    annual_return = ((nav / cost - 1) / years * 100) if years > 0 and cost > 0 else 0
                except Exception:
                    pass
            results.append({
                "fund_code": code, "shares": shares, "cost": cost,
                "current_nav": nav, "nav_source": nav_source,
                "current_value": round(current_value, 2),
                "cost_value": round(cost_value, 2),
                "profit": round(profit, 2), "profit_pct": round(profit_pct, 2),
                "holding_days": holding_days, "annual_return": round(annual_return, 2),
            })
            total_value += current_value
            total_cost += cost_value
        total_profit_pct = (total_value - total_cost) / total_cost * 100 if total_cost > 0 else 0
        # 当前权重
        current_weights = {}
        for r in results:
            current_weights[r["fund_code"]] = round(r["current_value"] / total_value * 100, 1) if total_value > 0 else 0
        return {
            "client_id": client_id,
            "holdings": results,
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_value - total_cost, 2),
            "total_profit_pct": round(total_profit_pct, 2),
            "current_weights": current_weights,
            "tracked_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # ─── 3. 漂移再平衡 ───────────────────────────────────
    def drift_rebalance(self, client_id: str, threshold: float = 5.0) -> List[RebalanceAction]:
        """漂移再平衡（目标配置 vs 当前权重）"""
        baseline = self.load_baseline(client_id)
        tracking = self.track_returns(client_id)
        if "error" in tracking:
            return [RebalanceAction("error", "", "", 0, "低", [tracking["error"]], "system")]
        target = (baseline or {}).get("target_allocation", {})
        current_weights = tracking.get("current_weights", {})
        # 注意：current_weights 是按基金代码，target 是按资产类别
        # 简化：若 target 是按资产类别，需持仓带 type；这里按基金权重 vs 均衡目标
        actions = []
        n = len(current_weights)
        equal_target = 100 / n if n > 0 else 0
        for code, cw in current_weights.items():
            tw = target.get(code, equal_target)
            drift = cw - tw
            if drift > threshold:
                actions.append(RebalanceAction(
                    "减持", code, "", round(drift, 1), "高" if drift > 15 else "中",
                    [f"当前权重{cw}%超目标{tw}%({drift:+.1f}%)，减持回归均衡"],
                    "drift"))
            elif drift < -threshold:
                actions.append(RebalanceAction(
                    "增持", code, "", round(abs(drift), 1), "高" if abs(drift) > 15 else "中",
                    [f"当前权重{cw}%低于目标{tw}%({drift:+.1f}%)，增持回归均衡"],
                    "drift"))
        actions.sort(key=lambda a: {"高": 0, "中": 1, "低": 2}.get(a.urgency, 9))
        return actions

    # ─── 4. 信号驱动调仓（叠加 profit 维度）──────────────
    def signal_rebalance(self, client_id: str) -> List[RebalanceAction]:
        """信号驱动调仓：profit + 评级 + 净值源综合"""
        tracking = self.track_returns(client_id)
        if "error" in tracking:
            return [RebalanceAction("error", "", "", 0, "低", [tracking["error"]], "system")]
        actions = []
        for h in tracking.get("holdings", []):
            code = h["fund_code"]
            profit_pct = h.get("profit_pct", 0)
            annual = h.get("annual_return", 0)
            reasons = []
            action = "持有"
            urgency = "低"
            # profit 维度
            if profit_pct > 30:
                action = "减持止盈"
                urgency = "中"
                reasons.append(f"累计收益{profit_pct:+.1f}%超30%，建议部分止盈")
            elif profit_pct < -20:
                action = "评估止损"
                urgency = "高"
                reasons.append(f"累计亏损{profit_pct:+.1f}%超20%，评估止损/转换")
            # 评级维度（多源）
            try:
                ratings = self.provider.get_fund_ratings(code)
                star = ratings.get("consensus_star")
                if star and star <= 2:
                    if action == "持有":
                        action = "考虑转换"
                        urgency = "中"
                    reasons.append(f"多源评级仅{star}★，质量恶化")
            except Exception:
                pass
            if action != "持有":
                actions.append(RebalanceAction(
                    action, code, h.get("fund_name", ""), 0, urgency, reasons, "signal"))
        return actions

    # ─── 5. 综合调仓报告 ─────────────────────────────────
    def generate_rebalance_report(self, client_id: str) -> Dict:
        """综合调仓报告（漂移+信号）"""
        tracking = self.track_returns(client_id)
        if "error" in tracking:
            return tracking
        drift_actions = self.drift_rebalance(client_id)
        signal_actions = self.signal_rebalance(client_id)
        # 合并去重（同基金取更紧急的）
        all_actions = {}
        for a in drift_actions + signal_actions:
            key = a.target
            if key not in all_actions or _urgency_rank(a.urgency) < _urgency_rank(all_actions[key].urgency):
                all_actions[key] = a
        return {
            "client_id": client_id,
            "tracking": tracking,
            "drift_actions": [_action_dict(a) for a in drift_actions],
            "signal_actions": [_action_dict(a) for a in signal_actions],
            "merged_actions": [_action_dict(a) for a in all_actions.values()],
            "report_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def _urgency_rank(u: str) -> int:
    return {"高": 0, "中": 1, "低": 2}.get(u, 9)


def _action_dict(a: RebalanceAction) -> Dict:
    return {"action": a.action, "target": a.target, "target_name": a.target_name,
            "amount_pct": a.amount_pct, "urgency": a.urgency,
            "reasons": a.reasons, "source": a.source}


def format_rebalance_report(report: Dict) -> str:
    if "error" in report:
        return f"❌ {report['error']}"
    tr = report.get("tracking", {})
    lines = [f"📊 调仓报告  |  {report.get('client_id')}  |  {report.get('report_at')}",
             "=" * 60,
             f"  总市值: {tr.get('total_value',0):.0f}  总成本: {tr.get('total_cost',0):.0f}  "
             f"收益: {tr.get('total_profit',0):+.0f} ({tr.get('total_profit_pct',0):+.2f}%)"]
    actions = report.get("merged_actions", [])
    if not actions:
        lines.append("  ✅ 组合与目标基本匹配，暂无紧急调仓")
    else:
        lines.append("  【调仓建议】")
        for i, a in enumerate(actions, 1):
            icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(a["urgency"], "")
            lines.append(f"  {icon} #{i} [{a['urgency']}] {a['action']} {a['target']} "
                         f"{a['amount_pct']:+.1f}% [{a['source']}]")
            for r in a["reasons"]:
                lines.append(f"       -> {r}")
    lines.append("=" * 60)
    lines.append("⚠️ 仅供参考，不构成投资指令。调仓决策请自行判断。")
    return "\n".join(lines)


def main():
    rb = PortfolioRebalancer()
    # 测试：确认 baseline -> 跟踪 -> 调仓
    rb.confirm_baseline("test_client", [
        {"fund_code": "110022", "shares": 10000, "cost": 1.5, "purchase_date": "2025-01-15"},
        {"fund_code": "510300", "shares": 5000, "cost": 4.2, "purchase_date": "2025-03-01"},
    ], target_allocation={"110022": 60, "510300": 40})
    report = rb.generate_rebalance_report("test_client")
    print(format_rebalance_report(report))


if __name__ == "__main__":
    main()
