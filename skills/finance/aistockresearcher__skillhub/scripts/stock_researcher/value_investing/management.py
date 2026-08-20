#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理层评估（v5.0 新增）

6 维度评估管理层质量：
1. ROE/ROIC 趋势（25%）- 杜邦分解定位驱动力
2. 资本配置（25%）- 回购/分红/再投资比例
3. 股本稀释（15%）- 增发频率与稀释程度
4. 股东结构（10%）- 实控人持股 + 机构持股
5. 治理代理（10%）- 独立董事占比 / 董事会规模
6. 信息披露质量（15%）- 商誉减值/非经常性损益/审计意见

输出 0-100 评分 + verdict (优秀/良好/一般/较差) + 证据链
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
    fetch_f10_shareholders,
    fetch_f10_dividends,
    fetch_f10_management,
    filter_recent_n_years,
)


@dataclass
class ManagementResult:
    """管理层评估结果"""
    code: str
    score: float = 0.0
    verdict: str = "一般"
    sub_scores: Dict[str, float] = field(default_factory=dict)
    dupont_breakdown: Dict = field(default_factory=dict)
    evidence: List[str] = field(default_factory=list)
    insufficient_data: bool = False


def _safe(val, default=0.0) -> float:
    try:
        f = float(val) if val is not None else default
        return f if math.isfinite(f) else default
    except (TypeError, ValueError):
        return default


