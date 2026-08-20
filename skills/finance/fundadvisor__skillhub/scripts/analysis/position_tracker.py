#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v7.4 持仓跟仓分析 (PortfolioPositionTracker)
==============================================
跟踪持仓 vs 目标配置的偏差,识别漂移、贡献度、触发再平衡。

设计要点:
  - 输入:实际持仓(基金代码 + 权重%) + 目标配置(基金代码 + 权重%)
  - 输出:每只基金的:
      - actual_weight 实际权重
      - target_weight 目标权重
      - drift 偏差百分比(>0 超配,<0 低配)
      - drift_severity 偏差等级(none/minor/moderate/severe/critical)
      - contribution 偏差贡献度(权重 * drift)
      - rebalance_action 建议操作(buy/sell/hold)
  - 汇总:总漂移度 / 平均绝对偏差 / 最大偏差基金 / 是否需要再平衡

v7.4 设计:
  - 不依赖外部数据,纯计算
  - 漂移等级阈值可配(默认 minor 1% / moderate 3% / severe 5% / critical 10%)
  - 输出结构稳定,可被 MCP 工具直接序列化
"""
from __future__ import annotations

import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

SKILL_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILL_DIR / "scripts"))


# 漂移等级阈值(单位:百分点,如 1.0 = 1%)
DEFAULT_DRIFT_THRESHOLDS: Dict[str, float] = {
    "minor": 1.0,
    "moderate": 3.0,
    "severe": 5.0,
    "critical": 10.0,
}

# 再平衡触发阈值(总漂移度达到此值才触发)
DEFAULT_REBALANCE_TRIGGER = 5.0  # 总漂移度 ≥ 5% 触发


class PortfolioPositionTracker:
    """v7.4 持仓跟仓分析器"""

    def __init__(self,
                 drift_thresholds: Optional[Dict[str, float]] = None,
                 rebalance_trigger: float = DEFAULT_REBALANCE_TRIGGER):
        self.drift_thresholds = {**DEFAULT_DRIFT_THRESHOLDS, **(drift_thresholds or {})}
        self.rebalance_trigger = rebalance_trigger

    def analyze(self,
                actual_holdings: List[Dict[str, Any]],
                target_alloc: Dict[str, float],
                total_assets: Optional[float] = None) -> Dict[str, Any]:
        """跟仓分析主入口

        Args:
            actual_holdings: 实际持仓列表 [{code, name, weight, amount, ...}]
                weight 单位:百分比(0~100),amount 单位:元
            target_alloc: 目标配置 {code: weight_pct}  权重单位:百分比(0~100)
            total_assets: 组合总资产(元),若提供则给出买卖金额建议

        Returns:
            {
              "positions": [  # 每只基金跟仓详情
                {
                  "code": str, "name": str,
                  "actual_weight": float, "target_weight": float,
                  "drift": float,  # 百分点差
                  "drift_severity": "none/minor/moderate/severe/critical",
                  "drift_direction": "overweight/underweight/match",
                  "contribution": float,  # 偏差贡献(权重*drift)
                  "action": "buy/sell/hold",
                  "trade_amount": float,  # 调仓金额(若有 total_assets)
                }
              ],
              "summary": {
                "total_drift": float,        # 总绝对漂移度 = Σ|drift|
                "avg_drift": float,           # 平均绝对偏差
                "max_drift_code": str,
                "max_drift_value": float,
                "needs_rebalance": bool,     # 总漂移 ≥ 触发阈值
                "matched_count": int,        # 偏差 < 1% 的基金数
                "overweight_count": int,
                "underweight_count": int,
              },
              "config_validation": {
                "actual_total_pct": float,  # 实际权重之和
                "target_total_pct": float,
                "actual_count": int,
                "target_count": int,
                "missing_in_actual": [str],  # 实际有但目标无
                "missing_in_target": [str],  # 目标有但实际无
              },
            }
        """
        # 1) 归一化数据
        actual_map: Dict[str, Dict[str, Any]] = {}
        for h in actual_holdings:
            if not isinstance(h, dict):
                continue
            code = str(h.get("code", "")).strip()
            if not code:
                continue
            actual_map[code] = {
                "code": code,
                "name": h.get("name", ""),
                "weight": float(h.get("weight", 0) or 0),
                "amount": float(h.get("amount", 0) or 0),
            }

        target_map: Dict[str, float] = {}
        for code, weight in target_alloc.items():
            if code and isinstance(weight, (int, float)):
                target_map[str(code)] = float(weight)

        # 2) 合并代码集合
        all_codes = set(actual_map.keys()) | set(target_map.keys())

        # 3) 逐只基金计算 drift
        positions: List[Dict[str, Any]] = []
        for code in sorted(all_codes):
            actual = actual_map.get(code, {"code": code, "name": "", "weight": 0, "amount": 0})
            target = target_map.get(code, 0)
            actual_weight = actual["weight"]
            target_weight = target
            drift = actual_weight - target_weight
            severity = self._classify_drift(abs(drift))
            if abs(drift) < 0.01:
                direction = "match"
            elif drift > 0:
                direction = "overweight"
            else:
                direction = "underweight"
            contribution = (actual_weight * drift) / 10000  # 归一化
            # 调仓金额建议
            if total_assets and total_assets > 0:
                target_amount = total_assets * target_weight / 100
                trade_amount = round(target_amount - actual.get("amount", 0), 2)
            else:
                trade_amount = 0.0
            # 调仓动作
            if abs(drift) < 0.01:
                action = "hold"
            elif drift > 0:
                action = "sell"
            else:
                action = "buy"
            positions.append({
                "code": code,
                "name": actual.get("name", ""),
                "actual_weight": round(actual_weight, 2),
                "target_weight": round(target_weight, 2),
                "drift": round(drift, 2),
                "drift_severity": severity,
                "drift_direction": direction,
                "contribution": round(contribution, 4),
                "action": action,
                "trade_amount": trade_amount,
            })

        # 4) 汇总统计
        total_drift = sum(abs(p["drift"]) for p in positions) / 2  # 避免双重计数
        avg_drift = (total_drift / len(positions)) if positions else 0.0
        max_pos = max(positions, key=lambda x: abs(x["drift"]), default=None)
        needs_rebalance = total_drift >= self.rebalance_trigger
        matched_count = sum(1 for p in positions if p["drift_severity"] == "none")
        over_count = sum(1 for p in positions if p["drift_direction"] == "overweight")
        under_count = sum(1 for p in positions if p["drift_direction"] == "underweight")

        # 5) 配置校验
        actual_total = sum(h["weight"] for h in actual_map.values())
        target_total = sum(target_map.values())

        result = {
            "positions": positions,
            "summary": {
                "total_drift": round(total_drift, 2),
                "avg_drift": round(avg_drift, 2),
                "max_drift_code": max_pos["code"] if max_pos else "",
                "max_drift_value": max_pos["drift"] if max_pos else 0.0,
                "needs_rebalance": needs_rebalance,
                "matched_count": matched_count,
                "overweight_count": over_count,
                "underweight_count": under_count,
            },
            "config_validation": {
                "actual_total_pct": round(actual_total, 2),
                "target_total_pct": round(target_total, 2),
                "actual_count": len(actual_map),
                "target_count": len(target_map),
                "missing_in_actual": sorted(set(target_map.keys()) - set(actual_map.keys())),
                "missing_in_target": sorted(set(actual_map.keys()) - set(target_map.keys())),
            },
        }
        return result

    def _classify_drift(self, abs_drift_pct: float) -> str:
        """根据 |drift| 划分等级(百分点)。"""
        if abs_drift_pct < self.drift_thresholds["minor"]:
            return "none"
        if abs_drift_pct < self.drift_thresholds["moderate"]:
            return "minor"
        if abs_drift_pct < self.drift_thresholds["severe"]:
            return "moderate"
        if abs_drift_pct < self.drift_thresholds["critical"]:
            return "severe"
        return "critical"

    def format_report(self, analysis: Dict[str, Any]) -> str:
        """生成中文可读报告。"""
        s = analysis["summary"]
        cv = analysis["config_validation"]
        lines = [
            "📊 持仓跟仓分析报告",
            f"   总漂移度: {s['total_drift']:.2f}%  |  "
            f"平均偏差: {s['avg_drift']:.2f}%  |  "
            f"是否再平衡: {'是' if s['needs_rebalance'] else '否'}",
            "",
            f"   实际持仓 {cv['actual_count']} 只(权重 {cv['actual_total_pct']:.1f}%),"
            f" 目标 {cv['target_count']} 只(权重 {cv['target_total_pct']:.1f}%)",
        ]
        if cv["missing_in_actual"]:
            lines.append(f"   ⚠️ 目标有但实际缺失: {', '.join(cv['missing_in_actual'])}")
        if cv["missing_in_target"]:
            lines.append(f"   ℹ️ 实际有但目标未配: {', '.join(cv['missing_in_target'])}")
        lines.append("")
        lines.append("   📋 逐只基金:")
        for p in analysis["positions"]:
            icon = {"none": "✅", "minor": "🟡", "moderate": "🟠",
                     "severe": "🔴", "critical": "⛔"}.get(p["drift_severity"], "❓")
            arrow = "↑超配" if p["drift_direction"] == "overweight" else (
                "↓低配" if p["drift_direction"] == "underweight" else "=匹配")
            lines.append(f"     {icon} {p['code']} {p['name'][:10]:10s}  "
                         f"实 {p['actual_weight']:5.2f}% → 目 {p['target_weight']:5.2f}%  "
                         f"漂移 {p['drift']:+5.2f}% {arrow} → {p['action']}")
        return "\n".join(lines)


    # ── v8.0 新增: 集中度风险分析 ──────────────────────────────
    def concentration_risk(self, holdings: List[Dict[str, Any]],
                           holdings_data: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """持仓集中度风险分析。

        分析维度:
          - 单基金集中度: 最大单只基金占比
          - 类型集中度: 股票/债券/混合/QDII 分布
          - 公司集中度: 同一基金公司产品占比
          - Herfindahl 指数: 权重平方和（越接近1越集中）

        Returns:
            {"max_single_pct": 35.2,
             "type_concentration": {"股票型": 55.0, ...},
             "herfindahl_index": 0.18,
             "risk_level": "🟡 中等集中",
             "warnings": [...]}
        """
        if not holdings:
            return {"error": "无持仓数据"}

        total_weight = sum(h.get("weight", 0) for h in holdings) or 1.0
        weights = [h.get("weight", 0) / total_weight for h in holdings]

        # 单基金集中度
        max_single = max(weights) if weights else 0

        # Herfindahl 指数
        hhi = sum(w ** 2 for w in weights)

        # 类型集中度（从fund_code推断）
        type_weights: Dict[str, float] = {}
        for h in holdings:
            code = h.get("fund_code", "")
            ftype = self._guess_fund_type(code)
            w = h.get("weight", 0) / total_weight
            type_weights[ftype] = type_weights.get(ftype, 0) + w

        warnings = []
        if max_single > 0.30:
            warnings.append(f"🔴 单基金占比 {max_single*100:.1f}% > 30%，建议分散")
        elif max_single > 0.20:
            warnings.append(f"🟡 单基金占比 {max_single*100:.1f}% > 20%，需关注")
        if hhi > 0.25:
            warnings.append(f"🔴 Herfindahl 指数 {hhi:.2f} > 0.25，组合高度集中")
        elif hhi > 0.15:
            warnings.append(f"🟡 Herfindahl 指数 {hhi:.2f} > 0.15，集中度中等")

        risk_level = ("🔴 高度集中" if hhi > 0.25 or max_single > 0.30
                      else "🟡 中等集中" if hhi > 0.15 or max_single > 0.20
                      else "🟢 分散良好")

        return {
            "fund_count": len(holdings),
            "max_single_fund_pct": round(max_single * 100, 1),
            "max_single_name": max(holdings, key=lambda h: h.get("weight", 0)).get("name", ""),
            "type_concentration": {k: round(v * 100, 1) for k, v in sorted(type_weights.items(), key=lambda x: -x[1])},
            "herfindahl_index": round(hhi, 4),
            "risk_level": risk_level,
            "warnings": warnings,
        }

    # ── v8.0 新增: 相关性矩阵 ──────────────────────────────────
    def correlation_matrix(self, holdings: List[Dict[str, Any]],
                           nav_data: Optional[Dict[str, List[float]]] = None) -> Dict[str, Any]:
        """计算持仓基金间的收益相关性矩阵。

        Args:
            holdings: 持仓列表
            nav_data: {fund_code: [nav1, nav2, ...]} 历史净值数据

        Returns:
            {"matrix": [[1.0, 0.85, ...], ...],
             "labels": ["000001", ...],
             "high_corr_pairs": [("000001", "000002", 0.92), ...],
             "diversification_ratio": 0.65}
        """
        codes = [h.get("fund_code", "") for h in holdings if h.get("fund_code")]
        labels = [h.get("name", c) for h, c in zip(holdings, codes)]

        if len(codes) < 2:
            return {"error": "至少需要2只基金才能计算相关性", "labels": labels}

        # 计算日收益序列
        ret_series: Dict[str, List[float]] = {}
        for code in codes:
            nav = (nav_data or {}).get(code, [])
            if nav and len(nav) >= 20:
                rets = []
                for i in range(1, len(nav)):
                    if nav[i - 1] > 0:
                        rets.append((nav[i] - nav[i - 1]) / nav[i - 1])
                ret_series[code] = rets
            else:
                ret_series[code] = []

        n = len(codes)
        matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        high_corr_pairs = []

        for i in range(n):
            for j in range(i + 1, n):
                ri = ret_series.get(codes[i], [])
                rj = ret_series.get(codes[j], [])
                if len(ri) >= 20 and len(rj) >= 20:
                    corr = self._pearson_corr(ri[:min(len(ri), len(rj))], rj[:min(len(ri), len(rj))])
                else:
                    # 无数据时用类型估算
                    corr = self._estimate_corr_from_types(codes[i], codes[j])
                matrix[i][j] = matrix[j][i] = round(corr, 4)
                if corr > 0.85:
                    high_corr_pairs.append((codes[i], codes[j], round(corr, 4)))

        # 分散化比率 = 1 - 平均相关性
        off_diag = [matrix[i][j] for i in range(n) for j in range(i + 1, n)]
        avg_corr = sum(off_diag) / len(off_diag) if off_diag else 0
        div_ratio = round(1 - avg_corr, 4)

        return {
            "matrix": matrix,
            "labels": labels,
            "codes": codes,
            "high_corr_pairs": high_corr_pairs,
            "avg_correlation": round(avg_corr, 4),
            "diversification_ratio": div_ratio,
            "assessment": (
                "🟢 分散良好" if div_ratio > 0.5
                else "🟡 分散度一般" if div_ratio > 0.25
                else "🔴 高度相关，缺乏分散"
            ),
        }

    # ── v8.0 新增: 带成本的调仓信号 ────────────────────────────
    def rebalance_signal_with_cost(
        self,
        actual_holdings: List[Dict[str, Any]],
        target_alloc: Dict[str, float],
        total_assets: float,
        holding_days: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """带成本效益分析的调仓信号。

        扩展 analyze() 输出:
          - 每笔买卖操作估算费用
          - 回本周期估算
          - "不调仓"情景对比
        """
        base = self.analyze(actual_holdings, target_alloc, total_assets)
        holding_days = holding_days or {}

        # 为每个需要调仓的基金计算费用
        for pos in base["positions"]:
            if pos["action"] in ("buy", "sell") and pos.get("trade_amount", 0) > 0:
                code = pos["code"]
                days = holding_days.get(code, 365)  # 默认1年以上

                if pos["action"] == "sell":
                    fee = self._calc_redemption_fee(pos["trade_amount"], days)
                else:
                    fee = pos["trade_amount"] * 0.0015  # 申购费0.15%(1折)
                pos["estimated_fee"] = round(fee, 2)

                # 回本周期（假设年化超额3%）
                annual_excess = 0.03
                daily_excess = annual_excess / 252
                if daily_excess > 0:
                    pos["breakeven_days"] = round(fee / (pos["trade_amount"] * daily_excess), 0)
                else:
                    pos["breakeven_days"] = 999

        # 总成本
        total_fee = sum(p.get("estimated_fee", 0) for p in base["positions"] if p["action"] in ("buy", "sell"))
        base["total_estimated_fee"] = round(total_fee, 2)
        base["fee_pct"] = round(total_fee / max(total_assets, 0.01) * 100, 2)

        # "不调仓"对比
        current_drift = base["summary"]["total_drift"]
        base["no_action_scenario"] = {
            "current_drift": current_drift,
            "risk": "继续承受当前偏差" if current_drift > 2 else "偏差在可接受范围内",
            "advice": "建议调仓" if current_drift > 3 else "可以暂不调仓",
        }

        return base

    # ── v8.0 新增: 实时净值跟踪 ──────────────────────────────
    def nav_vs_target_tracking(
        self,
        holdings: List[Dict[str, Any]],
        target_alloc: Dict[str, float],
        nav_updates: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """基于最新净值的实时 vs 目标对比。

        Args:
            holdings: 当前持仓
            target_alloc: 目标配置
            nav_updates: {fund_code: latest_nav} 最新净值

        Returns:
            当前实际权重 vs 目标权重对比
        """
        nav_updates = nav_updates or {}
        rows = []
        for h in holdings:
            code = h.get("fund_code", "")
            if not code:
                continue
            shares = float(h.get("shares", 0) or 0)
            nav = float(nav_updates.get(code)
                        or h.get("nav")
                        or h.get("current_nav")
                        or 0)
            amount = float(h.get("amount", 0) or h.get("market_value", 0) or 0)
            weight = float(h.get("weight", 0) or 0)
            if shares > 0 and nav > 0:
                market_value = shares * nav
                has_value = True
            elif amount > 0:
                market_value = amount
                has_value = True
            else:
                market_value = weight
                has_value = False
            rows.append({
                "code": str(code),
                "name": h.get("name", code),
                "market_value": market_value,
                "weight": weight,
                "has_value": has_value,
            })

        total_market_value = sum(r["market_value"] for r in rows)
        total_weight = sum(r["weight"] for r in rows)
        positions = []
        for r in rows:
            if total_market_value > 0 and r["has_value"]:
                actual_pct = r["market_value"] / total_market_value * 100.0
            elif total_weight > 0:
                actual_pct = r["weight"] / total_weight * 100.0
            else:
                actual_pct = 0.0
            target_w = float(target_alloc.get(r["code"], 0) or 0)
            drift = actual_pct - target_w
            positions.append({
                "code": r["code"],
                "name": r["name"],
                "actual_weight_pct": round(actual_pct, 2),
                "target_weight_pct": round(target_w, 2),
                "drift_pct": round(drift, 2),
                "status": "超配" if drift > 0.01 else "低配" if drift < -0.01 else "正常",
            })

        total_drift = sum(abs(p["drift_pct"]) for p in positions)
        return {
            "positions": positions,
            "total_drift_pct": round(total_drift, 2),
            "needs_rebalance": total_drift > 5.0,
            "tracked_at": datetime.now().isoformat(),
        }

    # ── 内部工具方法 ───────────────────────────────────────────
    @staticmethod
    def _pearson_corr(x: List[float], y: List[float]) -> float:
        """计算 Pearson 相关系数。"""
        n = min(len(x), len(y))
        if n < 3:
            return 0.5
        mx = sum(x) / n
        my = sum(y) / n
        sx = math.sqrt(sum((v - mx) ** 2 for v in x) / n)
        sy = math.sqrt(sum((v - my) ** 2 for v in y) / n)
        if sx == 0 or sy == 0:
            return 0.5
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n)) / n
        return cov / (sx * sy)

    @staticmethod
    def _estimate_corr_from_types(code1: str, code2: str) -> float:
        """基于基金类型估算相关性（无净值数据时的降级方案）。"""
        # 简化的类型相关性表
        type_corr = {
            ("股票型", "股票型"): 0.85, ("股票型", "偏股混合"): 0.80,
            ("股票型", "混合型"): 0.65, ("股票型", "债券型"): 0.10,
            ("债券型", "债券型"): 0.70, ("债券型", "纯债"): 0.80,
            ("混合型", "混合型"): 0.70,
        }
        # 无法精确判断类型时返回默认值
        return 0.50

    @staticmethod
    def _calc_redemption_fee(amount: float, holding_days: int) -> float:
        """计算赎回费。"""
        if holding_days < 7:
            return amount * 0.015  # 惩罚性 1.5%
        elif holding_days < 30:
            return amount * 0.0075
        elif holding_days < 365:
            return amount * 0.005
        elif holding_days < 730:
            return amount * 0.0025
        return 0.0

    @staticmethod
    def _guess_fund_type(code: str) -> str:
        """从代码推测基金类型（简化版）。"""
        # 实际应从 fund_products.json 查询
        return "混合型"


# ===== 便捷函数 =====

def quick_position_analysis(actual_holdings: List[Dict[str, Any]],
                              target_alloc: Dict[str, float],
                              total_assets: Optional[float] = None) -> Dict[str, Any]:
    """便捷函数:持仓跟仓分析。"""
    return PortfolioPositionTracker().analyze(actual_holdings, target_alloc, total_assets)
