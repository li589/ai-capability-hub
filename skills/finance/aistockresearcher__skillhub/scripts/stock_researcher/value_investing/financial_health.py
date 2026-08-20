#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务健康检查（v5.0 新增）⭐

集成三大经典财务健康模型 + 6 维子评分：
- Altman Z-score: 破产预测模型（5 因子加权，>2.99 安全 / 1.81-2.99 灰色 / <1.81 危险）
- Piotroski F-score: 9 项 0/1 会计质量评分（F≥8 强 / F≤3 弱）
- Beneish M-score: 盈利操纵识别（8 项指数，M<-2.22 较安全 / M>-1.78 疑似操纵）
- 流动性 / 偿债能力 / 现金流质量

输出 0-100 综合评分 + A/B/C/D 评级 + red_flags 列表。
所有模型在数据不足时降级（仅用可用维度归一化），不伪装默认分。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..data.financial_statements import (
    fetch_income_statement,
    fetch_balance_sheet,
    fetch_cashflow_statement,
    fetch_financial_indicators,
    filter_recent_n_years,
)


@dataclass
class HealthResult:
    """财务健康检查结果"""
    code: str
    score: float = 0.0                    # 综合评分 0-100
    grade: str = "D"                      # A/B/C/D
    altman_z: Optional[float] = None
    piotroski_f: Optional[int] = None
    beneish_m: Optional[float] = None
    sub_scores: Dict[str, float] = field(default_factory=dict)
    red_flags: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    insufficient_data: bool = False


def _safe(val, default=0.0) -> float:
    try:
        f = float(val) if val is not None else default
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


