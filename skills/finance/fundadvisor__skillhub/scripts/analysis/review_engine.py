#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""投后业绩追踪检视引擎 (v7.0 新增)

组合投后闭环：拼组合净值序列 -> 业绩六维检视 -> 健康灯号 -> 周/月检视报告。
- 复用 PortfolioRebalancer（baseline / track_returns / drift / signal）
- 复用 perf_metrics 指标库（年化/回撤/夏普/Calmar 等）
- 净值历史：优先 provider.get_fund_nav_history（若实现），否则尝试 akshare，
  全部失败时降级为"成本常数序列"并在返回 dict 标注 degraded=True
- 所有网络调用 try/except；离线 import 与演示均可运行
"""
from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
sys.path.insert(0, str(_SCRIPTS / "data_collection"))

from analysis.portfolio_rebalancer import PortfolioRebalancer, _action_dict  # noqa: E402
from analysis import perf_metrics as pm  # noqa: E402


def _health_icon(value: Optional[float], good: float, warn: float,
                 lower_is_better: bool = False) -> str:
    """健康灯号：🟢 健康 / 🟡 关注 / 🔴 预警"""
    if value is None:
        return "🟡"
    if lower_is_better:
        return "🟢" if value <= good else ("🟡" if value <= warn else "🔴")
    return "🟢" if value >= good else ("🟡" if value >= warn else "🔴")


class ReviewEngine:
    """投后检视引擎"""

    def __init__(self):
        self.rebalancer = PortfolioRebalancer()
        self.provider = self.rebalancer.provider

    # ─── 组合净值序列 ─────────────────────────────────────
    def _fund_nav_history(self, code: str, days: int) -> List[Dict]:
        """尽力获取单只基金净值历史 [{date, nav}]，全部失败返回 []"""
        # 1) provider 若实现了 get_fund_nav_history 则优先
        try:
            fn = getattr(self.provider, "get_fund_nav_history", None)
            if callable(fn):
                r = fn(code, days=days)
                items = r.get("history") or r.get("items") or []
                out = [{"date": str(x.get("date") or x.get("净值日期")),
                        "nav": float(x.get("nav") or x.get("单位净值"))}
                       for x in items if x.get("nav") or x.get("单位净值")]
                if out:
                    return out
        except Exception:
            pass
        # 2) akshare 可选依赖
        try:
            import akshare as ak  # noqa: E402
            df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
            if df is not None and len(df) > 0:
                tail = df.tail(days)
                return [{"date": str(row["净值日期"])[:10], "nav": float(row["单位净值"])}
                        for _, row in tail.iterrows()]
        except Exception:
            pass
        return []

    def portfolio_nav_series(self, client_id: str, days: int = 250) -> Dict:
        """拼组合日度净值序列（以 baseline 份额加权，起点归一为 1）

        返回 dict:
          nav_series  list[float] 组合净值（起点=1）
          dates       list[str]   对应日期
          degraded    True 表示历史净值拿不到，已降级为成本常数序列
          note        降级说明
        """
        baseline = self.rebalancer.load_baseline(client_id)
        if not baseline:
            return {"nav_series": [], "dates": [], "degraded": True,
                    "note": f"未找到 {client_id} 的 baseline"}
        holdings = [h for h in baseline.get("holdings", [])
                    if h.get("fund_code") and h.get("shares", 0) > 0]
        if not holdings:
            return {"nav_series": [], "dates": [], "degraded": True, "note": "baseline 无持仓"}
        # 拉各基金净值历史
        histories: Dict[str, Dict[str, float]] = {}
        for h in holdings:
            hist = self._fund_nav_history(h["fund_code"], days)
            if hist:
                histories[h["fund_code"]] = {x["date"]: x["nav"] for x in hist}
        if not histories:
            # 降级：成本常数序列
            const = 1.0
            n = 30
            today = datetime.now().date()
            return {
                "nav_series": [const] * n,
                "dates": [(today - timedelta(days=n - 1 - i)).strftime("%Y-%m-%d") for i in range(n)],
                "degraded": True,
                "note": "净值历史不可用（网络/源失败），已降级为成本常数序列，指标仅供参考",
            }
        # 日期并集（升序）
        all_dates = sorted({d for hist in histories.values() for d in hist})
        all_dates = all_dates[-days:]
        # 前向填充各基金净值
        filled: Dict[str, List[float]] = {}
        for code, hist in histories.items():
            series = []
            last = None
            for d in all_dates:
                if d in hist:
                    last = hist[d]
                series.append(last)
            # 起始日尚无净值的基金，用其首个已知净值回填
            first = next((v for v in series if v is not None), None)
            series = [v if v is not None else first for v in series]
            filled[code] = series
        # 组合市值序列（缺历史的基金按成本常数计）
        values = []
        for i in range(len(all_dates)):
            v = 0.0
            for h in holdings:
                code = h["fund_code"]
                if code in filled and filled[code][i]:
                    v += h["shares"] * filled[code][i]
                else:
                    v += h["shares"] * h.get("cost", 0)
            values.append(v)
        if not values or values[0] <= 0:
            return {"nav_series": [], "dates": [], "degraded": True, "note": "组合估值失败"}
        base = values[0]
        return {"nav_series": [v / base for v in values], "dates": all_dates,
                "degraded": False, "note": ""}

    # ─── 周检视 ───────────────────────────────────────────
    def weekly_review(self, client_id: str) -> Dict:
        """周度检视：六维 Dashboard + 健康灯号 + 本周要点 + 下次检视日"""
        tracking = self.rebalancer.track_returns(client_id)
        if "error" in tracking:
            return {"error": tracking["error"]}
        nav_info = self.portfolio_nav_series(client_id, days=60)
        series = nav_info.get("nav_series", [])
        metrics = pm.compute_all_metrics(series) if len(series) >= 2 else {}
        drift_actions = [a for a in self.rebalancer.drift_rebalance(client_id)
                         if a.action != "error"]
        max_drift = max((abs(a.amount_pct) for a in drift_actions), default=0.0)

        total_ret = tracking.get("total_profit_pct")
        ann = metrics.get("annualized")
        mdd = metrics.get("max_drawdown")
        sharpe = metrics.get("sharpe")
        dashboard = [
            {"维度": "总收益", "值": total_ret, "单位": "%",
             "灯号": _health_icon(total_ret, 0, -5)},
            {"维度": "年化收益", "值": ann, "单位": "%",
             "灯号": _health_icon(ann, 5, 0)},
            {"维度": "最大回撤", "值": mdd, "单位": "%",
             "灯号": _health_icon(mdd, -10, -20)},  # 回撤越浅(越接近0)越健康
            {"维度": "夏普比率", "值": sharpe, "单位": "",
             "灯号": _health_icon(sharpe, 1.0, 0.0)},
            {"维度": "配置漂移", "值": round(max_drift, 1), "单位": "%",
             "灯号": _health_icon(max_drift, 5, 10, lower_is_better=True)},
            {"维度": "偏离提示", "值": len(drift_actions), "单位": "项",
             "灯号": "🟢" if not drift_actions else ("🟡" if len(drift_actions) <= 2 else "🔴")},
        ]
        red = sum(1 for d in dashboard if d["灯号"] == "🔴")
        yellow = sum(1 for d in dashboard if d["灯号"] == "🟡")
        health = "🔴 需尽快处理" if red >= 2 else ("🟡 有关注点" if red == 1 or yellow >= 3 else "🟢 组合健康")
        # 本周要点
        highlights = []
        if total_ret is not None:
            highlights.append(f"组合累计收益 {total_ret:+.2f}%，市值 {tracking.get('total_value', 0):.0f}")
        if mdd is not None:
            highlights.append(f"近60日最大回撤 {mdd:.2f}%" + ("（数据降级）" if nav_info.get("degraded") else ""))
        for a in drift_actions[:3]:
            highlights.append(f"[{a.urgency}] {a.action} {a.target} {a.amount_pct:+.1f}%")
        if not highlights:
            highlights.append("暂无显著变化")
        return {
            "type": "weekly",
            "client_id": client_id,
            "dashboard": dashboard,
            "health": health,
            "highlights": highlights,
            "degraded": nav_info.get("degraded", False),
            "degraded_note": nav_info.get("note", ""),
            "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_review": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        }

    # ─── 月检视 ───────────────────────────────────────────
    def _period_stats(self, series: List[float], days: int) -> Dict:
        """截取近 days 天子序列算收益与回撤"""
        if len(series) < 2:
            return {"return": None, "mdd": None}
        sub = series[-days:] if len(series) > days else series
        ret = (sub[-1] / sub[0] - 1.0) * 100.0
        dd = pm.max_drawdown(sub)
        return {"return": round(ret, 2), "mdd": dd["mdd"] if dd else None}

    def monthly_review(self, client_id: str) -> Dict:
        """月度检视：表现表 + 归因汇总 + 告警汇总 + 下月建议 + 下次检视日"""
        tracking = self.rebalancer.track_returns(client_id)
        if "error" in tracking:
            return {"error": tracking["error"]}
        nav_info = self.portfolio_nav_series(client_id, days=250)
        series = nav_info.get("nav_series", [])
        perf_table = {
            "本月": self._period_stats(series, 22),
            "本年": self._period_stats(series, 250),
            "成立以来": self._period_stats(series, max(len(series), 2)),
        }
        # 归因汇总（简化估算）：配置=漂移敞口估算，选基=持仓加权超额，时机=残差
        attribution = self._simple_attribution(tracking, nav_info)
        # 告警汇总（复用 rebalancer 的 drift + signal）
        report = self.rebalancer.generate_rebalance_report(client_id)
        alerts = report.get("merged_actions", []) if "error" not in report else []
        # 下月建议
        suggestions = []
        high = [a for a in alerts if a.get("urgency") == "高"]
        if high:
            suggestions.append(f"优先处理 {len(high)} 项高 urgency 告警：" +
                               "；".join(f"{a['action']}{a['target']}" for a in high[:3]))
        if any(a.get("source") == "drift" for a in alerts):
            suggestions.append("存在配置漂移，建议按目标配置再平衡")
        if nav_info.get("degraded"):
            suggestions.append("净值数据降级中，建议恢复网络后复核指标")
        if not suggestions:
            suggestions.append("组合运行平稳，按季度计划检视即可")
        return {
            "type": "monthly",
            "client_id": client_id,
            "perf_table": perf_table,
            "attribution": attribution,
            "alerts": alerts,
            "suggestions": suggestions,
            "degraded": nav_info.get("degraded", False),
            "degraded_note": nav_info.get("note", ""),
            "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "next_review": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        }

    def _simple_attribution(self, tracking: Dict, nav_info: Dict) -> Dict:
        """简化归因：配置 / 选基 / 时机（无基准时为单组合近似）"""
        holdings = tracking.get("holdings", [])
        total = tracking.get("total_profit_pct", 0.0) or 0.0
        # 选基贡献：各基金收益相对组合均值的加权超额之和的绝对水平
        n = len(holdings)
        if n == 0:
            return {"配置贡献": None, "选基贡献": None, "时机贡献": None, "note": "无持仓"}
        avg = sum(h.get("profit_pct", 0) for h in holdings) / n
        selection = sum((h.get("profit_pct", 0) - avg) * (h.get("current_value", 0) /
                        max(1e-8, tracking.get("total_value", 1))) for h in holdings)
        # 配置贡献：用目标 vs 当前的漂移幅度近似（漂移越大拖累越多，记负值）
        drift_actions = self.rebalancer.drift_rebalance(tracking.get("client_id", ""))
        drift_cost = -sum(abs(a.amount_pct) for a in drift_actions if a.action != "error") * 0.1
        timing = total - selection - drift_cost
        return {
            "配置贡献": round(drift_cost, 2),
            "选基贡献": round(selection, 2),
            "时机贡献": round(timing, 2),
            "合计": round(drift_cost + selection + timing, 2),
            "note": "简化归因（无基准近似）：配置=漂移拖累估算，选基=持仓加权超额，时机=残差",
        }


# ─── 报告格式化 ───────────────────────────────────────────
def format_review(review: Dict) -> str:
    """把 weekly/monthly 检视结果渲染为 markdown 文本（带 emoji）"""
    if "error" in review:
        return f"❌ {review['error']}"
    rtype = review.get("type", "weekly")
    title = "📅 月度检视报告" if rtype == "monthly" else "📋 周度检视报告"
    lines = [f"{title}  |  {review.get('client_id')}  |  {review.get('reviewed_at')}",
             "=" * 60]
    if review.get("degraded"):
        lines.append(f"⚠️ 数据降级：{review.get('degraded_note', '部分数据不可用')}")
    # 周度：六维 Dashboard
    if rtype == "weekly":
        lines.append(f"健康状态: {review.get('health', '')}")
        lines.append("\n【六维 Dashboard】")
        for d in review.get("dashboard", []):
            v = d.get("值")
            vs = f"{v:+.2f}" if isinstance(v, float) else str(v)
            lines.append(f"  {d['灯号']} {d['维度']}: {vs}{d.get('单位','')}")
        lines.append("\n【本周要点】")
        for h in review.get("highlights", []):
            lines.append(f"  · {h}")
    # 月度：表现表 + 归因 + 告警 + 建议
    else:
        lines.append("【组合表现】")
        for period, st in review.get("perf_table", {}).items():
            ret = st.get("return")
            mdd = st.get("mdd")
            rs = f"{ret:+.2f}%" if ret is not None else "N/A"
            ms = f"{mdd:.2f}%" if mdd is not None else "N/A"
            lines.append(f"  {period}: 收益 {rs}  最大回撤 {ms}")
        att = review.get("attribution", {})
        if att:
            lines.append("\n【归因汇总】(简化)")
            for k in ("配置贡献", "选基贡献", "时机贡献"):
                v = att.get(k)
                lines.append(f"  · {k}: {v:+.2f}%" if isinstance(v, (int, float))
                             else f"  · {k}: N/A")
        alerts = review.get("alerts", [])
        lines.append(f"\n【告警汇总】({len(alerts)} 项)")
        if not alerts:
            lines.append("  ✅ 暂无告警")
        for a in alerts[:8]:
            icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(a.get("urgency"), "")
            lines.append(f"  {icon} [{a.get('urgency')}] {a.get('action')} {a.get('target')} "
                         f"[{a.get('source')}]")
        lines.append("\n【下月建议】")
        for s in review.get("suggestions", []):
            lines.append(f"  · {s}")
    lines.append("")
    lines.append(f"📌 下次检视: {review.get('next_review')}")
    lines.append("=" * 60)
    lines.append("⚠️ 仅供参考，不构成投资指令。")
    return "\n".join(lines)


if __name__ == "__main__":
    # 演示（offline safe）：构造假 review 演示渲染；真实 client 演示在网络失败时也能跑完
    fake_weekly = {
        "type": "weekly", "client_id": "demo_client",
        "dashboard": [
            {"维度": "总收益", "值": 3.25, "单位": "%", "灯号": "🟢"},
            {"维度": "年化收益", "值": 8.1, "单位": "%", "灯号": "🟢"},
            {"维度": "最大回撤", "值": -6.4, "单位": "%", "灯号": "🟢"},
            {"维度": "夏普比率", "值": 1.2, "单位": "", "灯号": "🟢"},
            {"维度": "配置漂移", "值": 6.5, "单位": "%", "灯号": "🟡"},
            {"维度": "偏离提示", "值": 1, "单位": "项", "灯号": "🟡"},
        ],
        "health": "🟡 有关注点",
        "highlights": ["组合累计收益 +3.25%，市值 103250", "[中] 减持 110022 +6.5%"],
        "degraded": False, "degraded_note": "",
        "reviewed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "next_review": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
    }
    print(format_review(fake_weekly))
    print()
    # 真实引擎演示：不存在的 client 应优雅返回 error 文本，不抛异常
    try:
        eng = ReviewEngine()
        print(format_review(eng.weekly_review("demo_no_such_client")))
    except Exception as e:
        print(f"真实引擎演示跳过（环境限制）: {type(e).__name__}: {e}")
