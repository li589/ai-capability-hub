#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""定期报告解读 (financial_report.py, v9.2 新增)

针对上市公司定期报告（年报 / 半年报 / 季报）做结构化中文解读：

  - 报告期解析：自动最新 / 指定 2024（年报）/ 2025Q3 / 2025H1 / 2025-06-30
  - 核心指标同比（YoY，去年同期）/ 环比（QoQ，上一季度）
  - 规则化「业绩亮点 / 风险提示」提炼（营收加速、增收不增利、毛利率、
    盈利质量=经营现金流/净利润、杠杆变化、EPS）
  - 一句话结论 + markdown 中文报告

数据源：复用 data.financial_statements 的多期三表（东方财富免费接口，
港美股走 akshare 降级）。纯标准库，零新依赖。
离线 / 数据源失败时诚实返回 data_mode="insufficient"，不编造、不崩溃。
"""
from __future__ import annotations

import calendar
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ─────────────────────────────────────────────────────
# 报告期解析
# ─────────────────────────────────────────────────────

_QUARTER_ENDS = {"Q1": "-03-31", "Q2": "-06-30", "Q3": "-09-30", "Q4": "-12-31"}


def _shift_date(date_str: str, months: int) -> str:
    """把 YYYY-MM-DD 向前平移 months 个月（用于 YoY=-12 / QoQ=-3）。"""
    try:
        d = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return ""
    month = d.month - months
    year = d.year
    while month <= 0:
        month += 12
        year -= 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(d.day, last_day)
    return f"{year:04d}-{month:02d}-{day:02d}"


def _resolve_period(income: List[dict], period: Optional[str]) -> str:
    """把用户 period 解析成精确 report_date；None → 最新报告期。"""
    dates = sorted({s.get("report_date", "") for s in income if s.get("report_date")},
                   reverse=True)
    if not dates:
        return ""
    if not period:
        return dates[0]
    p = str(period).strip()
    if not p:
        return dates[0]

    # ① 精确报告期 "2024-12-31" / "2024-06-30"
    if len(p) >= 10:
        for d in dates:
            if d == p or d.startswith(p[:10]):
                return d
    # ② 年份 "2024" → 年报 "2024-12-31"（无年报则取该年最新）
    if re.fullmatch(r"\d{4}", p):
        annual = f"{p}-12-31"
        for d in dates:
            if d == annual:
                return d
        for d in dates:
            if d.startswith(p):
                return d
    # ③ 季度 "2025Q3" / 半年 "2025H1"
    m = re.fullmatch(r"(\d{4})(Q[1-4]|H1|H2)", p, re.IGNORECASE)
    if m:
        year, seg = m.group(1), m.group(2).upper()
        if seg == "H1":
            target = f"{year}-06-30"
        elif seg == "H2":
            target = f"{year}-12-31"
        else:
            target = f"{year}{_QUARTER_ENDS[seg]}"
        for d in dates:
            if d == target:
                return d
    # ④ 兜底：模糊匹配（含该年份的最近一期）
    for d in dates:
        if p in d or d.startswith(p):
            return d
    return dates[0]


def _pct_change(cur: Optional[float], base: Optional[float]) -> Optional[float]:
    """百分比变化 (cur-base)/|base|；base 缺失或为 0 时返回 None（不编造）。"""
    if cur is None or base in (None, 0):
        return None
    try:
        return round((float(cur) - float(base)) / abs(float(base)) * 100, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _delta(cur: Optional[float], base: Optional[float]) -> Optional[float]:
    """绝对差值（用于比率类指标，如毛利率、负债率的百分点变化）。"""
    if cur is None or base is None:
        return None
    try:
        return round(float(cur) - float(base), 2)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────
# 解读结果
# ─────────────────────────────────────────────────────

@dataclass
class ReportInterpretation:
    """定期报告解读结果"""
    code: str = ""
    market: str = "cn"
    period: str = ""            # 目标报告期 "2024-12-31"
    period_label: str = ""      # 人类可读 "2024 年报"
    data_mode: str = "insufficient"  # ok | insufficient
    metrics: Dict = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    conclusion: str = ""
    verdict: str = "无法判断"    # 高增长/增长/承压/持平/无法判断


def _period_label(date_str: str) -> str:
    """把 report_date 转成中文标签：2024-12-31 → 2024 年报。"""
    if not date_str:
        return "最新报告期"
    d = str(date_str)[:10]
    year = d[:4]
    mmdd = d[5:10]
    if mmdd == "12-31":
        return f"{year} 年报"
    if mmdd == "06-30":
        return f"{year} 中报"
    if mmdd == "09-30":
        return f"{year} 三季报"
    if mmdd == "03-31":
        return f"{year} 一季报"
    return d


def _get(d: dict, *keys, default=0.0):
    for k in keys:
        v = d.get(k)
        if v is not None and v != "":
            return v
    return default


class FinancialReportInterpreter:
    """定期报告解读器（纯标准库，逻辑与数据获取分离便于离线测试）。"""

    def interpret(self, code: str, market: str = "cn", period: Optional[str] = None,
                  years: int = 5) -> ReportInterpretation:
        """入口：拉取财务数据并解读。"""
        financials = self._load_financials(code, market, years)
        return self.analyze(financials, code=code, market=market, period=period)

    # ── 数据加载（网络，失败降级）─────────────────────────
    def _load_financials(self, code: str, market: str, years: int) -> dict:
        if market in ("hk", "us"):
            # 港美股：走 akshare 兜底（未装/失败返回 {}）
            from stock_researcher.data.financial_statements import fetch_financials_akshare
            try:
                return fetch_financials_akshare(code, market=market) or {}
            except Exception:
                return {}
        try:
            from stock_researcher.data.financial_statements import fetch_all_financials
            return fetch_all_financials(code, years=years)
        except Exception:
            return {}

    # ── 纯逻辑解读（可离线测试）─────────────────────────
    def analyze(self, financials: dict, code: str = "", market: str = "cn",
                period: Optional[str] = None) -> ReportInterpretation:
        income = financials.get("income", []) or []
        balance = financials.get("balance", []) or []
        cashflow = financials.get("cashflow", []) or []

        result = ReportInterpretation(
            code=code or financials.get("code", ""),
            market=market,
        )

        if not income:
            result.conclusion = "无可用财务数据（离线或数据源不可达），无法解读。"
            return result

        # 对齐目标报告期
        target_date = _resolve_period(income, period)
        by_date = {str(s.get("report_date", ""))[:10]: s for s in income
                   if s.get("report_date")}
        cur = by_date.get(target_date, {})
        yoy = by_date.get(_shift_date(target_date, 12), {})
        qoq = by_date.get(_shift_date(target_date, 3), {})

        bal_by_date = {str(b.get("report_date", ""))[:10]: b for b in balance
                       if b.get("report_date")}
        cf_by_date = {str(c.get("report_date", ""))[:10]: c for c in cashflow
                      if c.get("report_date")}
        cur_bal = bal_by_date.get(target_date, {})
        yoy_bal = bal_by_date.get(_shift_date(target_date, 12), {})
        cur_cf = cf_by_date.get(target_date, {})

        # 核心指标
        rev = _get(cur, "TOTAL_OPERATE_INCOME", "OPERATE_INCOME")
        profit = _get(cur, "PARENT_NETPROFIT", "NETPROFIT")
        rev_yoy = _pct_change(rev, _get(yoy, "TOTAL_OPERATE_INCOME", "OPERATE_INCOME"))
        rev_qoq = _pct_change(rev, _get(qoq, "TOTAL_OPERATE_INCOME", "OPERATE_INCOME"))
        profit_yoy = _pct_change(profit, _get(yoy, "PARENT_NETPROFIT", "NETPROFIT"))
        profit_qoq = _pct_change(profit, _get(qoq, "PARENT_NETPROFIT", "NETPROFIT"))
        eps = _get(cur, "BASIC_EPS", "EPS")
        eps_yoy = _pct_change(eps, _get(yoy, "BASIC_EPS", "EPS"))

        gm = _get(cur, "GROSS_MARGIN", "GROSS_PROFIT_RATIO", "XSJLL")
        gm_yoy = _get(yoy, "GROSS_MARGIN", "GROSS_PROFIT_RATIO", "XSJLL")
        gm_change = _delta(gm, gm_yoy)

        net_margin = round(profit / rev * 100, 2) if rev else None
        net_margin_yoy = (round(_get(yoy, "PARENT_NETPROFIT", "NETPROFIT")
                                / _get(yoy, "TOTAL_OPERATE_INCOME", "OPERATE_INCOME") * 100, 2)
                          if _get(yoy, "TOTAL_OPERATE_INCOME", "OPERATE_INCOME") else None)
        net_margin_change = _delta(net_margin, net_margin_yoy)

        debt_ratio = _get(cur_bal, "DEBT_ASSET_RATIO", "ZCFZL")
        debt_yoy = _get(yoy_bal, "DEBT_ASSET_RATIO", "ZCFZL")
        debt_change = _delta(debt_ratio, debt_yoy)

        ocf = _get(cur_cf, "NETCASH_OPERATE")
        ocf_ratio = round(ocf / profit, 2) if (ocf and profit) else None

        metrics = {
            "revenue": rev,
            "revenue_yoy": rev_yoy,
            "revenue_qoq": rev_qoq,
            "net_profit": profit,
            "net_profit_yoy": profit_yoy,
            "net_profit_qoq": profit_qoq,
            "eps": eps,
            "eps_yoy": eps_yoy,
            "gross_margin": gm,
            "gross_margin_change": gm_change,
            "net_margin": net_margin,
            "net_margin_change": net_margin_change,
            "roe": _get(cur, "ROE", "ROEJQ"),
            "debt_ratio": debt_ratio,
            "debt_ratio_change": debt_change,
            "operating_cashflow": ocf,
            "ocf_to_profit": ocf_ratio,
        }

        highlights, risks = self._extract_highlights_risks(metrics)

        result.period = target_date
        result.period_label = _period_label(target_date)
        result.data_mode = "ok"
        result.metrics = metrics
        result.highlights = highlights
        result.risks = risks
        result.verdict, result.conclusion = self._make_conclusion(metrics, risks)
        return result

    # ── 亮点/风险规则引擎 ────────────────────────────────
    def _extract_highlights_risks(self, m: dict) -> tuple:
        highlights: List[str] = []
        risks: List[str] = []
        rev_yoy = m.get("revenue_yoy")
        profit_yoy = m.get("net_profit_yoy")

        # 营收增速
        if rev_yoy is not None:
            if rev_yoy > 10:
                highlights.append(f"营收同比 +{rev_yoy}%，保持两位数增长")
            elif rev_yoy < 0:
                risks.append(f"营收同比 {rev_yoy}%，出现负增长")

        # 利润 vs 营收（经营杠杆 / 增收不增利 / 盈利恶化）
        if profit_yoy is not None and rev_yoy is not None and profit_yoy != rev_yoy:
            if profit_yoy > rev_yoy and profit_yoy > 0:
                highlights.append(f"净利润增速(+{profit_yoy}%)高于营收增速(+{rev_yoy}%)，经营杠杆显现")
            elif profit_yoy < rev_yoy and rev_yoy > 0:
                risks.append(f"净利润增速(+{profit_yoy}%)低于营收增速(+{rev_yoy}%)，增收不增利")
            elif profit_yoy < rev_yoy and rev_yoy <= 0:
                risks.append(f"净利润降幅({profit_yoy}%)大于营收降幅({rev_yoy}%)，盈利恶化")

        # 毛利率
        gm_change = m.get("gross_margin_change")
        if gm_change is not None:
            if gm_change > 1:
                highlights.append(f"毛利率提升 {gm_change:+.1f} pct，盈利能力增强")
            elif gm_change < -1:
                risks.append(f"毛利率下滑 {gm_change:+.1f} pct，成本或竞争压力")

        # 盈利质量（经营现金流 / 净利润）
        ocf_ratio = m.get("ocf_to_profit")
        if ocf_ratio is not None:
            if ocf_ratio > 1:
                highlights.append(f"经营现金流/净利润 = {ocf_ratio:.2f}，盈利质量高")
            elif ocf_ratio < 0.5:
                risks.append(f"经营现金流/净利润 = {ocf_ratio:.2f}，利润含金量不足")

        # 资产负债率
        debt_change = m.get("debt_ratio_change")
        if debt_change is not None:
            if debt_change < -2:
                highlights.append(f"资产负债率下降 {abs(debt_change):.1f} pct，财务结构改善")
            elif debt_change > 3:
                risks.append(f"资产负债率上升 {debt_change:+.1f} pct，杠杆加大")

        if not highlights and not risks:
            highlights.append("各项核心指标同比平稳，无明显异常")

        return highlights, risks

    # ── 结论 ────────────────────────────────────────────
    def _make_conclusion(self, m: dict, risks: List[str]) -> tuple:
        profit_yoy = m.get("net_profit_yoy")
        rev_yoy = m.get("revenue_yoy")

        if profit_yoy is not None:
            if profit_yoy > 20 and not risks:
                verdict = "高增长"
            elif profit_yoy > 0:
                verdict = "增长"
            elif profit_yoy < 0:
                verdict = "承压"
            else:
                verdict = "持平"
        elif rev_yoy is not None:
            verdict = "增长" if rev_yoy > 0 else ("承压" if rev_yoy < 0 else "持平")
        else:
            verdict = "无法判断"

        if verdict == "高增长":
            conclusion = "业绩高速增长且无明显风险点，基本面景气向上。"
        elif verdict == "增长":
            conclusion = "业绩保持增长，需结合风险点观察可持续性。"
        elif verdict == "承压":
            conclusion = "业绩承压，警惕下行风险，需跟踪后续季度改善情况。"
        elif verdict == "持平":
            conclusion = "业绩基本持平，缺乏明确方向性变化。"
        else:
            conclusion = "数据不足以判断业绩趋势。"
        return verdict, conclusion

    # ── markdown 报告 ───────────────────────────────────
    def format_report(self, r: ReportInterpretation) -> str:
        if r.data_mode != "ok":
            return (f"# 定期报告解读\n\n"
                    f"> ⚠️ {r.conclusion}\n\n"
                    f"> 数据源：东方财富/akshare（免费，需国内直连）。")
        m = r.metrics
        lines = [
            f"# 定期报告解读：{r.period_label}（{r.period}）",
            "",
            f"- 代码/市场：{r.code} / {r.market}",
            f"- 数据模式：{r.data_mode}（真实数据，未编造）",
            "",
            "## 一、核心指标（同比 / 环比）",
            "",
            "| 指标 | 本期 | 同比 | 环比 |",
            "|---|---|---|---|",
            f"| 营业收入 | {m['revenue']:,.0f} | {_fmt_pct(m['revenue_yoy'])} | {_fmt_pct(m['revenue_qoq'])} |",
            f"| 归母净利润 | {m['net_profit']:,.0f} | {_fmt_pct(m['net_profit_yoy'])} | {_fmt_pct(m['net_profit_qoq'])} |",
            f"| 基本每股收益 | {m['eps']:.2f} | {_fmt_pct(m['eps_yoy'])} | — |",
            f"| 毛利率 | {m['gross_margin']:.2f}% | {_fmt_delta(m['gross_margin_change'])} | — |",
            f"| 净利率 | {m['net_margin']:.2f}% | {_fmt_delta(m['net_margin_change'])} | — |",
            f"| ROE | {m['roe']:.2f}% | — | — |",
            f"| 资产负债率 | {m['debt_ratio']:.2f}% | {_fmt_delta(m['debt_ratio_change'])} | — |",
            f"| 经营现金流/净利润 | {_fmt_ratio(m['ocf_to_profit'])} | — | — |",
            "",
            "## 二、业绩亮点",
            "",
        ]
        if r.highlights:
            for h in r.highlights:
                lines.append(f"- ✅ {h}")
        else:
            lines.append("- 无显著亮点")
        lines += ["", "## 三、风险提示", ""]
        if r.risks:
            for risk in r.risks:
                lines.append(f"- ⚠️ {risk}")
        else:
            lines.append("- 无显著风险点")
        lines += [
            "",
            "## 四、结论",
            "",
            f"**{r.verdict}**：{r.conclusion}",
            "",
            "> ⚠️ 仅供学习参考，不构成投资建议。",
        ]
        return "\n".join(lines)


def _fmt_pct(v) -> str:
    return f"{v:+.2f}%" if v is not None else "—"


def _fmt_delta(v) -> str:
    return f"{v:+.1f} pct" if v is not None else "—"


def _fmt_ratio(v) -> str:
    return f"{v:.2f}" if v is not None else "—"


# ── 便捷函数 ────────────────────────────────────────────
def interpret_report(code: str, market: str = "cn", period: Optional[str] = None,
                     years: int = 5) -> ReportInterpretation:
    """解读某只股票的定期报告（年报/半年报/季报）。

    Args:
        code: 股票代码（A股 6 位，港股 hk:00700，美股 us:AAPL）
        market: cn / hk / us
        period: 可选报告期，None=最新；如 "2024" / "2025Q3" / "2025H1" / "2024-12-31"
        years: 拉取年数（默认 5，用于同比环比对齐）
    """
    return FinancialReportInterpreter().interpret(code, market=market, period=period, years=years)


def format_report(r: ReportInterpretation) -> str:
    """把解读结果格式化为 markdown 中文报告。"""
    return FinancialReportInterpreter().format_report(r)