class FinancialHealthChecker:
    """
    财务健康检查器。

    用法:
        checker = FinancialHealthChecker()
        result = checker.check("600519")
    """

    # 6 维权重（归一化）
    WEIGHTS = {
        "altman_z": 0.25,
        "piotroski_f": 0.25,
        "beneish_m": 0.15,
        "liquidity": 0.10,
        "solvency": 0.10,
        "cash_flow_quality": 0.15,
    }

    def __init__(self, years: int = 5):
        self.years = years

    # ─────────────────────────────────────────────
    # Altman Z-score（A 股适配版）
    # ─────────────────────────────────────────────
    def calc_altman_z(self, balance: List[dict], income: List[dict],
                      market_cap: float = 0.0) -> Optional[float]:
        """
        Z = 1.2×X1 + 1.4×X2 + 3.3×X3 + 0.6×X4 + 1.0×X5

        X1 = 营运资金 / 总资产 = (流动资产 - 流动负债) / 总资产
        X2 = 留存收益 / 总资产
        X3 = EBIT / 总资产 = (营业利润 + 财务费用) / 总资产
        X4 = 股权市值 / 总负债
        X5 = 营收 / 总资产
        """
        if not balance or not income:
            return None
        b = balance[0]  # 最新一期
        i = income[0]
        total_assets = _safe(b.get("TOTAL_ASSETS"))
        if total_assets <= 0:
            return None
        current_assets = _safe(b.get("TOTAL_CURRENT_ASSETS"))
        current_liab = _safe(b.get("TOTAL_CURRENT_LIAB"))
        retained = _safe(b.get("UNDISTRIBUTED_PROFIT") or b.get("RETAINED_EARNINGS"))
        total_liab = _safe(b.get("TOTAL_LIABILITIES"))
        ebit = _safe(i.get("OPERATE_PROFIT")) + _safe(i.get("FINANCE_EXPENSE"))
        revenue = _safe(i.get("TOTAL_OPERATE_INCOME") or i.get("OPERATE_INCOME"))

        x1 = (current_assets - current_liab) / total_assets
        x2 = retained / total_assets
        x3 = ebit / total_assets
        # X4：优先用市值，缺失则用股东权益近似
        x4 = (market_cap / total_liab) if (market_cap > 0 and total_liab > 0) \
            else (_safe(b.get("TOTAL_PARENT_EQUITY")) / total_liab if total_liab > 0 else 0)
        x5 = revenue / total_assets

        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5
        return z

    # ─────────────────────────────────────────────
    # Piotroski F-score
    # ─────────────────────────────────────────────
    def calc_piotroski_f(self, indicators: List[dict],
                         balance: List[dict], income: List[dict],
                         cashflow: List[dict]) -> Optional[int]:
        """
        9 项 0/1 评分:
        盈利能力: ROA>0, ΔROA>0, CFO>0, CFO>NI
        杠杆/融资: Δ长期负债比率<0, Δ流动比率>0, 无增发
        效率: Δ毛利率>0, Δ资产周转率>0
        """
        if len(indicators) < 2 or len(balance) < 2 or len(income) < 2:
            return None
        cur, prev = indicators[0], indicators[1]
        cur_b, prev_b = balance[0], balance[1]
        cur_i, prev_i = income[0], income[1]
        cf = cashflow[0] if cashflow else {}

        f = 0
        # 盈利能力
        roa = _safe(cur.get("ROA") or cur.get("ROEJQ"))
        roa_prev = _safe(prev.get("ROA") or prev.get("ROEJQ"))
        if roa > 0:
            f += 1
        if roa > roa_prev:
            f += 1
        cfo = _safe(cf.get("NETCASH_OPERATE"))
        if cfo > 0:
            f += 1
        # CFO > NI
        netprofit = _safe(cur_i.get("PARENT_NETPROFIT") or cur_i.get("NETPROFIT"))
        if cfo > netprofit and netprofit > 0:
            f += 1
        # 杠杆
        cur_debt_ratio = _safe(cur.get("DEBT_ASSET_RATIO") or cur.get("ZCFZL"))
        prev_debt_ratio = _safe(prev.get("DEBT_ASSET_RATIO") or prev.get("ZCFZL"))
        if cur_debt_ratio < prev_debt_ratio:
            f += 1
        cur_current = _safe(cur_b.get("TOTAL_CURRENT_ASSETS")) / max(_safe(cur_b.get("TOTAL_CURRENT_LIAB")), 1)
        prev_current = _safe(prev_b.get("TOTAL_CURRENT_ASSETS")) / max(_safe(prev_b.get("TOTAL_CURRENT_LIAB")), 1)
        if cur_current > prev_current:
            f += 1
        # 无增发：总股本不变（用归母权益变化 vs 净利润累加近似）
        cur_equity = _safe(cur_b.get("TOTAL_PARENT_EQUITY"))
        prev_equity = _safe(prev_b.get("TOTAL_PARENT_EQUITY"))
        if prev_equity > 0 and netprofit > 0:
            # 权益增加 ≤ 净利润 -> 视为无增发
            if cur_equity - prev_equity <= netprofit * 1.05:
                f += 1
        # 效率
        cur_gm = _safe(cur.get("GROSS_PROFIT_RATIO") or cur.get("XSJLL"))
        prev_gm = _safe(prev.get("GROSS_PROFIT_RATIO") or prev.get("XSJLL"))
        if cur_gm > prev_gm:
            f += 1
        cur_rev = _safe(cur_i.get("TOTAL_OPERATE_INCOME"))
        prev_rev = _safe(prev_i.get("TOTAL_OPERATE_INCOME"))
        cur_ta = _safe(cur_b.get("TOTAL_ASSETS"))
        prev_ta = _safe(prev_b.get("TOTAL_ASSETS"))
        if prev_ta > 0 and prev_rev > 0:
            cur_turn = cur_rev / max(cur_ta, 1)
            prev_turn = prev_rev / max(prev_ta, 1)
            if cur_turn > prev_turn:
                f += 1
        return f

    # ─────────────────────────────────────────────
    # Beneish M-score
    # ─────────────────────────────────────────────
    def calc_beneish_m(self, income: List[dict], balance: List[dict],
                       cashflow: List[dict]) -> Optional[float]:
        """
        M = -4.84 + 0.92×DSRI + 0.528×GMI + 0.404×AQI + 0.892×SGI
              + 0.115×DEPI - 0.172×SGAI + 4.679×TATA - 0.327×LVGI

        ⚠️ Beneish 模型对输入字段极敏感，当 OPERATE_COST/SALE_EXPENSE/MANAGE_EXPENSE 等
        为派生值或 0 时结果不可靠，此时返回 None 而非误导性分数。
        """
        if len(income) < 2 or len(balance) < 2:
            return None
        cur_i, prev_i = income[0], income[1]
        cur_b, prev_b = balance[0], balance[1]
        cur_cf = cashflow[0] if cashflow else {}

        # 数据质量检查：若关键字段为 0（派生/缺失），Beneish 结果不可靠
        if (_safe(cur_i.get("SALE_EXPENSE")) == 0
                and _safe(cur_i.get("MANAGE_EXPENSE")) == 0):
            # SGAI 无法计算，跳过 Beneish
            return None

        def _ratio(a, b):
            return a / b if abs(b) > 1e-9 else 1.0

        # DSRI
        cur_ar = _safe(cur_b.get("ACCOUNTS_RECE"))
        prev_ar = _safe(prev_b.get("ACCOUNTS_RECE"))
        cur_rev = _safe(cur_i.get("TOTAL_OPERATE_INCOME"))
        prev_rev = _safe(prev_i.get("TOTAL_OPERATE_INCOME"))
        cur_ar_turn = cur_rev / max(cur_ar, 1)
        prev_ar_turn = prev_rev / max(prev_ar, 1)
        dsri = _ratio(cur_ar_turn, prev_ar_turn)
        # GMI
        cur_gm = (_safe(cur_i.get("TOTAL_OPERATE_INCOME")) - _safe(cur_i.get("OPERATE_COST"))) / max(cur_rev, 1)
        prev_gm = (prev_rev - _safe(prev_i.get("OPERATE_COST"))) / max(prev_rev, 1)
        gmi = _ratio(prev_gm, cur_gm)
        # AQI
        cur_aq = (1 - (_safe(cur_b.get("TOTAL_CURRENT_ASSETS")) + _safe(cur_b.get("FIXED_ASSET"))) / max(_safe(cur_b.get("TOTAL_ASSETS")), 1))
        prev_aq = (1 - (_safe(prev_b.get("TOTAL_CURRENT_ASSETS")) + _safe(prev_b.get("FIXED_ASSET"))) / max(_safe(prev_b.get("TOTAL_ASSETS")), 1))
        aqi = _ratio(cur_aq, prev_aq)
        # SGI
        sgi = _ratio(cur_rev, prev_rev)
        # DEPI（简化：用固定资产/总资产代替折旧率）
        cur_dep = _safe(cur_b.get("FIXED_ASSET")) / max(_safe(cur_b.get("TOTAL_ASSETS")), 1)
        prev_dep = _safe(prev_b.get("FIXED_ASSET")) / max(_safe(prev_b.get("TOTAL_ASSETS")), 1)
        depi = _ratio(prev_dep, cur_dep)
        # SGAI
        cur_sga = _safe(cur_i.get("SALE_EXPENSE")) + _safe(cur_i.get("MANAGE_EXPENSE"))
        prev_sga = _safe(prev_i.get("SALE_EXPENSE")) + _safe(prev_i.get("MANAGE_EXPENSE"))
        sgai = _ratio(cur_sga / max(cur_rev, 1), prev_sga / max(prev_rev, 1))
        # TATA
        cfo = _safe(cur_cf.get("NETCASH_OPERATE"))
        netprofit = _safe(cur_i.get("NETPROFIT"))
        ta = _safe(cur_b.get("TOTAL_ASSETS"))
        tata = (netprofit - cfo) / max(ta, 1)
        # LVGI
        cur_lev = _safe(cur_b.get("TOTAL_LIABILITIES")) / max(_safe(cur_b.get("TOTAL_ASSETS")), 1)
        prev_lev = _safe(prev_b.get("TOTAL_LIABILITIES")) / max(_safe(prev_b.get("TOTAL_ASSETS")), 1)
        lvgi = _ratio(cur_lev, prev_lev)

        m = (-4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi
             + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi)
        return m

    # ─────────────────────────────────────────────
    # 子评分映射到 0-100
    # ─────────────────────────────────────────────
    @staticmethod
    def _altman_z_to_score(z: Optional[float]) -> Optional[float]:
        if z is None:
            return None
        # >2.99 安全(100), 1.81-2.99 灰色(50), <1.81 危险(10)
        if z >= 2.99:
            return min(100, 60 + (z - 2.99) * 15)
        if z >= 1.81:
            return 30 + (z - 1.81) / (2.99 - 1.81) * 30
        return max(0, z / 1.81 * 30)

    @staticmethod
    def _piotroski_f_to_score(f: Optional[int]) -> Optional[float]:
        if f is None:
            return None
        # 9 项满分 -> 100, 0 项 -> 0
        return f / 9 * 100

    @staticmethod
    def _beneish_m_to_score(m: Optional[float]) -> Optional[float]:
        if m is None:
            return None
        # M < -2.22 安全(100), -2.22 ~ -1.78 灰色(50), > -1.78 疑似操纵(0)
        if m <= -2.22:
            return min(100, 70 + (-2.22 - m) * 30)
        if m <= -1.78:
            return 30 + (-1.78 - m) / (-1.78 + 2.22) * 40
        return max(0, 30 - (m + 1.78) * 50)

    def _calc_liquidity_score(self, balance: List[dict],
                              indicators: List[dict]) -> Optional[float]:
        if not balance or not indicators:
            return None
        b = balance[0]
        cur_assets = _safe(b.get("TOTAL_CURRENT_ASSETS"))
        cur_liab = _safe(b.get("TOTAL_CURRENT_LIAB"))
        if cur_liab <= 0:
            return None
        current_ratio = cur_assets / cur_liab
        # 流动比率 2.0 为 100 分；1.0 为 50 分；<0.5 为 10 分
        score = min(100, current_ratio / 2.0 * 100)
        # 趋势：5Y 流动比率是否稳定
        if len(indicators) >= 3:
            ratios = []
            for ind in indicators[:min(5, len(indicators))]:
                # ZYLB 指标可能没有，用流动比率字段名兜底
                r = _safe(ind.get("CURRENT_RATIO") or ind.get("LDBL"))
                if r > 0:
                    ratios.append(r)
            if len(ratios) >= 2:
                std = (sum((r - sum(ratios)/len(ratios))**2 for r in ratios) / len(ratios)) ** 0.5
                # 标准差越大扣分
                score -= min(20, std * 5)
        return max(0, min(100, score))

    def _calc_solvency_score(self, balance: List[dict],
                             income: List[dict],
                             indicators: List[dict]) -> Optional[float]:
        if not balance or not income:
            return None
        b = balance[0]
        i = income[0]
        debt_ratio = _safe(b.get("TOTAL_LIABILITIES")) / max(_safe(b.get("TOTAL_ASSETS")), 1)
        # 资产负债率：30% 为 100 分，60% 为 50 分，>80% 为 10 分
        if debt_ratio <= 0.3:
            score = 100
        elif debt_ratio <= 0.6:
            score = 50 + (0.6 - debt_ratio) / 0.3 * 50
        else:
            score = max(10, 50 - (debt_ratio - 0.6) / 0.4 * 40)
        # 利息保障倍数
        ebit = _safe(i.get("OPERATE_PROFIT")) + _safe(i.get("FINANCE_EXPENSE"))
        interest = _safe(i.get("FINANCE_EXPENSE"))
        if interest > 0:
            coverage = ebit / interest
            if coverage >= 10:
                score = min(100, score + 20)
            elif coverage >= 3:
                score = min(100, score + 10)
            elif coverage < 1:
                score = max(0, score - 30)
        return max(0, min(100, score))

    def _calc_cash_flow_quality_score(self, cashflow: List[dict],
                                      income: List[dict]) -> Optional[float]:
        if not cashflow or not income:
            return None
        cf = cashflow[0]
        i = income[0]
        cfo = _safe(cf.get("NETCASH_OPERATE"))
        netprofit = _safe(i.get("PARENT_NETPROFIT") or i.get("NETPROFIT"))
        if netprofit <= 0:
            return 50 if cfo > 0 else 20
        # OCF/NI 比率：>=1 为 100 分；0.5-1 为 60 分；<0 为 10 分
        ratio = cfo / netprofit
        if ratio >= 1.0:
            score = min(100, 80 + (ratio - 1) * 20)
        elif ratio >= 0.5:
            score = 40 + (ratio - 0.5) / 0.5 * 40
        else:
            score = max(0, ratio * 80)
        # FCF 趋势（5Y）
        if len(cashflow) >= 3:
            pos_count = sum(1 for c in cashflow[:min(5, len(cashflow))]
                            if _safe(c.get("NETCASH_OPERATE")) - _safe(c.get("BUY_FIX_ASSET_OTHER")) > 0)
            score = score * 0.7 + (pos_count / min(5, len(cashflow)) * 100) * 0.3
        return max(0, min(100, score))

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────
    def check(self, code: str, market_cap: float = 0.0,
              financials: Optional[dict] = None) -> HealthResult:
        """
        执行完整财务健康检查。

        Args:
            code: 股票代码
            market_cap: 股权市值（元）；用于 Altman Z 的 X4
            financials: 预取的财务数据（避免重复网络请求）；None 时自动获取
        """
        if financials is None:
            financials = {
                "income": fetch_income_statement(code, self.years),
                "balance": fetch_balance_sheet(code, self.years),
                "cashflow": fetch_cashflow_statement(code, self.years),
                "indicators": fetch_financial_indicators(code, self.years),
            }
        income = filter_recent_n_years(financials.get("income", []), self.years)
        balance = filter_recent_n_years(financials.get("balance", []), self.years)
        cashflow = filter_recent_n_years(financials.get("cashflow", []), self.years)
        indicators = filter_recent_n_years(financials.get("indicators", []), self.years)

        if not income or not balance:
            return HealthResult(code=code, insufficient_data=True,
                                evidence=["利润表或资产负债表数据不足"])

        # 三大模型
        altman_z = self.calc_altman_z(balance, income, market_cap)
        piotroski_f = self.calc_piotroski_f(indicators, balance, income, cashflow)
        beneish_m = self.calc_beneish_m(income, balance, cashflow)

        # 6 维子评分
        sub_scores: Dict[str, Optional[float]] = {
            "altman_z": self._altman_z_to_score(altman_z),
            "piotroski_f": self._piotroski_f_to_score(piotroski_f),
            "beneish_m": self._beneish_m_to_score(beneish_m),
            "liquidity": self._calc_liquidity_score(balance, indicators),
            "solvency": self._calc_solvency_score(balance, income, indicators),
            "cash_flow_quality": self._calc_cash_flow_quality_score(cashflow, income),
        }

        # 加权求和（仅用可用维度归一化）
        available = {k: v for k, v in sub_scores.items() if v is not None}
        if not available:
            return HealthResult(code=code, insufficient_data=True,
                                evidence=["6 个维度均无数据"])

        weight_sum = sum(self.WEIGHTS[k] for k in available)
        score = sum(self.WEIGHTS[k] * available[k] for k in available) / max(weight_sum, 1e-9)

        # 评级
        grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"

        # Red flags
        red_flags: List[str] = []
        if altman_z is not None and altman_z < 1.81:
            red_flags.append(f"Altman Z-score = {altman_z:.2f}，处于破产危险区（<1.81）")
        if piotroski_f is not None and piotroski_f <= 3:
            red_flags.append(f"Piotroski F-score = {piotroski_f}/9，财务质量弱（≤3）")
        if beneish_m is not None and beneish_m > -1.78:
            red_flags.append(f"Beneish M-score = {beneish_m:.2f}，疑似盈利操纵（>-1.78）")
        if cashflow:
            cfo = _safe(cashflow[0].get("NETCASH_OPERATE"))
            if cfo < 0:
                red_flags.append("最近一期经营现金流为负")
            # 连续 2 年 OCF 为负
            if len(cashflow) >= 2:
                cfo_prev = _safe(cashflow[1].get("NETCASH_OPERATE"))
                if cfo < 0 and cfo_prev < 0:
                    red_flags.append("连续 2 年经营现金流为负")
        if balance:
            goodwill = _safe(balance[0].get("GOODWILL"))
            total_assets = _safe(balance[0].get("TOTAL_ASSETS"))
            if total_assets > 0 and goodwill / total_assets > 0.3:
                red_flags.append(f"商誉占总资产 {goodwill/total_assets*100:.1f}%，>30% 减值风险高")

        evidence: List[str] = []
        if altman_z is not None:
            evidence.append(f"Altman Z = {altman_z:.2f} ({'安全' if altman_z >= 2.99 else '灰色' if altman_z >= 1.81 else '危险'})")
        if piotroski_f is not None:
            evidence.append(f"Piotroski F = {piotroski_f}/9 ({'强' if piotroski_f >= 8 else '中' if piotroski_f >= 5 else '弱'})")
        if beneish_m is not None:
            evidence.append(f"Beneish M = {beneish_m:.2f} ({'安全' if beneish_m <= -2.22 else '灰色' if beneish_m <= -1.78 else '疑似操纵'})")

        return HealthResult(
            code=code,
            score=round(score, 1),
            grade=grade,
            altman_z=round(altman_z, 2) if altman_z is not None else None,
            piotroski_f=piotroski_f,
            beneish_m=round(beneish_m, 2) if beneish_m is not None else None,
            sub_scores={k: round(v, 1) for k, v in available.items()},
            red_flags=red_flags,
            evidence=evidence,
            insufficient_data=False,
        )

    @staticmethod
    def format_report(result: HealthResult) -> str:
        """格式化输出报告"""
        if result.insufficient_data:
            return f"【{result.code}】财务健康检查：数据不足，跳过"
        lines = [
            f"【{result.code}】财务健康检查 - 评级 {result.grade}（{result.score}/100）",
            "",
            "■ 三大模型:",
        ]
        if result.altman_z is not None:
            lines.append(f"  • Altman Z-score: {result.altman_z} ({'✅安全' if result.altman_z >= 2.99 else '⚠️灰色' if result.altman_z >= 1.81 else '🚨危险'})")
        if result.piotroski_f is not None:
            lines.append(f"  • Piotroski F-score: {result.piotroski_f}/9 ({'✅强' if result.piotroski_f >= 8 else '⚠️中' if result.piotroski_f >= 5 else '🚨弱'})")
        if result.beneish_m is not None:
            lines.append(f"  • Beneish M-score: {result.beneish_m} ({'✅安全' if result.beneish_m <= -2.22 else '⚠️灰色' if result.beneish_m <= -1.78 else '🚨疑似操纵'})")
        lines.append("")
        lines.append("■ 6 维子评分:")
        for k, v in result.sub_scores.items():
            label = {"altman_z": "Altman Z", "piotroski_f": "Piotroski F",
                     "beneish_m": "Beneish M", "liquidity": "流动性",
                     "solvency": "偿债能力", "cash_flow_quality": "现金流质量"}.get(k, k)
            lines.append(f"  • {label}: {v}/100")
        if result.red_flags:
            lines.append("")
            lines.append("■ 🚨 风险提示:")
            for flag in result.red_flags:
                lines.append(f"  • {flag}")
        return "\n".join(lines)
