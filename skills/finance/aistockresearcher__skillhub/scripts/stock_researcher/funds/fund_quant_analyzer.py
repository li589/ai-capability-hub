# -*- coding: utf-8 -*-
"""
基金量化分析模块 v2.0（v9.3 增强）
Fund Quantitative Analysis

功能：
  1. 基金绩效归因（Alpha/Beta/Sharpe/Sortino/Treynor）
  2. 持仓风格分析（大盘/小盘/价值/成长）
  3. 基金经理能力评估（选股/择时/一致性）
  4. 基金对比排名
  5. 定投回测
  6. v9.3 新增：尾部风险（偏度/峰度/VaR）、回撤恢复期、滚动 Sharpe 稳定性、
     NAV 短期预测（动量漂移 + 波动率区间）

用法：
  from funds.fund_quant_analyzer import FundQuantAnalyzer
  fqa = FundQuantAnalyzer()
  result = fqa.analyze_fund(nav_series, benchmark_returns, risk_free_rate)
"""

import math
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FundPerformance:
    """基金绩效分析结果"""
    fund_name: str
    total_return: float  # 总回报 %
    annual_return: float  # 年化回报 %
    annual_volatility: float  # 年化波动率 %
    max_drawdown: float  # 最大回撤 %
    sharpe_ratio: float
    sortino_ratio: float
    alpha: float  # Jensen Alpha
    beta: float
    information_ratio: float
    win_rate: float  # 月度胜率 %
    avg_win: float  # 平均盈利 %
    avg_loss: float  # 平均亏损 %
    calmar_ratio: float
    omega_ratio: float
    rating: str  # A+/A/B/C/D
    score: float  # 0~100
    # v9.3 新增字段（带默认值，向后兼容）
    treynor_ratio: float = 0.0      # Treynor = (年化-无风险)/Beta
    skewness: float = 0.0           # 日收益偏度（负=左尾风险大）
    excess_kurtosis: float = 0.0    # 超额峰度（正=肥尾）
    var_5pct: float = 0.0           # 日度 5% 分位 VaR（负值，%）
    recovery_days: int = 0          # 最大回撤谷底至今的恢复天数
    dd_recovered: bool = True       # 最大回撤是否已收复
    stability: float = 50.0         # 滚动 Sharpe 方向稳定性 0~100


