# -*- coding: utf-8 -*-
"""
定期报告分析解读引擎 v7.1.0 (report_interpreter.py)

把上市公司定期报告（年报/半年报/季报）的财务数据转化为**自然语言解读**：
业绩概览、同比/环比、盈利能力、成长性、现金流质量、亮点信号、风险警示、
综合评分与评级建议。纯规则引擎（阈值+模板），零 LLM 依赖、零 pip 依赖。

数据来源（多路输入）：
  1. interpret_stock("600519")           —— 东财 RPT_LICO_FN_CPD 直连（含同比/环比增速字段）
  2. interpret_data([{...}, ...])         —— 直接喂财务数据 dict（离线/自定义，字段名兼容中英文）
  3. interpret_periods(periods)           —— 已归一化的周期序列

用法：
  from scripts.report_interpreter import interpret_stock_report
  text = interpret_stock_report("600519")          # 一站式解读
  result = interpret_data({"营收": 100, "净利润": 20, ...})  # 结构化结果
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

try:
    from .http_utils import http_get
except ImportError:  # 脚本直跑
    from http_utils import http_get  # type: ignore

# ── 东财财务报告接口（RPT_LICO_FN_CPD，含同比/环比增速字段）────────────
_EM_FN_URL = ("https://datacenter-web.eastmoney.com/api/data/v1/get"
              "?reportName=RPT_LICO_FN_CPD&columns=ALL"
              "&filter=(SECUCODE%3D%22{secucode}%22)"
              "&pageNumber=1&pageSize={limit}&source=WEB&client=WEB")
_EM_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36"),
    "Referer": "https://data.eastmoney.com/",
    "Accept": "application/json, text/plain, */*",
}

# ── 解读规则（阈值 → 档位标签 + 评语模板）─────────────────────────
RULES: Dict[str, Dict[str, Any]] = {
    "revenue_yoy": {   # 营收同比增速（%）
        ">30": ("高增长", "营收同比大增 {v:.1f}%，规模扩张动能强劲"),
        "10~30": ("稳健增长", "营收同比增长 {v:.1f}%，处于稳健增长区间"),
        "0~10": ("低增长", "营收同比增长 {v:.1f}%，增速平缓"),
        "<0": ("营收下滑", "营收同比下滑 {v:.1f}%，需关注需求端压力"),
    },
    "profit_yoy": {    # 归母净利润同比增速（%）
        ">50": ("利润爆发", "归母净利润同比大增 {v:.1f}%，盈利爆发式增长"),
        "20~50": ("利润强劲", "归母净利润同比增长 {v:.1f}%，盈利强劲"),
        "0~20": ("利润平稳", "归母净利润同比增长 {v:.1f}%，盈利平稳"),
        "<0": ("利润承压", "归母净利润同比下滑 {v:.1f}%，盈利承压"),
    },
    "gross_margin": {  # 销售毛利率（%）
        ">60": ("极高毛利", "毛利率 {v:.1f}%，具备极强的定价权与成本优势"),
        "40~60": ("高毛利", "毛利率 {v:.1f}%，盈利空间充裕"),
        "25~40": ("中等毛利", "毛利率 {v:.1f}%，处于行业中游水平"),
        "<25": ("毛利偏低", "毛利率 {v:.1f}%，产品或面临同质化竞争"),
    },
    "roe": {           # 加权净资产收益率（%）
        ">20": ("ROE优秀", "ROE {v:.1f}%，资本回报水平优秀"),
        "12~20": ("ROE良好", "ROE {v:.1f}%，资本回报良好"),
        "6~12": ("ROE一般", "ROE {v:.1f}%，资本回报一般"),
        "<6": ("ROE偏弱", "ROE {v:.1f}%，资本回报偏弱"),
    },
    "cash_ratio": {    # 每股经营现金流 / 每股收益
        ">1": ("现金流充沛", "每股经营现金流为 EPS 的 {v:.2f} 倍，盈利含金量高"),
        "0.5~1": ("现金流尚可", "每股经营现金流为 EPS 的 {v:.2f} 倍，盈利质量尚可"),
        "<0.5": ("现金流偏紧", "每股经营现金流仅 EPS 的 {v:.2f} 倍，盈利含金量不足"),
    },
}

SCORE_WEIGHTS = {      # 综合评分权重（合计 100）
    "profit_yoy": 25, "revenue_yoy": 20, "roe": 20,
    "gross_margin": 15, "cash_ratio": 10, "eps": 10,
}


def _band(value: float, rule: Dict[str, Any]) -> Tuple[str, str]:
    """按阈值区间取档位标签与评语模板。"""
    for key, (label, tpl) in rule.items():
        ok = False
        if key == ">30":
            ok = value > 30
        elif key == ">60":
            ok = value > 60
        elif key == ">50":
            ok = value > 50
        elif key == ">20":
            ok = value > 20
        elif key == ">12":
            ok = value > 12
        elif key == ">1":
            ok = value > 1
        elif key == "10~30":
            ok = 10 <= value <= 30
        elif key == "40~60":
            ok = 40 <= value <= 60
        elif key == "25~40":
            ok = 25 <= value < 40
        elif key == "12~20":
            ok = 12 <= value < 20
        elif key == "6~12":
            ok = 6 <= value < 12
        elif key == "0~10":
            ok = 0 <= value < 10
        elif key == "0~20":
            ok = 0 <= value < 20
        elif key == "0.5~1":
            ok = 0.5 <= value <= 1
        elif key == "<0":
            ok = value < 0
        elif key == "<25":
            ok = value < 25
        elif key == "<6":
            ok = value < 6
        elif key == "<0.5":
            ok = value < 0.5
        if ok:
            return label, tpl
    return "数据缺失", "该指标本期数据缺失"


def _f(v: Any) -> Optional[float]:
    """安全转 float（兼容 None/'-'/空串）。"""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).replace(",", "").replace("%", "").strip()
    if not s or s in ("-", "--", "nan", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


# ── 字段归一化：东财字段名 / 中英文常见别名 → 统一键 ────────────────
_FIELD_ALIASES = {
    "revenue": ["TOTAL_OPERATE_INCOME", "OPERATE_INCOME", "营收", "营业收入",
                "营业总收入", "revenue", "total_revenue"],
    "net_profit": ["PARENT_NETPROFIT", "NETPROFIT", "归母净利润", "净利润",
                   "net_profit", "netprofit"],
    "eps": ["BASIC_EPS", "EPSJB", "EPS", "每股收益", "基本每股收益"],
    "roe": ["WEIGHTAVG_ROE", "ROEJQ", "ROE", "净资产收益率", "加权净资产收益率"],
    "gross_margin": ["XSMLL", "毛利率", "销售毛利率", "gross_margin"],
    "revenue_yoy": ["YSTZ", "营收同比", "营业收入同比增长率", "TOTAL_OPERATE_INCOME_YOY"],
    "profit_yoy": ["SJLTZ", "净利同比", "净利润同比增长率", "PARENT_NETPROFIT_YOY"],
    "revenue_qoq": ["YSHZ", "营收环比", "营业收入环比增长率"],
    "profit_qoq": ["SJLHZ", "净利环比", "净利润环比增长率"],
    "cash_per_share": ["MGJYXJJE", "每股经营现金流", "每股经营现金流量净额"],
    "bps": ["BPS", "每股净资产"],
    "report_date": ["REPORTDATE", "REPORT_DATE", "报告期", "date"],
    "name": ["SECURITY_NAME_ABBR", "公司名称", "名称", "name"],
}


def normalize_period(row: Dict[str, Any]) -> Dict[str, Any]:
    """把任意来源的财务数据行归一化为统一键。"""
    out: Dict[str, Any] = {}
    for key, aliases in _FIELD_ALIASES.items():
        for a in aliases:
            if a in row and row[a] is not None:
                v = row[a]
                if key in ("revenue", "net_profit", "eps", "roe", "gross_margin",
                           "revenue_yoy", "profit_yoy", "revenue_qoq", "profit_qoq",
                           "cash_per_share", "bps"):
                    v = _f(v)
                out[key] = v
                break
    return out


# ── 东财直连拉取 ──────────────────────────────────────────────

def fetch_periods(stock_code: str, limit: int = 8) -> List[Dict[str, Any]]:
    """东财 RPT_LICO_FN_CPD 拉取财务周期（自动补 .SH/.SZ/.BJ）。"""
    code = stock_code.strip().upper()
    if "." in code:
        secucode, suffix = code.split(".")[:2]
        secucode = secucode + "." + suffix
    else:
        market = "BJ" if code.startswith(("4", "8", "92")) else (
            "SH" if code.startswith(("6", "9")) else "SZ")
        secucode = f"{code}.{market}"
    try:
        resp = http_get(_EM_FN_URL.format(secucode=secucode, limit=limit),
                        headers=_EM_HEADERS, timeout=20, rate_limit_delay=0.3)
        if resp is None:
            return []
        data = (resp.json().get("result") or {}).get("data") or []
        return [normalize_period(r) for r in data]
    except Exception as e:
        print(f"[report_interpreter] 拉取 {stock_code} 财务数据失败: {e}",
              file=sys.stderr)
        return []


# ── 解读核心 ──────────────────────────────────────────────────

class ReportInterpreter:
    """定期报告解读器：指标计算 → 规则命中 → 评分评级 → 文本生成。"""

    def __init__(self, rules: Optional[Dict] = None,
                 weights: Optional[Dict[str, int]] = None):
        self.rules = rules or RULES
        self.weights = weights or SCORE_WEIGHTS

    # ── 指标提取 ────────────────────────────────────────
    @staticmethod
    def _latest(periods: List[Dict]) -> Dict[str, Any]:
        periods = [p for p in periods if p.get("report_date") or p.get("revenue")]
        if not periods:
            return {}
        # 报告期日期倒序取最新（无日期则取列表第一个）
        def _key(p: Dict) -> str:
            d = str(p.get("report_date") or "")
            return d.replace("-", "").replace("/", "").replace(" ", "")
        return sorted(periods, key=_key, reverse=True)[0] if any(
            _key(p) for p in periods) else periods[0]

    def compute(self, periods: List[Dict]) -> Dict[str, Any]:
        """计算指标与信号。"""
        latest = self._latest(periods)
        if not latest:
            return {"error": "无财务数据"}
        rev, np_ = latest.get("revenue"), latest.get("net_profit")
        eps, roe = latest.get("eps"), latest.get("roe")
        gm, cps = latest.get("gross_margin"), latest.get("cash_per_share")
        rev_yoy = latest.get("revenue_yoy")
        np_yoy = latest.get("profit_yoy")
        rev_qoq = latest.get("revenue_qoq")
        np_qoq = latest.get("profit_qoq")

        cash_ratio = None
        if cps is not None and eps is not None and eps > 0:
            cash_ratio = cps / eps   # 负 EPS 时比率无意义（亏损公司直接看现金流正负）

        # 历史趋势：最近两期同比增速
        trend = None
        if len(periods) >= 2:
            prev = periods[1]
            if (np_yoy is not None and prev.get("profit_yoy") is not None
                    and np_yoy < 0 and prev.get("profit_yoy", 0) < 0):
                trend = "连续两期利润下滑"

        metrics = {
            "name": latest.get("name") or "",
            "report_date": latest.get("report_date") or "",
            "revenue": rev, "net_profit": np_, "eps": eps, "roe": roe,
            "gross_margin": gm, "revenue_yoy": rev_yoy, "profit_yoy": np_yoy,
            "revenue_qoq": rev_qoq, "profit_qoq": np_qoq,
            "cash_per_share": cps, "cash_ratio": cash_ratio, "bps": latest.get("bps"),
            "trend": trend,
        }
        return metrics

    # ── 规则命中 → 亮点/风险 ─────────────────────────────
    def signals(self, m: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        highlights, risks = [], []
        if m.get("error"):
            return highlights, risks
        # 营收/利润增速
        if m.get("revenue_yoy") is not None:
            label, tpl = _band(m["revenue_yoy"], self.rules["revenue_yoy"])
            text = tpl.format(v=m["revenue_yoy"])
            (risks if m["revenue_yoy"] < 0 else highlights).append(text)
        if m.get("profit_yoy") is not None:
            label, tpl = _band(m["profit_yoy"], self.rules["profit_yoy"])
            text = tpl.format(v=m["profit_yoy"])
            (risks if m["profit_yoy"] < 0 else highlights).append(text)
        # 环比短期承压
        for key, name in (("revenue_qoq", "营收"), ("profit_qoq", "净利润")):
            v = m.get(key)
            if v is not None and v < 0:
                risks.append(f"{name}环比下滑 {v:.1f}%，短期动能转弱")
        # 毛利率
        if m.get("gross_margin") is not None:
            label, tpl = _band(m["gross_margin"], self.rules["gross_margin"])
            text = tpl.format(v=m["gross_margin"])
            (risks if m["gross_margin"] < 25 else highlights).append(text)
        # ROE
        if m.get("roe") is not None:
            label, tpl = _band(m["roe"], self.rules["roe"])
            (risks if m["roe"] < 6 else highlights).append(
                tpl.format(v=m["roe"]))
        # 现金流质量
        if m.get("cash_ratio") is not None:
            label, tpl = _band(m["cash_ratio"], self.rules["cash_ratio"])
            text = tpl.format(v=m["cash_ratio"])
            (risks if m["cash_ratio"] < 0.5 else highlights).append(text)
        elif m.get("cash_per_share") is not None and m.get("cash_per_share", 0) < 0:
            risks.append("每股经营现金流为负，经营性现金流出")
        # 趋势
        if m.get("trend"):
            risks.append(m["trend"])
        return highlights[:6], risks[:6]

    # ── 综合评分与评级 ───────────────────────────────────
    def score(self, m: Dict[str, Any]) -> Tuple[float, str]:
        if m.get("error"):
            return 0.0, "无数据"
        total = 0.0
        got = 0
        # 各维度得分（0-100 按档位）
        def _dim(value, bands):
            for lo, hi, s in bands:
                if lo is None or value > lo:
                    if hi is None or value <= hi:
                        return s
            return 50
        dims = {
            "profit_yoy": (m.get("profit_yoy"), [
                (50, None, 95), (20, 50, 85), (0, 20, 65),
                (-10, 0, 40), (None, -10, 25)]),
            "revenue_yoy": (m.get("revenue_yoy"), [
                (30, None, 90), (10, 30, 75), (0, 10, 55),
                (-10, 0, 35), (None, -10, 20)]),
            "roe": (m.get("roe"), [
                (20, None, 90), (12, 20, 75), (6, 12, 55), (None, 6, 30)]),
            "gross_margin": (m.get("gross_margin"), [
                (60, None, 90), (40, 60, 75), (25, 40, 55), (None, 25, 30)]),
            "cash_ratio": (m.get("cash_ratio"), [
                (1, None, 90), (0.5, 1, 65), (None, 0.5, 30)]),
            "eps": (m.get("eps"), [
                (1, None, 80), (0.3, 1, 65), (0, 0.3, 50), (None, 0, 25)]),
        }
        for key, weight in self.weights.items():
            if key not in dims:
                continue
            value, bands = dims[key]
            if value is None:
                continue
            total += weight * _dim(value, bands)
            got += weight
        if got == 0:
            return 0.0, "数据不足"
        final = total / got
        if final >= 80:
            rating = "积极"
        elif final >= 65:
            rating = "中性偏积极"
        elif final >= 45:
            rating = "中性"
        else:
            rating = "谨慎"
        return round(final, 1), rating

    # ── 文本解读 ────────────────────────────────────────
    def format_text(self, m: Dict[str, Any], highlights: List[str],
                    risks: List[str], score: float, rating: str) -> str:
        if m.get("error"):
            return f"❌ 解读失败：{m['error']}"
        L = []
        name = m.get("name") or "该公司"
        L.append(f"📊 定期报告解读：{name}"
                 f"（报告期 {m.get('report_date') or '—'}）")
        L.append("=" * 52)
        if m.get("revenue") is not None:
            rev_txt = f"营收 {m['revenue']/1e8:.2f} 亿元"
            if m.get("revenue_yoy") is not None:
                rev_txt += f"（同比 {m['revenue_yoy']:+.1f}%"
                rev_txt += (f" 环比 {m['revenue_qoq']:+.1f}%）"
                            if m.get("revenue_qoq") is not None else "）")
            L.append(f"【业绩概览】{rev_txt}")
        else:
            L.append("【业绩概览】营收数据缺失")
        if m.get("net_profit") is not None:
            np_txt = f"归母净利润 {m['net_profit']/1e8:.2f} 亿元"
            if m.get("profit_yoy") is not None:
                np_txt += f"（同比 {m['profit_yoy']:+.1f}%"
                np_txt += (f" 环比 {m['profit_qoq']:+.1f}%）"
                           if m.get("profit_qoq") is not None else "）")
            L.append(f"          {np_txt}")
        if m.get("eps") is not None:
            bps_txt = f"；每股净资产 {m['bps']:.2f} 元" if m.get("bps") is not None else ""
            L.append(f"          基本每股收益 {m['eps']:.3f} 元{bps_txt}")
        L.append("")
        L.append(f"【盈利能力】ROE {m['roe']:.1f}%　毛利率 {m['gross_margin']:.1f}%"
                 if m.get("roe") is not None and m.get("gross_margin") is not None
                 else "【盈利能力】数据缺失")
        L.append("")
        if highlights:
            L.append("✅ 亮点信号")
            for h in highlights:
                L.append(f"  · {h}")
        if risks:
            L.append("⚠️ 风险提示")
            for r in risks:
                L.append(f"  · {r}")
        L.append("")
        L.append(f"【综合评分】{score}/100　评级：{'🟢' if rating == '积极' else '🟡' if rating in ('中性偏积极', '中性') else '🔴'} {rating}")
        L.append("_" * 52)
        L.append("注：规则引擎自动解读，供研究参考，不构成投资建议。")
        return "\n".join(L)

    def interpret(self, periods: List[Dict]) -> Dict[str, Any]:
        # 统一归一化（已归一化行幂等；原始东财行/中文字段行均可）
        periods = [normalize_period(p) for p in periods]
        m = self.compute(periods)
        if m.get("error"):
            return m
        highlights, risks = self.signals(m)
        score, rating = self.score(m)
        return {**m, "highlights": highlights, "risks": risks,
                "score": score, "rating": rating,
                "text": self.format_text(m, highlights, risks, score, rating)}


# ── 便捷入口 ──────────────────────────────────────────────────

def interpret_data(data: Any) -> Dict[str, Any]:
    """直接喂财务数据（dict 单期 / list 多期 / 东财原始行均可）。"""
    if isinstance(data, dict):
        periods = [normalize_period(data)]
    elif isinstance(data, (list, tuple)):
        periods = [normalize_period(d) if not _is_normalized(d) else d
                   for d in data]
    else:
        return {"error": "无法识别的数据格式"}
    return ReportInterpreter().interpret(periods)


def _is_normalized(d: Dict) -> bool:
    return any(k in d for k in ("revenue", "net_profit", "eps"))


def interpret_stock(stock_code: str, limit: int = 8) -> Dict[str, Any]:
    """一站式：拉取东财财务数据并解读。"""
    periods = fetch_periods(stock_code, limit=limit)
    if not periods:
        return {"error": f"未获取到 {stock_code} 的财务数据（代码可能错误或接口暂不可用）"}
    return ReportInterpreter().interpret(periods)


def interpret_stock_report(stock_code: str, limit: int = 8) -> str:
    """便捷文本入口（供 MCP/CLI/对话调用）。"""
    result = interpret_stock(stock_code, limit=limit)
    return result.get("text") or f"❌ 解读失败：{result.get('error', '未知错误')}"


# ── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="v7.1.0 定期报告解读引擎")
    ap.add_argument("stock", help="股票代码，如 600519 / 000001.SZ")
    ap.add_argument("--limit", type=int, default=8, help="拉取报告期数")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    args = ap.parse_args()
    result = interpret_stock(args.stock, limit=args.limit)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1, default=str))
    else:
        print(result.get("text") or result.get("error", "解读失败"))
