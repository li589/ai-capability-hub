# -*- coding: utf-8 -*-
"""策略回测引擎 (v8.0 新增)
============================
支持三种回测模式:
  1. 历史组合模拟回测 — 给定持仓列表+调仓规则，模拟历史表现
  2. 策略回测 — 动量/均值回归/风险平价/股债轮动策略回测
  3. 基准对比 — vs 沪深300/中证全债等
  4. 情景压力测试 — 历史情景重演+自定义冲击

输出指标:
  - 收益指标: 累计收益、年化收益、各年度收益
  - 风险指标: 最大回撤（含日期和持续天数）、年化波动、下行波动
  - 风险调整: Sharpe、Sortino、Calmar、Information Ratio
  - 交易统计: 换手率、交易次数、交易成本合计
  - 滚动指标: 滚动1年收益、滚动夏普、滚动回撤

依赖: 纯标准库 (math/statistics/json/datetime/sqlite3)
"""
from __future__ import annotations

import math
import json
import statistics
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field

_SCRIPTS = Path(__file__).resolve().parents[1]
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from fund_advisor_paths import DATA_DIR, load_json_data  # noqa: E402
from data_collection.nav_cache import get_nav_cache, NavCache  # noqa: E402
from analysis import perf_metrics as pm  # noqa: E402

# ── 策略常量 ──────────────────────────────────────────────────
REBALANCE_FREQUENCIES = {
    "weekly": 5, "monthly": 22, "quarterly": 66,
    "semi_annual": 126, "annual": 252,
}

STRATEGIES = {
    "momentum": "动量策略 — 买入近N月强势基金，月度换仓",
    "mean_reversion": "均值回归 — 买入近N月弱势基金，季度换仓",
    "risk_parity": "风险平价 — 月度再平衡至等风险贡献",
    "equity_bond_rotation": "股债轮动 — 基于宏观指标切换股债配比",
    "buy_and_hold": "买入持有 — 不调仓，作为基准对比",
}

HISTORICAL_SCENARIOS = {
    "2008_gfc": {"name": "2008 全球金融危机", "equity_shock": -0.50, "bond_shock": 0.05, "duration_months": 18},
    "2015_crash": {"name": "2015 A股暴跌", "equity_shock": -0.40, "bond_shock": 0.03, "duration_months": 6},
    "2018_trade_war": {"name": "2018 贸易摩擦", "equity_shock": -0.25, "bond_shock": 0.06, "duration_months": 12},
    "2020_covid": {"name": "2020 疫情冲击", "equity_shock": -0.25, "bond_shock": 0.02, "duration_months": 3},
    "2022_bear": {"name": "2022 熊市", "equity_shock": -0.30, "bond_shock": -0.02, "duration_months": 10},
    "rate_hike_shock": {"name": "加息冲击 (+200bp)", "equity_shock": -0.15, "bond_shock": -0.08, "duration_months": 6},
    "credit_crisis": {"name": "信用危机 (+300bp利差)", "equity_shock": -0.20, "bond_shock": -0.12, "duration_months": 4},
}


# ── 数据模型 ──────────────────────────────────────────────────
@dataclass
class BacktestResult:
    """回测结果"""
    name: str = ""
    start_date: str = ""
    end_date: str = ""
    total_return_pct: float = 0.0
    annual_return_pct: float = 0.0
    annual_volatility_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    max_drawdown_start: str = ""
    max_drawdown_end: str = ""
    max_drawdown_days: int = 0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    win_rate_pct: float = 0.0  # 月度正收益比例
    total_trades: int = 0
    total_cost_pct: float = 0.0
    turnover_pct: float = 0.0  # 年化换手率
    benchmark_return_pct: float = 0.0
    excess_return_pct: float = 0.0
    information_ratio: float = 0.0
    tracking_error_pct: float = 0.0
    annual_returns: Dict[str, float] = field(default_factory=dict)
    rolling_1y_returns: List[float] = field(default_factory=list)
    rolling_sharpe: List[float] = field(default_factory=list)
    nav_series: List[float] = field(default_factory=list)
    benchmark_nav_series: List[float] = field(default_factory=list)
    trade_log: List[Dict] = field(default_factory=list)
    degraded: bool = False
    warnings: List[str] = field(default_factory=list)


@dataclass
class StressTestResult:
    """压力测试结果"""
    scenario_name: str = ""
    portfolio_loss_pct: float = 0.0
    equity_contribution_pct: float = 0.0
    bond_contribution_pct: float = 0.0
    other_contribution_pct: float = 0.0
    recovery_months_est: float = 0.0  # 估算恢复月数
    worst_holding: str = ""
    worst_holding_loss_pct: float = 0.0
    var_95_pct: float = 0.0
    cvar_95_pct: float = 0.0