class FundQuantAnalyzer:
    """基金量化分析器"""

    def analyze_fund(self, nav_series: List[float],
                     benchmark_returns: List[float] = None,
                     risk_free_rate: float = 0.025,
                     fund_name: str = "未命名基金") -> FundPerformance:
        """综合基金绩效分析。

        Args:
            nav_series: 基金净值序列（日度）
            benchmark_returns: 基准日收益率序列（如沪深300）
            risk_free_rate: 无风险利率（年化），默认2.5%
            fund_name: 基金名称
        """
        if not nav_series or len(nav_series) < 60:
            return FundPerformance(fund_name, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "C", 30)

        returns = self._calc_daily_returns(nav_series)
        n = len(returns)
        rf_daily = risk_free_rate / 252

        # 1. 收益率
        total_return = (nav_series[-1] / nav_series[0] - 1) * 100
        annual_return = ((nav_series[-1] / nav_series[0]) ** (252 / n) - 1) * 100

        # 2. 风险
        annual_vol = self._annual_volatility(returns)
        max_dd = self._max_drawdown(nav_series)

        # 3. Sharpe
        excess = [r - rf_daily for r in returns]
        avg_excess = sum(excess) / n
        std_excess = (sum((e - avg_excess) ** 2 for e in excess) / (n - 1)) ** 0.5
        sharpe = (avg_excess / std_excess * math.sqrt(252)) if std_excess > 0 else 0

        # 4. Sortino
        downside = [min(0, e) ** 2 for e in excess]
        downside_std = (sum(downside) / n) ** 0.5
        sortino = (annual_return / 100 - risk_free_rate) / downside_std if downside_std > 0 else 0

        # 5. Alpha/Beta（如果有基准）
        alpha, beta, ir_ = 0, 1, 0
        if benchmark_returns and len(benchmark_returns) >= n:
            bm_rf = [b - rf_daily for b in benchmark_returns[-n:]]
            fund_rf = [r - rf_daily for r in returns]
            beta = self._calc_beta(fund_rf, bm_rf)
            alpha = self._calc_alpha(fund_rf, bm_rf, beta, rf_daily, n)
            ir_ = self._information_ratio(fund_rf, bm_rf, n)

        # 6. 胜率/盈亏比
        win_rate = sum(1 for r in returns if r > 0) / n * 100
        wins = [r for r in returns if r > 0]
        losses = [r for r in returns if r < 0]
        avg_win = sum(wins) / len(wins) * 100 if wins else 0
        avg_loss = sum(losses) / len(losses) * 100 if losses else 0

        # 7. Calmar / Omega
        calmar = annual_return / abs(max_dd) if max_dd != 0 else 0
        pos_sum = sum(r for r in returns if r > 0)
        neg_sum = abs(sum(r for r in returns if r < 0))
        omega = pos_sum / neg_sum if neg_sum > 0 else 99

        # 8. v9.3 尾部风险 / 回撤恢复 / 稳定性 / Treynor
        skew, kurt = self._skew_kurt(returns)
        var5 = self._empirical_quantile(returns, 0.05) * 100
        rec = self._drawdown_recovery(nav_series)
        stability = self._rolling_stability(returns, sharpe)
        treynor = ((annual_return / 100 - risk_free_rate) / beta
                   if beta > 1e-9 else 0.0)

        # 9. 综合评分
        score = self._calc_score(sharpe, sortino, annual_return, max_dd, alpha, calmar)
        # v9.3：肥尾/左尾风险小幅扣分，稳定性加分（±5 以内微调）
        score += min(2.0, max(-2.0, (stability - 50) * 0.04))
        if skew < -0.5:
            score -= 1.0
        if kurt > 3.0:
            score -= 1.0
        score = max(0, min(100, score))
        rating = self._score_to_rating(score)

        return FundPerformance(fund_name, round(total_return, 2), round(annual_return, 2),
                               round(annual_vol * 100, 2), round(max_dd, 2),
                               round(sharpe, 2), round(sortino, 2),
                               round(alpha * 100, 2), round(beta, 2),
                               round(ir_, 2), round(win_rate, 1),
                               round(avg_win, 2), round(avg_loss, 2),
                               round(calmar, 2), round(omega, 2), rating, round(score, 1),
                               round(treynor, 4), round(skew, 3), round(kurt, 3),
                               round(var5, 3), rec["recovery_days"], rec["recovered"],
                               round(stability, 1))

    def _calc_daily_returns(self, nav: List[float]) -> List[float]:
        return [(nav[i] / nav[i - 1] - 1) for i in range(1, len(nav))]

    def _annual_volatility(self, returns: List[float]) -> float:
        n = len(returns)
        avg = sum(returns) / n
        variance = sum((r - avg) ** 2 for r in returns) / (n - 1)
        return math.sqrt(variance * 252)

    def _max_drawdown(self, nav: List[float]) -> float:
        peak = nav[0]
        max_dd = 0
        for v in nav:
            if v > peak:
                peak = v
            dd = (v - peak) / peak * 100
            max_dd = min(max_dd, dd)
        return abs(max_dd)

    def _calc_beta(self, fund_rf: List[float], bm_rf: List[float]) -> float:
        n = min(len(fund_rf), len(bm_rf))
        f_avg = sum(fund_rf[:n]) / n
        b_avg = sum(bm_rf[:n]) / n
        cov = sum((fund_rf[i] - f_avg) * (bm_rf[i] - b_avg) for i in range(n)) / (n - 1)
        var = sum((b - b_avg) ** 2 for b in bm_rf[:n]) / (n - 1)
        return cov / var if var > 0 else 1

    def _calc_alpha(self, fund_rf, bm_rf, beta, rf_daily, n) -> float:
        n = min(len(fund_rf), len(bm_rf))
        f_avg = sum(fund_rf[:n]) / n
        b_avg = sum(bm_rf[:n]) / n
        return f_avg - (rf_daily + beta * (b_avg - rf_daily))

    def _information_ratio(self, fund_rf, bm_rf, n) -> float:
        n = min(len(fund_rf), len(bm_rf))
        diffs = [fund_rf[i] - bm_rf[i] for i in range(n)]
        avg_diff = sum(diffs) / n
        std_diff = (sum((d - avg_diff) ** 2 for d in diffs) / (n - 1)) ** 0.5
        return avg_diff / std_diff * math.sqrt(252) if std_diff > 0 else 0

    def _calc_score(self, sharpe: float, sortino: float, ann_ret: float,
                    max_dd: float, alpha: float, calmar: float) -> float:
        score = 50
        score += (sharpe - 0.5) * 15
        score += (sortino - 1) * 10
        score += (ann_ret - 5) * 1
        score += (10 - max_dd) * 0.5
        score += alpha * 3
        score += (calmar - 1) * 10
        return max(0, min(100, score))

    # ── v9.3 新增统计工具 ──────────────────────────────
    def _skew_kurt(self, returns: List[float]) -> Tuple[float, float]:
        """偏度 + 超额峰度（正态为 0）。"""
        n = len(returns)
        if n < 4:
            return 0.0, 0.0
        m = sum(returns) / n
        m2 = sum((r - m) ** 2 for r in returns) / n
        if m2 <= 0:
            return 0.0, 0.0
        m3 = sum((r - m) ** 3 for r in returns) / n
        m4 = sum((r - m) ** 4 for r in returns) / n
        skew = m3 / (m2 ** 1.5)
        kurt = m4 / (m2 ** 2) - 3.0
        return skew, kurt

    def _empirical_quantile(self, returns: List[float], q: float) -> float:
        """经验分位数（线性插值）。"""
        if not returns:
            return 0.0
        s = sorted(returns)
        if len(s) == 1:
            return s[0]
        idx = q * (len(s) - 1)
        lo = int(math.floor(idx))
        hi = min(lo + 1, len(s) - 1)
        frac = idx - lo
        return s[lo] * (1 - frac) + s[hi] * frac

    def _drawdown_recovery(self, nav: List[float]) -> Dict:
        """最大回撤谷底定位 + 恢复天数统计。"""
        peak = nav[0]
        peak_val_at_bottom = nav[0]
        max_dd = 0.0
        bottom_idx = 0
        for i, v in enumerate(nav):
            if v > peak:
                peak = v
            dd = (v - peak) / peak if peak > 0 else 0.0
            if dd < max_dd:
                max_dd = dd
                bottom_idx = i
                peak_val_at_bottom = peak
        if max_dd >= 0:
            return {"recovered": True, "recovery_days": 0}
        for j in range(bottom_idx, len(nav)):
            if nav[j] >= peak_val_at_bottom:
                return {"recovered": True, "recovery_days": j - bottom_idx}
        return {"recovered": False, "recovery_days": len(nav) - 1 - bottom_idx}

    def _rolling_stability(self, returns: List[float], overall_sharpe: float,
                           window: int = 60, step: int = 20) -> float:
        """滚动窗口 Sharpe 与整体方向一致的比例（0~100）。"""
        n = len(returns)
        if n < window or overall_sharpe == 0:
            return 50.0
        rf_daily = 0.025 / 252
        same = total = 0
        sign = 1 if overall_sharpe > 0 else -1
        for start in range(0, n - window + 1, step):
            seg = returns[start:start + window]
            avg = sum(seg) / window
            std = (sum((r - avg) ** 2 for r in seg) / (window - 1)) ** 0.5
            if std <= 0:
                continue
            total += 1
            if (avg - rf_daily) * sign > 0:
                same += 1
        return same / total * 100 if total > 0 else 50.0

    def forecast_nav(self, nav_series: List[float], days: int = 5,
                     drift_window: int = 20) -> Dict:
        """NAV 短期预测（v9.3）：近期动量漂移 + 80% 波动率区间。

        Returns:
            {data_mode, days, current_nav, predicted_nav, low, high,
             daily_drift_pct, daily_vol_pct, trend}
        """
        days = max(1, int(days))
        if not nav_series or len(nav_series) < 30:
            return {"data_mode": "insufficient", "days": days}
        returns = self._calc_daily_returns(nav_series)
        recent = returns[-min(drift_window, len(returns)):]
        mu = sum(recent) / len(recent)
        var = sum((r - mu) ** 2 for r in recent) / max(1, len(recent) - 1)
        sigma = math.sqrt(var)
        last = nav_series[-1]
        predicted = last * math.exp(mu * days)
        low = last * math.exp((mu - 1.2816 * sigma) * days)
        high = last * math.exp((mu + 1.2816 * sigma) * days)
        if mu > sigma * 0.2:
            trend = "up"
        elif mu < -sigma * 0.2:
            trend = "down"
        else:
            trend = "flat"
        return {
            "data_mode": "ok", "days": days,
            "current_nav": round(last, 4),
            "predicted_nav": round(predicted, 4),
            "low": round(low, 4), "high": round(high, 4),
            "daily_drift_pct": round(mu * 100, 3),
            "daily_vol_pct": round(sigma * 100, 3),
            "trend": trend,
        }

    def _score_to_rating(self, score: float) -> str:
        if score >= 85:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 65:
            return "B"
        elif score >= 50:
            return "C"
        return "D"

    def compare_funds(self, funds: List[Dict]) -> List[Dict]:
        """多基金对比排名。

        Args:
            funds: [{"name": str, "nav": List[float]}, ...]
        """
        results = []
        for f in funds:
            perf = self.analyze_fund(f["nav"], fund_name=f.get("name", "?"))
            results.append({
                "name": perf.fund_name,
                "annual_return": perf.annual_return,
                "max_drawdown": perf.max_drawdown,
                "sharpe": perf.sharpe_ratio,
                "alpha": perf.alpha,
                "score": perf.score,
                "rating": perf.rating,
            })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def dca_backtest(self, nav_series: List[float],
                     monthly_amount: float = 1000,
                     months: int = 36) -> Dict:
        """定投回测。

        Args:
            nav_series: 基金净值序列（日度，至少 months*22 条）
            monthly_amount: 每月定投金额
            months: 回测月数
        """
        days_needed = months * 22
        if len(nav_series) < days_needed:
            return {"error": "数据不足"}

        nav = nav_series[-days_needed:]
        total_units = 0
        total_invested = 0

        for i in range(0, len(nav), 22):
            price = nav[i]
            units = monthly_amount / price
            total_units += units
            total_invested += monthly_amount

        final_value = total_units * nav[-1]
        total_return = (final_value / total_invested - 1) * 100 if total_invested > 0 else 0

        return {
            "months": months,
            "total_invested": round(total_invested, 2),
            "final_value": round(final_value, 2),
            "total_return_pct": round(total_return, 2),
            "annualized_return": round(((final_value / total_invested) ** (12 / months) - 1) * 100, 2)
            if total_invested > 0 and months > 0 else 0,
        }

    def style_analysis(self, fund_returns: List[float],
                       factor_returns: Dict[str, List[float]]) -> Dict:
        """基金持仓风格归因。
        因子：大盘价值/大盘成长/小盘价值/小盘成长/债券/现金
        """
        # 简化版：计算与各因子指数的相关性
        corrs = {}
        n = min(len(fund_returns), *(len(v) for v in factor_returns.values()))
        for name, f_ret in factor_returns.items():
            if len(f_ret) >= n:
                corr = self._pearson_corr(fund_returns[:n], f_ret[:n])
                corrs[name] = round(corr, 3)

        if corrs:
            primary_style = max(corrs, key=lambda k: abs(corrs[k]))
        else:
            primary_style = "未知"

        return {"correlations": corrs, "primary_style": primary_style}

    def _pearson_corr(self, x: List[float], y: List[float]) -> float:
        n = min(len(x), len(y))
        if n < 3:
            return 0
        mx, my = sum(x[:n]) / n, sum(y[:n]) / n
        cov = sum((x[i] - mx) * (y[i] - my) for i in range(n))
        sx = (sum((v - mx) ** 2 for v in x[:n])) ** 0.5
        sy = (sum((v - my) ** 2 for v in y[:n])) ** 0.5
        return cov / (sx * sy) if sx > 0 and sy > 0 else 0


