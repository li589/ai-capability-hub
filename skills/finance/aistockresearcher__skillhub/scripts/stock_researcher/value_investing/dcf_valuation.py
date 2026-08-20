#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DCF 估值模型（v5.0 新增）⭐

两阶段自由现金流折现模型：
- 阶段 1（前 3-5 年）: 显式预测，增长率 = clip(历史 FCF CAGR, 0%, 25%) 与券商 EPS 一致预期取平均
- 阶段 2（终值）: Gordon 模型 TV = FCF_{n+1} / (WACC - g)，g 默认 3%

折现率调用 wacc.py 的 CAPM WACC，clip 到 [6%, 12%]。
敏感性分析: WACC ±1% × 终值增长 ±0.5% 的 9 格矩阵。
安全边际 = (内在价值 - 现价) / 内在价值；>30% 为有吸引力。

复用并扩展 core/valuation.py 的 DCF 逻辑，修复其返回总值而非每股的 bug。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..data.financial_statements import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cashflow_statement,
    filter_recent_n_years,
)
from .wacc import calc_wacc


@dataclass
class DCFResult:
    """DCF 估值结果"""
    code: str
    intrinsic_value_per_share: float = 0.0   # 每股内在价值
    fair_value_range: Tuple[float, float, float] = (0.0, 0.0, 0.0)  # (low, mid, high)
    margin_of_safety_pct: float = 0.0
    recommendation: str = "中性"
    current_price: float = 0.0
    wacc: float = 0.0
    terminal_growth: float = 0.0
    assumptions: Dict = field(default_factory=dict)
    sensitivity: Dict[str, Dict[str, float]] = field(default_factory=dict)
    fcf_history: List[float] = field(default_factory=list)
    growth_rate: float = 0.0
    insufficient_data: bool = False
    error: Optional[str] = None


def _safe(val, default=0.0) -> float:
    try:
        f = float(val) if val is not None else default
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