class ManagementAssessment:
    """管理层评估器"""

    WEIGHTS = {
        "roe_roic_trend": 0.25,
        "capital_allocation": 0.25,
        "share_dilution": 0.15,
        "shareholder_structure": 0.10,
        "governance": 0.10,
        "disclosure_quality": 0.15,
    }

    def __init__(self, years: int = 5):
        self.years = years

    # ─────────────────────────────────────────────
    # 1. ROE/ROIC 趋势 + 杜邦分解
    # ─────────────────────────────────────────────
    def _roe_roic_trend(self, indicators: List[dict],
                        income: List[dict], balance: List[dict]) -> Optional[Dict]:
        """
        ROE 5Y 均值 >15% 且趋势上升 -> 高分
        杜邦分解: ROE = 净利率 × 资产周转率 × 权益乘数
        """
        if len(indicators) < 3:
            return None
        roes = []
        for ind in indicators[:min(self.years, len(indicators))]:
            roe = _safe(ind.get("ROE") or ind.get("ROEJQ"))
            if roe != 0:
                roes.append(roe)
        if len(roes) < 3:
            return None
        mean_roe = sum(roes) / len(roes)
        # 均值 >15% 满分；<5% 低分
        mean_score = max(0, min(100, (mean_roe - 5) / 10 * 100))
        # 趋势：用线性回归斜率
        n = len(roes)
        mean_x = (n - 1) / 2
        num = sum((i - mean_x) * (roes[i] - mean_roe) for i in range(n))
        den = sum((i - mean_x) ** 2 for i in range(n))
        slope = num / den if den > 0 else 0
        trend_score = max(0, min(100, 50 + slope * 10))

        # 杜邦分解
        dupont = {}
        if income and balance:
            i, b = income[0], balance[0]
            netprofit = _safe(i.get("PARENT_NETPROFIT"))
            revenue = _safe(i.get("TOTAL_OPERATE_INCOME"))
            ta = _safe(b.get("TOTAL_ASSETS"))
            equity = _safe(b.get("TOTAL_PARENT_EQUITY"))
            if revenue > 0 and ta > 0 and equity > 0:
                dupont = {
                    "net_margin": round(netprofit / revenue * 100, 2),
                    "asset_turnover": round(revenue / ta, 3),
                    "equity_multiplier": round(ta / equity, 3),
                    "roe": round(netprofit / equity * 100, 2),
                }

        score = max(0, min(100, mean_score * 0.6 + trend_score * 0.4))
        return {
            "score": score,
            "mean_roe": round(mean_roe, 2),
            "trend_slope": round(slope, 3),
            "dupont": dupont,
        }

    # ─────────────────────────────────────────────
    # 2. 资本配置
    # ─────────────────────────────────────────────
    def _capital_allocation(self, income: List[dict],
                            balance: List[dict],
                            dividends: List[dict]) -> Optional[Dict]:
        """
        分红率稳定性 + 累计分红比例 + 回购识别
        """
        if not income or not balance:
            return None
        # 分红率（最近 5 年）
        payout_ratios = []
        div_by_year = {}
        for d in dividends[:min(self.years, len(dividends))]:
            rdate = str(d.get("report_date", ""))[:4]
            if rdate:
                div_by_year[rdate] = div_by_year.get(rdate, 0) + _safe(d.get("total_amount"))

        for row in income[:min(self.years, len(income))]:
            rdate = str(row.get("report_date", ""))[:4]
            netprofit = _safe(row.get("PARENT_NETPROFIT"))
            div = div_by_year.get(rdate, 0)
            if netprofit > 0:
                payout_ratios.append(div / netprofit * 100)

        if not payout_ratios:
            # 无分红数据：中性偏负（保守起见扣分）
            return {"score": 40, "avg_payout": 0, "stable": False, "note": "无分红记录"}

        avg_payout = sum(payout_ratios) / len(payout_ratios)
        # 分红率 30-60% 为优秀（稳健）；>80% 可能缺乏增长空间；<10% 偏低
        if 30 <= avg_payout <= 60:
            score = 90
        elif 20 <= avg_payout < 30 or 60 < avg_payout <= 80:
            score = 70
        elif avg_payout > 80:
            score = 50  # 高分红但可能缺乏增长投入
        else:
            score = max(0, avg_payout * 2)
        # 稳定性
        if len(payout_ratios) >= 3:
            std = (sum((r - avg_payout) ** 2 for r in payout_ratios) / len(payout_ratios)) ** 0.5
            if std < 10:
                score = min(100, score + 10)
            elif std > 25:
                score = max(0, score - 10)

        return {
            "score": score,
            "avg_payout": round(avg_payout, 2),
            "stable": len(payout_ratios) >= 3 and std < 10 if len(payout_ratios) >= 3 else False,
        }

    # ─────────────────────────────────────────────
    # 3. 股本稀释
    # ─────────────────────────────────────────────
    def _share_dilution(self, balance: List[dict]) -> Optional[Dict]:
        """5Y 总股本变化"""
        if len(balance) < 3:
            return None
        # 用归母权益 / 总股本近似每股净资产，反推股本变化
        # 或用 TOTAL_PARENT_EQUITY 的变化 vs 净利润累加
        equities = [_safe(b.get("TOTAL_PARENT_EQUITY")) for b in balance[:min(self.years, len(balance))]]
        equities = [e for e in equities if e > 0]
        if len(equities) < 3:
            return None
        # 5Y 权益变化率（粗略稀释代理）
        dilution = (equities[0] - equities[-1]) / equities[-1] * 100
        # 正值表示权益增长（可能来自利润留存，是好信号）
        # 但需要扣除利润贡献 - 这里简化处理
        if dilution >= 100:
            score = 60  # 大幅增长，需进一步判断是否来自增发
        elif dilution >= 50:
            score = 80
        elif dilution >= 20:
            score = 70
        elif dilution >= 0:
            score = 60
        else:
            score = max(0, 50 + dilution)  # 负增长扣分
        return {
            "score": score,
            "equity_growth_pct": round(dilution, 2),
        }

    # ─────────────────────────────────────────────
    # 4. 股东结构
    # ─────────────────────────────────────────────
    def _shareholder_structure(self, shareholders: dict) -> Optional[Dict]:
        """实控人持股 + 机构持股"""
        if not shareholders or "error" in shareholders:
            return None
        controller_pct = 0
        # 从 top10 中估算实控人持股（简化：取第一大股东）
        top10 = shareholders.get("top10", [])
        if top10:
            controller_pct = top10[0].get("pct", 0)
        inst_pct = shareholders.get("institutional_pct", 0)
        # 实控人持股 30-60% 为优（既稳定又不过度集中）；<10% 或 >80% 扣分
        if 30 <= controller_pct <= 60:
            controller_score = 90
        elif 20 <= controller_pct < 30 or 60 < controller_pct <= 80:
            controller_score = 70
        elif controller_pct > 80:
            controller_score = 50
        else:
            controller_score = max(0, controller_pct * 3)
        # 机构持股 10-40% 为优
        if 10 <= inst_pct <= 40:
            inst_score = 90
        elif inst_pct > 40:
            inst_score = 70
        else:
            inst_score = max(0, inst_pct * 5)
        score = controller_score * 0.6 + inst_score * 0.4
        return {
            "score": score,
            "controller_pct": round(controller_pct, 2),
            "institutional_pct": round(inst_pct, 2),
        }

    # ─────────────────────────────────────────────
    # 5. 治理代理
    # ─────────────────────────────────────────────
    def _governance(self, management_f10: dict) -> Optional[Dict]:
        """独立董事占比 / 董事会规模"""
        if not management_f10 or "error" in management_f10:
            return None
        board_size = management_f10.get("board_size", 0)
        indep_pct = management_f10.get("independent_pct", 0)
        if board_size == 0:
            return None
        # 董事会 7-15 人为合理
        if 7 <= board_size <= 15:
            board_score = 90
        elif 5 <= board_size < 7 or 15 < board_size <= 20:
            board_score = 70
        else:
            board_score = 50
        # 独立董事占比 >=33% 为合规（中国证监会要求 1/3）
        if indep_pct >= 40:
            indep_score = 90
        elif indep_pct >= 33:
            indep_score = 75
        else:
            indep_score = max(0, indep_pct * 2)
        score = board_score * 0.4 + indep_score * 0.6
        return {
            "score": score,
            "board_size": board_size,
            "independent_pct": round(indep_pct, 2),
        }

    # ─────────────────────────────────────────────
    # 6. 信息披露质量
    # ─────────────────────────────────────────────
    def _disclosure_quality(self, balance: List[dict],
                            income: List[dict]) -> Optional[Dict]:
        """商誉占比 + 非经常性损益代理"""
        if not balance or not income:
            return None
        b, i = balance[0], income[0]
        # 商誉占比
        goodwill = _safe(b.get("GOODWILL"))
        total_assets = _safe(b.get("TOTAL_ASSETS"))
        gw_pct = goodwill / max(total_assets, 1) * 100
        # 商誉 <10% 满分；>50% 严重扣分
        if gw_pct < 10:
            gw_score = 100
        elif gw_pct < 30:
            gw_score = 70
        elif gw_pct < 50:
            gw_score = 40
        else:
            gw_score = 10
        # 营业利润 / 利润总额比（衡量主营贡献度）
        op = _safe(i.get("OPERATE_PROFIT"))
        tp = _safe(i.get("TOTAL_PROFIT"))
        if tp > 0:
            main_ratio = op / tp * 100
            # 主营利润占比 >90% 满分；<50% 扣分
            if main_ratio >= 90:
                main_score = 100
            elif main_ratio >= 70:
                main_score = 70
            elif main_ratio >= 50:
                main_score = 40
            else:
                main_score = 10
        else:
            main_score = 50
        score = gw_score * 0.5 + main_score * 0.5
        return {
            "score": score,
            "goodwill_pct": round(gw_pct, 2),
            "main_profit_ratio": round(op / max(tp, 1) * 100, 2),
        }

    # ─────────────────────────────────────────────
    # 主入口
    # ─────────────────────────────────────────────
    def assess(self, code: str,
               financials: Optional[dict] = None) -> ManagementResult:
        if financials is None:
            financials = {
                "income": fetch_income_statement(code, self.years),
                "balance": fetch_balance_sheet(code, self.years),
                "cashflow": fetch_cashflow_statement(code, self.years),
                "indicators": fetch_financial_indicators(code, self.years),
                "shareholders": fetch_f10_shareholders(code),
                "dividends": fetch_f10_dividends(code),
                "management": fetch_f10_management(code),
            }
        income = filter_recent_n_years(financials.get("income", []), self.years)
        balance = filter_recent_n_years(financials.get("balance", []), self.years)
        indicators = filter_recent_n_years(financials.get("indicators", []), self.years)
        shareholders = financials.get("shareholders", {})
        dividends = financials.get("dividends", [])
        management_f10 = financials.get("management", {})

        if not income or not balance:
            return ManagementResult(code=code, insufficient_data=True,
                                    evidence=["利润表或资产负债表数据不足"])

        subs: Dict[str, Optional[Dict]] = {
            "roe_roic_trend": self._roe_roic_trend(indicators, income, balance),
            "capital_allocation": self._capital_allocation(income, balance, dividends),
            "share_dilution": self._share_dilution(balance),
            "shareholder_structure": self._shareholder_structure(shareholders),
            "governance": self._governance(management_f10),
            "disclosure_quality": self._disclosure_quality(balance, income),
        }

        available = {k: v for k, v in subs.items() if v is not None and "score" in v}
        if not available:
            return ManagementResult(code=code, insufficient_data=True,
                                    evidence=["6 个维度均无数据"])

        weight_sum = sum(self.WEIGHTS[k] for k in available)
        score = sum(self.WEIGHTS[k] * available[k]["score"] for k in available) / max(weight_sum, 1e-9)

        verdict = "优秀" if score >= 80 else "良好" if score >= 65 else "一般" if score >= 50 else "较差"

        # 证据
        evidence: List[str] = []
        if subs["roe_roic_trend"]:
            d = subs["roe_roic_trend"]
            evidence.append(f"5Y ROE 均值 {d['mean_roe']}%（斜率 {d['trend_slope']}）")
            if d.get("dupont"):
                dp = d["dupont"]
                evidence.append(f"  杜邦分解: 净利率 {dp.get('net_margin')}% × 周转 {dp.get('asset_turnover')} × 杠杆 {dp.get('equity_multiplier')}")
        if subs["capital_allocation"]:
            d = subs["capital_allocation"]
            evidence.append(f"分红率均值 {d.get('avg_payout', 0)}%（稳定性: {'是' if d.get('stable') else '否'}）")
        if subs["share_dilution"]:
            d = subs["share_dilution"]
            evidence.append(f"5Y 权益增长 {d['equity_growth_pct']}%")
        if subs["shareholder_structure"]:
            d = subs["shareholder_structure"]
            evidence.append(f"实控人持股 {d['controller_pct']}% / 机构持股 {d['institutional_pct']}%")
        if subs["governance"]:
            d = subs["governance"]
            evidence.append(f"董事会 {d['board_size']} 人 / 独立董事 {d['independent_pct']}%")
        if subs["disclosure_quality"]:
            d = subs["disclosure_quality"]
            evidence.append(f"商誉占比 {d['goodwill_pct']}% / 主营利润比 {d['main_profit_ratio']}%")

        # 杜邦分解
        dupont = subs["roe_roic_trend"].get("dupont", {}) if subs["roe_roic_trend"] else {}

        return ManagementResult(
            code=code,
            score=round(score, 1),
            verdict=verdict,
            sub_scores={k: round(v["score"], 1) for k, v in available.items()},
            dupont_breakdown=dupont,
            evidence=evidence,
            insufficient_data=False,
        )

    @staticmethod
    def format_report(result: ManagementResult) -> str:
        if result.insufficient_data:
            return f"【{result.code}】管理层评估：数据不足，跳过"
        lines = [
            f"【{result.code}】管理层评估 - {result.verdict}（{result.score}/100）",
            "",
            "■ 6 维子评分:",
        ]
        labels = {
            "roe_roic_trend": "ROE/ROIC 趋势",
            "capital_allocation": "资本配置",
            "share_dilution": "股本稀释",
            "shareholder_structure": "股东结构",
            "governance": "治理",
            "disclosure_quality": "信息披露",
        }
        for k, v in result.sub_scores.items():
            lines.append(f"  • {labels.get(k, k)}: {v}/100")
        if result.dupont_breakdown:
            lines.append("")
            lines.append("■ 杜邦分解:")
            dp = result.dupont_breakdown
            lines.append(f"  ROE = 净利率 {dp.get('net_margin')}% × 周转 {dp.get('asset_turnover')} × 杠杆 {dp.get('equity_multiplier')}")
            lines.append(f"  = {dp.get('roe')}%")
        lines.append("")
        lines.append("■ 证据链:")
        for ev in result.evidence:
            lines.append(f"  • {ev}")
        return "\n".join(lines)