# ── 便捷函数 ──

def analyze_fund_performance(nav: List[float], benchmark: List[float] = None,
                             name: str = "") -> Dict:
    """一步式基金绩效分析。"""
    fqa = FundQuantAnalyzer()
    perf = fqa.analyze_fund(nav, benchmark, fund_name=name)
    return {
        "name": perf.fund_name, "annual_return": perf.annual_return,
        "max_drawdown": perf.max_drawdown, "sharpe": perf.sharpe_ratio,
        "sortino": perf.sortino_ratio, "alpha": perf.alpha, "beta": perf.beta,
        "calmar": perf.calmar_ratio, "win_rate": perf.win_rate,
        "score": perf.score, "rating": perf.rating,
        # v9.3 新增
        "treynor": perf.treynor_ratio, "skewness": perf.skewness,
        "excess_kurtosis": perf.excess_kurtosis, "var_5pct": perf.var_5pct,
        "recovery_days": perf.recovery_days, "dd_recovered": perf.dd_recovered,
        "stability": perf.stability,
    }


if __name__ == "__main__":
    import random
    random.seed(42)
    nav = [1.0]
    for _ in range(252 * 2):  # 2年
        nav.append(nav[-1] * (1 + random.gauss(0.0005, 0.008)))
    bm = [random.gauss(0.0003, 0.01) for _ in range(len(nav) - 1)]

    fqa = FundQuantAnalyzer()
    perf = fqa.analyze_fund(nav, bm, fund_name="测试基金")
    print(f"Fund: {perf.fund_name} rating={perf.rating} score={perf.score}")
    print(f"  annual={perf.annual_return}% max_dd={perf.max_drawdown}% sharpe={perf.sharpe}")
    print(f"  alpha={perf.alpha}% beta={perf.beta} calmar={perf.calmar}")

    dca = fqa.dca_backtest(nav, 1000, 24)
    print(f"  DCA 24m: return={dca.get('total_return_pct', 0)}%")