class DCFValuation:
    """
    DCF 估值器。

    用法:
        valuator = DCFValuation()
        result = valuator.valuate("600519")
    """

    def __init__(self,
                 forecast_years: int = 5,
                 default_terminal_growth: float = 0.03,
                 wacc_min: float = 0.06,
                 wacc_max: float = 0.12):
        self.forecast_years = forecast_years
        self.default_terminal_growth = default_terminal_growth
        self.wacc_min = wacc_min
        self.wacc_max = wacc_max

    # ─────────────────────────────────────────────
    # FCF 计算
    # ─────────────────────────────────────────────
    def _calc_fcf_history(self, cashflow: List[dict]) -> List[float]:
        """
        FCF = 经营活动现金流净额 - 资本支出
        资本支出 ≈ 购建固定/无形/其他长期资产支付的现金
        """
        fcfs = []
        for row in cashflow:
            cfo = _safe(row.get("NETCASH_OPERATE"))
            capex = _safe(row.get("BUY_FIX_ASSET_OTHER"))
            fcfs.append(cfo - capex)
        return fcfs

    def _calc_cagr(self, values: List[float], min_years: int = 3) -> Optional[float]:
        """计算复合增长率 CAGR"""
        if len(values) < min_years + 1:
            return None
        # values 按报告期降序（最新在前），取首尾
        start = values[-1]  # 最早
        end = values[0]     # 最新
        n = len(values) - 1
        if start <= 0 or end <= 0:
            return None
        return (end / start) ** (1 / n) - 1

    # ─────────────────────────────────────────────
    # DCF 核心计算
    # ─────────────────────────────────────────────
    def _dcf_core(self,
                  fcf_current: float,
                  growth_rate: float,
                  wacc: float,
                  terminal_growth: float,
                  forecast_years: int,
                  shares_outstanding: float = 0.0,
                  total_debt: float = 0.0,
                  cash: float = 0.0) -> Tuple[float, float, float]:
        """
        核心 DCF 计算，返回 (企业价值, 股权价值, 每股内在价值)。

        Args:
            fcf_current: 当前 FCF（最新年）
            growth_rate: 阶段 1 增长率（小数）
            wacc: 折现率（小数）
            terminal_growth: 终值增长（小数）
            forecast_years: 阶段 1 年数
            shares_outstanding: 总股本（股）；>0 时计算每股
            total_debt: 有息负债（用于从 EV 到 Equity）
            cash: 现金及等价物（用于从 EV 到 Equity）

        Returns:
            (enterprise_value, equity_value, per_share_value)
        """
        # 阶段 1: 显式预测
        pv_explicit = 0.0
        fcf = fcf_current
        for y in range(1, forecast_years + 1):
            fcf = fcf * (1 + growth_rate)
            pv = fcf / (1 + wacc) ** y
            pv_explicit += pv

        # 阶段 2: 终值（Gordon 模型）
        fcf_terminal = fcf * (1 + terminal_growth)
        if wacc > terminal_growth:
            tv = fcf_terminal / (wacc - terminal_growth)
        else:
            tv = fcf_terminal / 0.01  # 兜底：用 1% 净折现率
        pv_tv = tv / (1 + wacc) ** forecast_years

        enterprise_value = pv_explicit + pv_tv
        equity_value = enterprise_value - total_debt + cash
        per_share = equity_value / shares_outstanding if shares_outstanding > 0 else equity_value
        return enterprise_value, equity_value, per_share

    # ─────────────────────────────────────────────
    # 敏感性分析
    # ─────────────────────────────────────────────
    def _sensitivity_matrix(self,
                            fcf_current: float,
                            growth_rate: float,
                            shares_outstanding: float,
                            total_debt: float,
                            cash: float,
                            wacc_center: float,
                            tg_center: float) -> Dict[str, Dict[str, float]]:
        """生成 WACC ±1% × 终值增长 ±0.5% 的 9 格矩阵"""
        wacc_range = [wacc_center - 0.01, wacc_center, wacc_center + 0.01]
        tg_range = [tg_center - 0.005, tg_center, tg_center + 0.005]
        matrix: Dict[str, Dict[str, float]] = {}
        for wacc in wacc_range:
            wacc_key = f"{wacc*100:.1f}%"
            matrix[wacc_key] = {}
            for tg in tg_range:
                tg_key = f"{tg*100:.1f}%"
                if wacc <= tg:
                    matrix[wacc_key][tg_key] = None
                    continue
                _, _, per_share = self._dcf_core(
                    fcf_current, growth_rate, max(0.06, min(0.15, wacc)),
                    max(0.0, tg), self.forecast_years,
                    shares_outstanding, total_debt, cash
                )
                matrix[wacc_key][tg_key] = round(per_share, 2)
        return matrix

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────
    def valuate(self,
                code: str,
                current_price: float = 0.0,
                shares_outstanding: float = 0.0,
                market_cap: float = 0.0,
                stock_returns: Optional[List[float]] = None,
                benchmark_returns: Optional[List[float]] = None,
                terminal_growth: Optional[float] = None,
                financials: Optional[dict] = None,
                analyst_growth_rate: Optional[float] = None) -> DCFResult:
        """
        执行 DCF 估值。

        Args:
            code: 股票代码
            current_price: 现价（用于计算安全边际）
            shares_outstanding: 总股本（股）
            market_cap: 股权市值（元）
            stock_returns / benchmark_returns: 用于计算 WACC 中的 beta
            terminal_growth: 终值增长率（小数，如 0.03）；None 用默认
            financials: 预取的财务数据
            analyst_growth_rate: 券商一致预期 EPS 增长率（小数）；用于调整阶段 1 增长
        """
        tg = terminal_growth if terminal_growth is not None else self.default_terminal_growth

        if financials is None:
            financials = {
                "income": fetch_income_statement(code, 5),
                "balance": fetch_balance_sheet(code, 5),
                "cashflow": fetch_cashflow_statement(code, 5),
            }
        income = filter_recent_n_years(financials.get("income", []), 5)
        balance = filter_recent_n_years(financials.get("balance", []), 5)
        cashflow = filter_recent_n_years(financials.get("cashflow", []), 5)

        if not cashflow or len(cashflow) < 3:
            return DCFResult(code=code, insufficient_data=True,
                             error="现金流量表数据不足（需至少 3 年）")

        # FCF 历史
        fcf_history = self._calc_fcf_history(cashflow)
        if not fcf_history or all(f <= 0 for f in fcf_history):
            return DCFResult(code=code, insufficient_data=True,
                             error="无法计算有效 FCF（经营现金流为负或数据缺失）",
                             fcf_history=fcf_history)

        fcf_current = fcf_history[0]  # 最新一期

        # 增长率：历史 FCF CAGR + 券商预期取平均，clip 到 [0%, 25%]
        # FCF 可能因 capex 代理（含全部投资活动现金流）而波动大，故用营收增长作兜底
        cagr = self._calc_cagr(fcf_history, min_years=3)
        # 营收 CAGR 作为更稳定的增长代理
        revenues = [_safe(row.get("TOTAL_OPERATE_INCOME")) for row in income[:min(self.forecast_years + 1, len(income))]]
        revenues = [r for r in revenues if r > 0]
        rev_cagr = self._calc_cagr(revenues, min_years=3) if len(revenues) >= 4 else None

        if cagr is not None and cagr > 0:
            # FCF CAGR 可信
            if analyst_growth_rate is not None:
                growth_rate = (cagr + analyst_growth_rate) / 2
            elif rev_cagr is not None and rev_cagr > 0:
                growth_rate = (cagr + rev_cagr) / 2
            else:
                growth_rate = cagr
        elif rev_cagr is not None and rev_cagr > 0:
            # FCF CAGR 不可信，用营收 CAGR
            growth_rate = rev_cagr
            if analyst_growth_rate is not None:
                growth_rate = (growth_rate + analyst_growth_rate) / 2
        elif analyst_growth_rate is not None:
            growth_rate = analyst_growth_rate
        else:
            # 兜底：用行业均值 8%
            growth_rate = 0.08
        growth_rate = max(0.0, min(0.25, growth_rate))

        # WACC
        # 从最新资产负债表获取有息负债 + 利息支出
        interest_expense = _safe(income[0].get("FINANCE_EXPENSE")) if income else 0
        total_debt = 0.0
        if balance:
            total_debt = (_safe(balance[0].get("SHORT_LOAN"))
                          + _safe(balance[0].get("LONG_LOAN"))
                          + _safe(balance[0].get("BOND_PAYABLE")))
        cash = _safe(balance[0].get("END_CASH") or balance[0].get("MONETARY_FUNDS")) if balance else 0

        wacc_result = calc_wacc(
            code=code,
            stock_returns=stock_returns,
            benchmark_returns=benchmark_returns,
            interest_expense=interest_expense,
            total_debt=total_debt,
            market_cap=market_cap,
        )
        if "error" in wacc_result:
            return DCFResult(code=code, insufficient_data=True, error=wacc_result["error"])
        wacc = max(self.wacc_min, min(self.wacc_max, wacc_result["wacc"]))

        # 总股本（若未提供，从 EPS + 净利润推导，或从市值/现价推导）
        if shares_outstanding <= 0:
            # 优先从 EPS + 归母净利润推导（最可靠）
            if income:
                eps = _safe(income[0].get("BASIC_EPS"))
                np_val = _safe(income[0].get("PARENT_NETPROFIT"))
                if eps > 0 and np_val > 0:
                    shares_outstanding = np_val / eps
            # 兜底：市值 / 现价
            if shares_outstanding <= 0 and market_cap > 0 and current_price > 0:
                shares_outstanding = market_cap / current_price

        # DCF 核心
        ev, equity_val, per_share = self._dcf_core(
            fcf_current=fcf_current,
            growth_rate=growth_rate,
            wacc=wacc,
            terminal_growth=tg,
            forecast_years=self.forecast_years,
            shares_outstanding=shares_outstanding,
            total_debt=total_debt,
            cash=cash,
        )

        # 公允价值区间（用敏感性矩阵的中心 3 格生成）
        sensitivity = self._sensitivity_matrix(
            fcf_current, growth_rate, shares_outstanding,
            total_debt, cash, wacc, tg
        )
        # 取中心格及四角
        center_wacc = f"{wacc*100:.1f}%"
        center_tg = f"{tg*100:.1f}%"
        center_val = sensitivity.get(center_wacc, {}).get(center_tg) or per_share
        # 用 ±1σ 的格作为 low/high
        low_wacc = f"{min(wacc + 0.01, 0.15)*100:.1f}%"
        low_tg = f"{max(tg - 0.005, 0)*100:.1f}%"
        high_wacc = f"{max(wacc - 0.01, 0.06)*100:.1f}%"
        high_tg = f"{tg + 0.005*100:.1f}%"
        low_val = sensitivity.get(low_wacc, {}).get(low_tg) or center_val * 0.8
        high_val = sensitivity.get(high_wacc, {}).get(high_tg) or center_val * 1.2
        fair_range = (round(min(low_val, center_val), 2),
                      round(center_val, 2),
                      round(max(high_val, center_val), 2))

        # 安全边际
        margin = 0.0
        recommendation = "中性"
        if current_price > 0 and center_val > 0:
            margin = (center_val - current_price) / center_val * 100
            if margin > 30:
                recommendation = "买入（安全边际充足）"
            elif margin > 10:
                recommendation = "观望（安全边际一般）"
            elif margin > -10:
                recommendation = "中性（估值合理）"
            elif margin > -20:
                recommendation = "高估"
            else:
                recommendation = "卖出（严重高估）"

        return DCFResult(
            code=code,
            intrinsic_value_per_share=round(center_val, 2),
            fair_value_range=fair_range,
            margin_of_safety_pct=round(margin, 1),
            recommendation=recommendation,
            current_price=current_price,
            wacc=round(wacc, 4),
            terminal_growth=tg,
            assumptions={
                "fcf_current": round(fcf_current, 2),
                "growth_rate": round(growth_rate * 100, 2),
                "wacc_pct": round(wacc * 100, 2),
                "terminal_growth_pct": round(tg * 100, 2),
                "forecast_years": self.forecast_years,
                "shares_outstanding": shares_outstanding,
                "total_debt": round(total_debt, 2),
                "cash": round(cash, 2),
                "wacc_components": wacc_result.get("assumptions", []),
            },
            sensitivity=sensitivity,
            fcf_history=[round(f, 2) for f in fcf_history],
            growth_rate=round(growth_rate * 100, 2),
            insufficient_data=False,
        )

    @staticmethod
    def format_report(result: DCFResult) -> str:
        if result.insufficient_data:
            return f"【{result.code}】DCF 估值：数据不足 - {result.error or ''}"
        lines = [
            f"【{result.code}】DCF 估值 - {result.recommendation}",
            "",
            f"■ 每股内在价值: ¥{result.intrinsic_value_per_share}",
            f"■ 公允价值区间: ¥{result.fair_value_range[0]} - ¥{result.fair_value_range[1]} - ¥{result.fair_value_range[2]}",
            f"■ 现价: ¥{result.current_price}",
            f"■ 安全边际: {result.margin_of_safety_pct}%",
            "",
            "■ 关键假设:",
            f"  • 当前 FCF: ¥{result.assumptions.get('fcf_current', 0)}",
            f"  • 阶段 1 增长率: {result.growth_rate}%",
            f"  • WACC: {result.assumptions.get('wacc_pct', 0)}%",
            f"  • 终值增长率: {result.assumptions.get('terminal_growth_pct', 0)}%",
            f"  • 预测年限: {result.assumptions.get('forecast_years', 5)} 年",
            "",
            "■ FCF 历史:",
        ]
        for i, f in enumerate(result.fcf_history):
            lines.append(f"  • 第{i+1}年: ¥{f}")
        lines.append("")
        lines.append("■ 敏感性分析（WACC × 终值增长）:")
        for wacc_key, row in result.sensitivity.items():
            cells = " | ".join(f"{tg}:{v}" if v else f"{tg}:N/A"
                                for tg, v in row.items())
            lines.append(f"  WACC {wacc_key}: {cells}")
        return "\n".join(lines)