# ── 回测引擎 ──────────────────────────────────────────────────
class BacktestEngine:
    """策略回测引擎 v8.0"""

    def __init__(self, nav_cache: Optional[NavCache] = None):
        self.nav_cache = nav_cache or get_nav_cache()
        self._fund_type_cache: Dict[str, str] = {}

    # ── 1. 组合历史回测 ──────────────────────────────────────
    def run_portfolio_backtest(
        self,
        holdings: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
        rebalance_rule: str = "quarterly",
        benchmark_code: str = "000300",
        initial_cash: float = 100000.0,
        subscription_fee_rate: float = 0.0015,  # 0.15% (1折后)
        redemption_fee_rate: float = 0.005,     # 0.5%
        management_fee_annual: float = 0.015,   # 1.5%/年
    ) -> BacktestResult:
        """历史组合模拟回测。

        Args:
            holdings: [{"fund_code": "000001", "weight": 50.0, "name": "XX基金"}, ...]
                      weight 单位: 百分比 (0-100)
            start_date: "2024-01-01"
            end_date: "2026-01-01"
            rebalance_rule: "weekly"/"monthly"/"quarterly"/"semi_annual"/"annual"
            benchmark_code: 基准基金/指数代码
            initial_cash: 初始资金

        Returns:
            BacktestResult 含所有指标 + NAV序列 + 交易日志
        """
        warnings: List[str] = []
        degraded = False

        # 1) 收集所有基金的净值序列
        fund_navs: Dict[str, List[float]] = {}
        fund_codes = [h.get("fund_code", "") for h in holdings if h.get("fund_code")]
        weights_pct = [h.get("weight", 100.0 / max(len(holdings), 1)) for h in holdings]

        if not fund_codes:
            return BacktestResult(name="空组合", warnings=["无有效基金代码"])

        for code in fund_codes:
            series = self.nav_cache.get_nav_series(code, start_date, end_date)
            if not series:
                warnings.append(f"{code} 无历史净值数据，使用成本常数序列")
                series = [1.0] * 252  # 降级为常数
                degraded = True
            fund_navs[code] = series

        # 2) 对齐长度（取最短的）
        min_len = min(len(v) for v in fund_navs.values())
        for code in fund_navs:
            fund_navs[code] = fund_navs[code][:min_len]
        if min_len < 2:
            return BacktestResult(name="数据不足", warnings=["净值序列长度<2"])

        # 3) 获取基准净值
        bench_series = self.nav_cache.get_nav_series(benchmark_code, start_date, end_date)
        if not bench_series:
            bench_series = [1.0] * min_len
            warnings.append(f"基准 {benchmark_code} 无数据，使用常数")

        # 4) 计算组合净值（加权求和）
        rebalance_freq = REBALANCE_FREQUENCIES.get(rebalance_rule, 66)
        portfolio_nav, trade_log, total_cost = self._simulate_portfolio(
            fund_navs, weights_pct, min_len, rebalance_freq,
            initial_cash, subscription_fee_rate, redemption_fee_rate,
            management_fee_annual
        )

        # 5) 计算指标
        result = self._compute_metrics(
            portfolio_nav, bench_series[:min_len],
            start_date, end_date, trade_log, total_cost,
            management_fee_annual
        )
        result.name = "组合回测"
        result.warnings = warnings
        result.degraded = degraded

        return result

    def _simulate_portfolio(
        self,
        fund_navs: Dict[str, List[float]],
        weights_pct: List[float],
        n_days: int,
        rebalance_freq: int,
        initial_cash: float,
        sub_fee: float,
        red_fee: float,
        mgmt_fee: float,
    ) -> Tuple[List[float], List[Dict], float]:
        """模拟组合净值序列。"""
        codes = list(fund_navs.keys())
        n_funds = len(codes)
        nav_series = [initial_cash]
        trade_log: List[Dict] = []
        total_cost = 0.0

        # 初始仓位（份额数）
        shares = []
        for i, code in enumerate(codes):
            init_nav = fund_navs[code][0]
            amount = initial_cash * weights_pct[i] / 100.0
            cost = amount * sub_fee
            total_cost += cost
            shares.append((amount - cost) / max(init_nav, 0.0001))
        trade_log.append({
            "date": "start", "action": "initial_buy",
            "details": [{"code": c, "shares": round(s, 2)} for c, s in zip(codes, shares)],
            "cost": round(total_cost, 2)
        })

        # 日度模拟
        mgmt_daily = mgmt_fee / 252
        for day in range(1, n_days):
            # 计算当日组合价值
            total_value = 0.0
            for i, code in enumerate(codes):
                nav = fund_navs[code][day]
                total_value += shares[i] * nav
            # 扣管理费
            total_value *= (1.0 - mgmt_daily)
            nav_series.append(total_value)

            # 再平衡日
            if day > 0 and day % rebalance_freq == 0:
                # 计算当前权重
                current_values = []
                for i, code in enumerate(codes):
                    current_values.append(shares[i] * fund_navs[code][day])
                total_v = sum(current_values)
                if total_v <= 0:
                    continue

                # 调整至目标权重
                rebalance_cost = 0.0
                for i, code in enumerate(codes):
                    target_amount = total_v * weights_pct[i] / 100.0
                    current_amount = current_values[i]
                    diff = target_amount - current_amount
                    if abs(diff) / max(total_v, 0.01) > 0.01:  # >1%才调
                        nav = fund_navs[code][day]
                        if diff > 0:  # 买入
                            cost = abs(diff) * sub_fee
                            rebalance_cost += cost
                            shares[i] += (abs(diff) - cost) / max(nav, 0.0001)
                        else:  # 卖出
                            cost = abs(diff) * red_fee
                            rebalance_cost += cost
                            shares[i] -= (abs(diff) + cost) / max(nav, 0.0001)
                            shares[i] = max(shares[i], 0)

                total_cost += rebalance_cost
                if rebalance_cost > 0:
                    trade_log.append({
                        "date": f"day_{day}", "action": "rebalance",
                        "cost": round(rebalance_cost, 2),
                    })

        return nav_series, trade_log, total_cost

    def _simulate_adaptive(self, fund_navs, codes, n_days, weights_at,
                           freq, initial_cash, sub_fee, red_fee, mgmt_fee):
        """v9.0: 支持按再平衡日动态目标权重的组合模拟（策略回测专用）。"""
        n_funds = len(codes)
        nav_series = [initial_cash]
        trade_log = []
        total_cost = 0.0

        init_weights = weights_at.get(0) or [1.0 / n_funds] * n_funds
        shares = []
        for i, code in enumerate(codes):
            init_nav = fund_navs[code][0]
            amount = initial_cash * init_weights[i]
            cost = amount * sub_fee
            total_cost += cost
            shares.append((amount - cost) / max(init_nav, 0.0001))

        mgmt_daily = mgmt_fee / 252
        for day in range(1, n_days):
            total_value = sum(shares[i] * fund_navs[code][day] for i, code in enumerate(codes))
            total_value *= (1.0 - mgmt_daily)
            nav_series.append(total_value)

            if day in weights_at and day > 0:
                target = weights_at[day]
                current_values = [shares[i] * fund_navs[code][day] for i, code in enumerate(codes)]
                total_v = sum(current_values)
                if total_v <= 0:
                    continue
                rebalance_cost = 0.0
                for i, code in enumerate(codes):
                    target_amount = total_v * target[i]
                    current_amount = current_values[i]
                    diff = target_amount - current_amount
                    if abs(diff) / max(total_v, 0.01) > 0.01:
                        nav = fund_navs[code][day]
                        if diff > 0:
                            cost = abs(diff) * sub_fee
                            rebalance_cost += cost
                            shares[i] += (abs(diff) - cost) / max(nav, 0.0001)
                        else:
                            cost = abs(diff) * red_fee
                            rebalance_cost += cost
                            shares[i] -= (abs(diff) + cost) / max(nav, 0.0001)
                            shares[i] = max(shares[i], 0)
                total_cost += rebalance_cost
                if rebalance_cost > 0:
                    trade_log.append({"date": f"day_{day}", "action": "rebalance",
                                      "cost": round(rebalance_cost, 2)})
        return nav_series, trade_log, total_cost

    # ── 2. 策略回测 ──────────────────────────────────────────
    def run_strategy_backtest(
        self,
        strategy: str,
        fund_universe: List[str],
        start_date: str,
        end_date: str,
        params: Optional[Dict[str, Any]] = None,
        benchmark_code: str = "000300",
    ) -> BacktestResult:
        """策略回测。

        Args:
            strategy: "momentum"/"mean_reversion"/"risk_parity"/"equity_bond_rotation"/"buy_and_hold"
            fund_universe: 候选基金代码列表
            start_date/end_date: 回测区间
            params: 策略参数 (如 lookback=3, hold_period=1)

        Returns:
            BacktestResult
        """
        p = params or {}

        if strategy == "momentum":
            return self._backtest_momentum(fund_universe, start_date, end_date, p, benchmark_code)
        elif strategy == "mean_reversion":
            return self._backtest_mean_reversion(fund_universe, start_date, end_date, p, benchmark_code)
        elif strategy == "risk_parity":
            return self._backtest_risk_parity(fund_universe, start_date, end_date, p, benchmark_code)
        elif strategy == "equity_bond_rotation":
            return self._backtest_rotation(fund_universe, start_date, end_date, p, benchmark_code)
        elif strategy == "buy_and_hold":
            return self._backtest_buy_and_hold(fund_universe, start_date, end_date, benchmark_code)
        else:
            return BacktestResult(name=strategy, warnings=[f"未知策略: {strategy}"])

    def _run_adaptive_backtest(self, universe, start, end, bench, name,
                               p, weight_fn, freq=None) -> BacktestResult:
        """v9.0: 通用自适应回测 — 按再平衡日动态权重模拟（策略回测真实实现）。"""
        navs = self._batch_get_nav(universe, start, end)
        if not navs:
            return BacktestResult(name=name, warnings=["无可用净值数据"], degraded=True)
        codes = list(navs.keys())
        min_len = min(len(v) for v in navs.values())
        navs = {c: v[:min_len] for c, v in navs.items()}
        if min_len < 2:
            return BacktestResult(name=name, warnings=["净值序列长度<2"], degraded=True)

        freq_days = freq or max(1, int(p.get("rebalance_months", 1) * 21))
        weights_at = {}
        for t in range(0, min_len, freq_days):
            w = weight_fn(navs, codes, t, p)
            if w and sum(w) > 0:
                weights_at[t] = w
        if not weights_at:
            weights_at[0] = [1.0 / len(codes)] * len(codes)

        nav_series, trade_log, cost = self._simulate_adaptive(
            navs, codes, min_len, weights_at, freq_days,
            initial_cash=100000.0, sub_fee=0.0015, red_fee=0.005, mgmt_fee=0.015)
        bench_series = self.nav_cache.get_nav_series(bench, start, end) or [1.0] * min_len
        r = self._compute_metrics(nav_series, bench_series[:min_len], start, end,
                                  trade_log, cost, 0.015)
        r.name = name
        return r

    @staticmethod
    def _momentum_weights(navs, codes, t, p):
        """动量权重：近 lookback 月收益最高 top_k 只等权。"""
        lookback = max(1, int(p.get("lookback", 3)) * 21)
        top_k = max(1, int(p.get("top_k", 3)))
        t0 = max(0, t - lookback)
        scores = []
        for c in codes:
            seq = navs[c]
            if t >= len(seq) or t0 >= t or seq[t0] <= 0:
                scores.append((float("-inf"), c))
                continue
            scores.append(((seq[t] - seq[t0]) / seq[t0], c))
        scores.sort(key=lambda x: -x[0])
        top = {c for _, c in scores[:top_k]}
        return [1.0 / top_k if c in top else 0.0 for c in codes]

    @staticmethod
    def _mean_reversion_weights(navs, codes, t, p):
        """均值回归权重：近 lookback 月最弱（超跌）top_k 只。"""
        lookback = max(1, int(p.get("lookback", 1)) * 21)
        top_k = max(1, int(p.get("top_k", 3)))
        t0 = max(0, t - lookback)
        scores = []
        for c in codes:
            seq = navs[c]
            if t >= len(seq) or t0 >= t or seq[t0] <= 0:
                scores.append((float("inf"), c))
                continue
            scores.append(((seq[t] - seq[t0]) / seq[t0], c))
        scores.sort(key=lambda x: x[0])
        top = {c for _, c in scores[:top_k]}
        return [1.0 / top_k if c in top else 0.0 for c in codes]

    @staticmethod
    def _risk_parity_weights(navs, codes, t, p):
        """风险平价权重：近 vol_window 日波动率倒数。"""
        import statistics
        vol_window = max(2, int(p.get("vol_window", 60)))
        t0 = max(0, t - vol_window)
        vols = []
        for c in codes:
            seq = navs[c]
            chunk = seq[t0:t + 1]
            if len(chunk) < 2:
                vols.append(0.0)
                continue
            rets = [(chunk[i] / max(chunk[i - 1], 1e-9) - 1) for i in range(1, len(chunk))]
            vols.append(statistics.pstdev(rets) if len(rets) > 1 else 0.0)
        inv = [1.0 / v if v > 1e-9 else 0.0 for v in vols]
        tot = sum(inv)
        if tot <= 0:
            return [1.0 / len(codes)] * len(codes)
        return [x / tot for x in inv]

    def _rotation_weights(self, navs, codes, t, p, bench_seq):
        """股债轮动权重：基准 12 月趋势定 regime — 牛市动量 / 熊市防御(低波动2只)。"""
        top_k = max(1, int(p.get("top_k", 2)))
        if bench_seq and t < len(bench_seq):
            b0 = bench_seq[max(0, t - 252)]
            if b0 > 0:
                trend = (bench_seq[t] - b0) / b0
                if trend > 0.02:  # 牛市 → 动量
                    return self._momentum_weights(navs, codes, t, {**p, "top_k": top_k, "lookback": 3})
                if trend < -0.02:  # 熊市 → 防御：低波动前 2 只
                    rp = self._risk_parity_weights(navs, codes, t, {**p, "vol_window": 60})
                    ranked = sorted(zip(codes, rp), key=lambda x: -x[1])
                    top = {c for c, _ in ranked[:2]}
                    return [0.5 if c in top else 0.0 for c in codes]
        # 震荡 → 动量（更分散）
        return self._momentum_weights(navs, codes, t, {**p, "top_k": max(2, top_k), "lookback": 3})

    def _backtest_momentum(self, universe, start, end, p, bench) -> BacktestResult:
        """动量策略：每月选近N月收益最高的前K只基金等权持有（v9.0 真实模拟）。"""
        return self._run_adaptive_backtest(
            universe, start, end, bench, f"动量策略(Top{p.get('top_k', 3)})",
            p, BacktestEngine._momentum_weights)

    def _backtest_mean_reversion(self, universe, start, end, p, bench) -> BacktestResult:
        """均值回归策略：买近N月最弱（超跌）基金（v9.0 真实模拟）。"""
        return self._run_adaptive_backtest(
            universe, start, end, bench, "均值回归策略",
            p, BacktestEngine._mean_reversion_weights)

    def _backtest_risk_parity(self, universe, start, end, p, bench) -> BacktestResult:
        """风险平价策略：波动率倒数权重（v9.0 真实模拟）。"""
        return self._run_adaptive_backtest(
            universe, start, end, bench, "风险平价策略",
            p, BacktestEngine._risk_parity_weights)

    def _backtest_rotation(self, universe, start, end, p, bench) -> BacktestResult:
        """股债轮动策略：基准趋势定 regime（v9.0 真实模拟）。"""
        bench_seq = self.nav_cache.get_nav_series(bench, start, end) or []
        return self._run_adaptive_backtest(
            universe, start, end, bench, "股债轮动策略",
            p, lambda navs, codes, t, pp: self._rotation_weights(navs, codes, t, pp, bench_seq))

    def _backtest_buy_and_hold(self, universe, start, end, bench) -> BacktestResult:
        """买入持有策略（等权）。"""
        holdings = [{"fund_code": c, "weight": 100.0 / len(universe)} for c in universe]
        return self.run_portfolio_backtest(holdings, start, end, rebalance_rule="annual",
                                           benchmark_code=bench)

    # ── 3. 对比回测 ──────────────────────────────────────────
    def compare_strategies(
        self,
        strategies: List[Dict[str, Any]],
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """对比多个策略/组合的回测结果。

        Args:
            strategies: [{"name": "策略A", "type": "portfolio", "holdings": [...]}, ...]

        Returns:
            {"results": [...], "best": "策略A", "best_sharpe": 1.23, ...}
        """
        all_results = []
        for s in strategies:
            s_type = s.get("type", "portfolio")
            if s_type == "portfolio":
                r = self.run_portfolio_backtest(
                    s.get("holdings", []), start_date, end_date,
                    rebalance_rule=s.get("rebalance", "quarterly"),
                    benchmark_code=s.get("benchmark", "000300"),
                )
            else:
                r = self.run_strategy_backtest(
                    s_type, s.get("universe", []), start_date, end_date,
                    params=s.get("params", {}),
                )
            r.name = s.get("name", s_type)
            all_results.append(r)

        best_sharpe = max((r.sharpe_ratio for r in all_results), default=0)
        best_calmar = max((r.calmar_ratio for r in all_results), default=0)

        return {
            "results": [_result_to_dict(r) for r in all_results],
            "count": len(all_results),
            "best_sharpe": best_sharpe,
            "best_calmar": best_calmar,
            "generated_at": datetime.now().isoformat(),
        }

    # ── 4. 压力测试 ──────────────────────────────────────────
    def stress_test(
        self,
        holdings: List[Dict[str, Any]],
        scenarios: Optional[List[str]] = None,
        custom_shock: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """组合压力测试。

        Args:
            holdings: 持仓列表
            scenarios: 预设情景列表（None=全部），可选: 2008_gfc, 2015_crash, ...
            custom_shock: 自定义冲击 {"equity": -0.20, "bond": -0.05}

        Returns:
            {"scenarios": [...], "worst_case_loss": -XX%, "var_95": -XX%}
        """
        if scenarios is None:
            scenarios = list(HISTORICAL_SCENARIOS.keys())

        # 分析持仓类型
        equity_weight, bond_weight, other_weight = self._classify_holdings(holdings)

        results = []
        for sc_name in scenarios:
            sc = HISTORICAL_SCENARIOS.get(sc_name)
            if not sc:
                continue
            equity_loss = equity_weight * abs(sc["equity_shock"])
            bond_loss = bond_weight * abs(sc["bond_shock"]) if sc["bond_shock"] < 0 else -bond_weight * sc["bond_shock"]
            total_loss = -(equity_loss + max(bond_loss, 0))
            monthly_return = sc["equity_shock"] / sc["duration_months"]

            recovery_months = abs(total_loss) / max(abs(monthly_return), 0.001) * 2  # 简单估算

            results.append(StressTestResult(
                scenario_name=sc["name"],
                portfolio_loss_pct=round(total_loss * 100, 2),
                equity_contribution_pct=round(equity_weight * 100, 1),
                bond_contribution_pct=round(bond_weight * 100, 1),
                other_contribution_pct=round(other_weight * 100, 1),
                recovery_months_est=round(recovery_months, 1),
                var_95_pct=round(total_loss * 100 * 1.2, 2),
                cvar_95_pct=round(total_loss * 100 * 1.5, 2),
            ))

        if custom_shock:
            eq = custom_shock.get("equity", 0)
            bd = custom_shock.get("bond", 0)
            total = -(equity_weight * abs(eq) + bond_weight * abs(bd))
            results.append(StressTestResult(
                scenario_name=f"自定义冲击(股{eq*100:.0f}%/债{bd*100:.0f}%)",
                portfolio_loss_pct=round(total * 100, 2),
                equity_contribution_pct=round(equity_weight * 100, 1),
                bond_contribution_pct=round(bond_weight * 100, 1),
                other_contribution_pct=round(other_weight * 100, 1),
                recovery_months_est=round(abs(total) / 0.05, 1),
            ))

        worst = min(results, key=lambda r: r.portfolio_loss_pct) if results else None

        return {
            "scenarios": [_stress_to_dict(r) for r in results],
            "count": len(results),
            "worst_case": _stress_to_dict(worst) if worst else {},
            "portfolio_composition": {
                "equity_weight_pct": round(equity_weight * 100, 1),
                "bond_weight_pct": round(bond_weight * 100, 1),
                "other_weight_pct": round(other_weight * 100, 1),
            },
            "generated_at": datetime.now().isoformat(),
        }

    def _classify_holdings(self, holdings: List[Dict]) -> Tuple[float, float, float]:
        """分类持仓为权益/债券/其他权重。"""
        equity_w = bond_w = other_w = 0.0
        total_w = sum(h.get("weight", 0) for h in holdings) or 1.0
        for h in holdings:
            code = h.get("fund_code", "")
            ftype = self._get_fund_type(code)
            w = h.get("weight", 0) / total_w
            if ftype in ("股票型", "偏股混合", "混合型", "指数型", "ETF", "QDII"):
                equity_w += w
            elif ftype in ("债券型", "纯债", "偏债混合"):
                bond_w += w
            else:
                other_w += w
        return equity_w, bond_w, other_w

    def _get_fund_type(self, code: str) -> str:
        """从 fund_products.json 获取基金类型。"""
        if code in self._fund_type_cache:
            return self._fund_type_cache[code]
        try:
            data = load_json_data("fund_products.json")
            items = data.get("products", data.get("items", []))
            for item in items:
                c = item.get("code", "") or item.get("fund_code", "")
                if c == code:
                    ftype = item.get("type", item.get("fund_type", "混合型"))
                    self._fund_type_cache[code] = ftype
                    return ftype
        except Exception:
            pass
        self._fund_type_cache[code] = "混合型"
        return "混合型"

    # ── 5. 指标计算 ──────────────────────────────────────────
    def _compute_metrics(
        self,
        nav_series: List[float],
        bench_series: List[float],
        start_date: str,
        end_date: str,
        trade_log: List[Dict],
        total_cost: float,
        mgmt_fee: float,
    ) -> BacktestResult:
        """计算所有回测指标。"""
        n = len(nav_series)
        if n < 2:
            return BacktestResult()

        initial = nav_series[0]
        final = nav_series[-1]
        total_ret = (final - initial) / initial

        # 年化收益
        days = max((datetime.strptime(end_date, "%Y-%m-%d") -
                     datetime.strptime(start_date, "%Y-%m-%d")).days, 1)
        years = days / 365.25
        annual_ret = (final / initial) ** (1 / max(years, 0.01)) - 1

        # 日收益序列
        daily_rets = []
        for i in range(1, n):
            if nav_series[i - 1] > 0:
                daily_rets.append((nav_series[i] - nav_series[i - 1]) / nav_series[i - 1])

        # 年化波动
        if daily_rets:
            daily_vol = statistics.stdev(daily_rets) if len(daily_rets) > 2 else 0
            annual_vol = daily_vol * math.sqrt(252)
        else:
            annual_vol = 0

        # 最大回撤 (v9.0 修复: pm.max_drawdown 返回 dict，兼容解包)
        mdd_result = pm.max_drawdown(nav_series) if hasattr(pm, 'max_drawdown') else None
        if isinstance(mdd_result, dict):
            mdd = float(mdd_result.get('mdd') or 0.0)
            mdd_start = mdd_result.get('peak_idx', 0)
            mdd_end = mdd_result.get('trough_idx', 0)
            mdd_days = mdd_result.get('duration_days', 0)
        elif isinstance(mdd_result, (list, tuple)) and len(mdd_result) >= 4:
            mdd, mdd_start, mdd_end, mdd_days = mdd_result
        else:
            mdd, mdd_start, mdd_end, mdd_days = self._calc_mdd(nav_series)

        # Sharpe (rf=2%)
        rf_annual = 0.02
        excess_annual = annual_ret - rf_annual
        sharpe = excess_annual / max(annual_vol, 0.001)

        # Sortino
        neg_rets = [r for r in daily_rets if r < 0]
        if neg_rets:
            down_vol = statistics.stdev(neg_rets) * math.sqrt(252) if len(neg_rets) > 2 else 0
            sortino = excess_annual / max(down_vol, 0.001)
        else:
            sortino = sharpe

        # Calmar
        calmar = annual_ret / max(abs(mdd), 0.001)

        # 月胜率
        monthly = self._to_monthly(nav_series)
        win_months = sum(1 for r in monthly if r > 0)
        win_rate = win_months / max(len(monthly), 1)

        # 交易统计
        total_trades = len([t for t in trade_log if t["action"] == "rebalance"])
        cost_pct = total_cost / initial
        turnover = total_trades / max(years, 0.01)  # 年化换手

        # 基准对比
        bench_ret = (bench_series[-1] - bench_series[0]) / max(bench_series[0], 0.01) if bench_series else 0
        excess_ret = total_ret - bench_ret
        info_ratio, te = self._calc_info_ratio(daily_rets, bench_series)

        # 滚动指标
        rolling_1y = self._rolling_returns(nav_series, 252)

        return BacktestResult(
            start_date=start_date, end_date=end_date,
            total_return_pct=round(total_ret * 100, 2),
            annual_return_pct=round(annual_ret * 100, 2),
            annual_volatility_pct=round(annual_vol * 100, 2),
            max_drawdown_pct=round(mdd * 100, 2),
            max_drawdown_start=mdd_start,
            max_drawdown_end=mdd_end,
            max_drawdown_days=mdd_days,
            sharpe_ratio=round(sharpe, 3),
            sortino_ratio=round(sortino, 3),
            calmar_ratio=round(calmar, 3),
            win_rate_pct=round(win_rate * 100, 1),
            total_trades=total_trades,
            total_cost_pct=round(cost_pct * 100, 2),
            turnover_pct=round(turnover, 0),
            benchmark_return_pct=round(bench_ret * 100, 2),
            excess_return_pct=round(excess_ret * 100, 2),
            information_ratio=round(info_ratio, 3),
            tracking_error_pct=round(te * 100, 2),
            nav_series=[round(v, 4) for v in nav_series],
            benchmark_nav_series=[round(v, 4) for v in bench_series],
            trade_log=trade_log,
            rolling_1y_returns=[round(r * 100, 2) for r in rolling_1y],
        )

    def _calc_mdd(self, nav: List[float]) -> Tuple[float, str, str, int]:
        """计算最大回撤 (幅度, 开始日期, 结束日期, 持续天数)。"""
        peak = nav[0]
        mdd = 0.0
        peak_idx = 0
        mdd_start = mdd_end = 0
        for i, v in enumerate(nav):
            if v > peak:
                peak = v
                peak_idx = i
            dd = (peak - v) / max(peak, 0.001)
            if dd > mdd:
                mdd = dd
                mdd_start = peak_idx
                mdd_end = i
        return (
            -mdd,
            f"day_{mdd_start}",
            f"day_{mdd_end}",
            mdd_end - mdd_start,
        )

    def _to_monthly(self, nav: List[float]) -> List[float]:
        """日序列 -> 月收益序列（简化：每21个交易日）。"""
        monthly = []
        for i in range(21, len(nav), 21):
            if nav[i - 21] > 0:
                monthly.append((nav[i] - nav[i - 21]) / nav[i - 21])
        return monthly

    def _rolling_returns(self, nav: List[float], window: int) -> List[float]:
        """滚动收益序列。"""
        rets = []
        for i in range(window, len(nav)):
            if nav[i - window] > 0:
                rets.append((nav[i] - nav[i - window]) / nav[i - window])
        return rets

    def _calc_info_ratio(self, port_rets: List[float], bench_nav: List[float]) -> Tuple[float, float]:
        """计算信息比率和跟踪误差。"""
        if len(port_rets) < 2 or len(bench_nav) < 2:
            return 0.0, 0.0
        # 计算基准日收益
        bench_rets = []
        for i in range(1, min(len(bench_nav), len(port_rets) + 1)):
            if bench_nav[i - 1] > 0:
                bench_rets.append((bench_nav[i] - bench_nav[i - 1]) / bench_nav[i - 1])
        n = min(len(port_rets), len(bench_rets))
        diffs = [port_rets[i] - bench_rets[i] for i in range(n)]
        if len(diffs) < 2:
            return 0.0, 0.0
        te = statistics.stdev(diffs) * math.sqrt(252)
        mean_diff = statistics.mean(diffs) * 252
        ir = mean_diff / max(te, 0.0001)
        return ir, te

    def _batch_get_nav(self, codes: List[str], start: str, end: str) -> Dict[str, List[float]]:
        """批量获取净值序列。"""
        result = {}
        for code in codes:
            series = self.nav_cache.get_nav_series(code, start, end)
            if series:
                result[code] = series
        return result


# ── 格式化输出 ──────────────────────────────────────────────
def _result_to_dict(r: BacktestResult) -> Dict[str, Any]:
    """BacktestResult -> 可序列化 dict。"""
    return {
        "name": r.name,
        "start_date": r.start_date, "end_date": r.end_date,
        "total_return_pct": r.total_return_pct,
        "annual_return_pct": r.annual_return_pct,
        "annual_volatility_pct": r.annual_volatility_pct,
        "max_drawdown_pct": r.max_drawdown_pct,
        "max_drawdown_days": r.max_drawdown_days,
        "sharpe_ratio": r.sharpe_ratio,
        "sortino_ratio": r.sortino_ratio,
        "calmar_ratio": r.calmar_ratio,
        "win_rate_pct": r.win_rate_pct,
        "total_trades": r.total_trades,
        "total_cost_pct": r.total_cost_pct,
        "turnover_pct": r.turnover_pct,
        "benchmark_return_pct": r.benchmark_return_pct,
        "excess_return_pct": r.excess_return_pct,
        "information_ratio": r.information_ratio,
        "tracking_error_pct": r.tracking_error_pct,
        "degraded": r.degraded,
        "warnings": r.warnings,
    }


def _stress_to_dict(s: StressTestResult) -> Dict[str, Any]:
    """StressTestResult -> dict。"""
    return {
        "scenario": s.scenario_name,
        "portfolio_loss_pct": s.portfolio_loss_pct,
        "equity_contribution_pct": s.equity_contribution_pct,
        "bond_contribution_pct": s.bond_contribution_pct,
        "recovery_months_est": s.recovery_months_est,
        "var_95_pct": s.var_95_pct,
        "cvar_95_pct": s.cvar_95_pct,
    }


def format_backtest_report(result: BacktestResult) -> str:
    """格式化 ASCII 回测报告。"""
    lines = [
        "=" * 64,
        f"  回测报告 — {result.name}",
        f"  区间: {result.start_date} → {result.end_date}",
        "=" * 64,
        "",
        "  ── 收益指标 ──",
        f"  累计收益:   {result.total_return_pct:>8.2f}%",
        f"  年化收益:   {result.annual_return_pct:>8.2f}%",
        f"  基准收益:   {result.benchmark_return_pct:>8.2f}%",
        f"  超额收益:   {result.excess_return_pct:>8.2f}%",
        "",
        "  ── 风险指标 ──",
        f"  年化波动:   {result.annual_volatility_pct:>8.2f}%",
        f"  最大回撤:   {result.max_drawdown_pct:>8.2f}% ({result.max_drawdown_days}天)",
        f"  跟踪误差:   {result.tracking_error_pct:>8.2f}%",
        "",
        "  ── 风险调整 ──",
        f"  Sharpe:     {result.sharpe_ratio:>8.3f}",
        f"  Sortino:    {result.sortino_ratio:>8.3f}",
        f"  Calmar:     {result.calmar_ratio:>8.3f}",
        f"  Info Ratio: {result.information_ratio:>8.3f}",
        "",
        "  ── 交易统计 ──",
        f"  交易次数:   {result.total_trades:>8}",
        f"  交易成本:   {result.total_cost_pct:>8.2f}%",
        f"  月胜率:     {result.win_rate_pct:>8.1f}%",
        "",
    ]
    if result.warnings:
        lines.append("  ⚠️ 警告:")
        for w in result.warnings:
            lines.append(f"    - {w}")
    if result.degraded:
        lines.append("  ⚠️ 数据降级: 部分或全部净值数据不可用，使用成本常数序列估算")
    lines.append("=" * 64)
    return "\n".join(lines)


# 模块级单例
_engine_instance: Optional[BacktestEngine] = None


def get_backtest_engine() -> BacktestEngine:
    """获取 BacktestEngine 单例。"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = BacktestEngine()
    return _engine_instance
