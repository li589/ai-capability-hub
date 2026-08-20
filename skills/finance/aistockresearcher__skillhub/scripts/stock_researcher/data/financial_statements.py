#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务报表获取器（v5.0 新增）

数据源：东方财富 datacenter-web API（免费接口，无需 token）
- 主要指标+利润表: RPT_LICO_FN_CPD
- 资产负债表: RPT_DMSK_FN_BALANCE
- 现金流量表: RPT_DMSK_FN_CASHFLOW
- F10 股东/治理: emweb F10 页面（部分字段）

提供 5 年年报 + 4 季度的多期数据，是 DCF/财务健康/护城河/管理层评估的基础。
所有获取函数均带 TTL 缓存（报表 24h，治理 7d），失败返回 [] 而非崩溃。
字段名已归一化为大写下划线格式，并补充派生字段（如 OPERATE_COST 由营收和毛利率推导）。
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from typing import Dict, List, Optional

from .cache import (
    TTL_FINANCIAL_STATEMENT,
    TTL_F10_GOVERNANCE,
    cached,
)

# ─────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────
_DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://data.eastmoney.com/",
    "Accept": "application/json, text/plain, */*",
}


def _normalize_code(code: str) -> str:
    """600519 / SH600519 / 600519.SS -> 600519.SH（东财 SECUCODE 格式）"""
    code = str(code).strip().upper()
    code = code.replace(".SS", ".SH").replace(".SZ", "")
    if code.startswith(("SH", "SZ")):
        bare = code[2:]
        suffix = code[:2]
        return f"{bare}.{suffix}"
    code_pure = code.zfill(6)
    if code_pure.startswith(("6", "5", "9")):
        return f"{code_pure}.SH"
    return f"{code_pure}.SZ"


def _bare_code(code: str) -> str:
    """SH600519 / 600519.SH / 600519 -> 600519"""
    c = str(code).strip().upper()
    for pfx in ("SH", "SZ"):
        if c.startswith(pfx):
            return c[len(pfx):]
    if "." in c:
        return c.split(".")[0]
    return c.zfill(6)


def _http_get_json(url: str, timeout: int = 10) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers=_DEFAULT_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="ignore")
        if raw.startswith("\ufeff"):
            raw = raw.lstrip("\ufeff")
        return json.loads(raw)
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, OSError):
        return None


def _safe_float(val, default: float = 0.0) -> float:
    if val is None:
        return default
    if isinstance(val, (int, float)):
        f = float(val)
        return f if abs(f) < 1e15 else default
    s = str(val).strip()
    if not s or s in ("--", "-", "null", "None", "NaN", "nan"):
        return default
    try:
        f = float(s)
        return f if abs(f) < 1e15 else default
    except (ValueError, TypeError):
        return default


def _pick_first(row: dict, keys) -> float:
    """v8.0: 从东财行记录中探测第一个存在的候选字段（容忍字段名差异）。"""
    for k in keys:
        v = row.get(k)
        if v is not None and str(v).strip() not in ("", "--", "-", "null", "None"):
            return _safe_float(v)
    return 0.0


# ─────────────────────────────────────────────────────
# 主要指标 + 利润表（RPT_LICO_FN_CPD）
# ─────────────────────────────────────────────────────

@cached(ttl=TTL_FINANCIAL_STATEMENT, key_fn=lambda code, years=5: f"{_normalize_code(code)}_licocpd_{years}")
def fetch_income_statement(code: str, years: int = 5) -> List[dict]:
    """
    利润表 + 主要财务指标（东财 RPT_LICO_FN_CPD）。

    返回字段（已归一化）:
    - report_date: 报告期
    - TOTAL_OPERATE_INCOME: 营业总收入
    - PARENT_NETPROFIT: 归母净利润
    - NETPROFIT: 净利润（同 PARENT_NETPROFIT 兜底）
    - BASIC_EPS: 基本每股收益
    - ROE: 加权净资产收益率(%)
    - BPS: 每股净资产
    - GROSS_MARGIN: 毛利率(%)
    - REVENUE_GROWTH: 营收同比(%)
    - PROFIT_GROWTH: 净利润同比(%)
    - OCF_PER_SHARE: 每股经营现金流
    - 派生: OPERATE_COST = 营收 × (1 - 毛利率/100)
    """
    secucode = _normalize_code(code)
    limit = max(years * 4, 20)
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get"
           f"?reportName=RPT_LICO_FN_CPD&columns=ALL"
           f"&filter=(SECUCODE%3D%22{urllib.parse.quote(secucode)}%22)"
           f"&pageSize={limit}&pageNumber=1"
           f"&sortColumns=REPORTDATE&sortTypes=-1")
    data = _http_get_json(url)
    if not isinstance(data, dict) or not data.get("success"):
        return []
    rows = (data.get("result") or {}).get("data") or []
    parsed: List[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        rev = _safe_float(row.get("TOTAL_OPERATE_INCOME"))
        gm = _safe_float(row.get("XSMLL"))
        item = {
            "report_date": str(row.get("REPORTDATE", ""))[:10],
            "TOTAL_OPERATE_INCOME": rev,
            "OPERATE_INCOME": rev,
            "PARENT_NETPROFIT": _safe_float(row.get("PARENT_NETPROFIT")),
            "NETPROFIT": _safe_float(row.get("PARENT_NETPROFIT")),  # 兜底用归母
            "BASIC_EPS": _safe_float(row.get("BASIC_EPS")),
            "ROE": _safe_float(row.get("WEIGHTAVG_ROE")),
            "ROEJQ": _safe_float(row.get("WEIGHTAVG_ROE")),
            "BPS": _safe_float(row.get("BPS")),
            "GROSS_MARGIN": gm,
            "GROSS_PROFIT_RATIO": gm,
            "XSJLL": gm,  # 兼容下游模块的字段别名
            "REVENUE_GROWTH": _safe_float(row.get("YSTZ")),
            "PROFIT_GROWTH": _safe_float(row.get("SJLTZ")),
            "OCF_PER_SHARE": _safe_float(row.get("MGJYXJJE")),
            "industry": row.get("PUBLISHNAME") or row.get("BOARD_NAME", ""),
            "SECUCODE": row.get("SECUCODE", ""),
        }
        # 派生 OPERATE_COST = 营收 × (1 - 毛利率/100)
        item["OPERATE_COST"] = rev * (1 - gm / 100) if rev > 0 and gm > 0 else 0
        # v7.2: 标记派生字段
        item["OPERATE_COST_derived"] = True
        # 派生 OPERATE_PROFIT ≈ 净利润 / 0.75（假设 25% 税率）
        if item["PARENT_NETPROFIT"] > 0:
            item["OPERATE_PROFIT"] = item["PARENT_NETPROFIT"] / 0.75
            item["TOTAL_PROFIT"] = item["PARENT_NETPROFIT"] / 0.75
            item["OPERATE_PROFIT_derived"] = True
            item["OPERATE_PROFIT_note"] = "假设25%税率: 净利润/0.75"
        else:
            item["OPERATE_PROFIT"] = 0
            item["TOTAL_PROFIT"] = 0
        # v8.0: 财务费用探测真实字段（东财常用别名 XSFY），无则保持不可得。
        # 此前硬编码 0 导致 DCF 利息支出/债务成本恒 0。
        fin_exp = _pick_first(row, ["FINANCE_EXPENSE", "XSFY"])
        item["FINANCE_EXPENSE"] = fin_exp
        if fin_exp == 0:
            item["FINANCE_EXPENSE_unavailable"] = True
        else:
            item["FINANCE_EXPENSE_unavailable"] = False
            item["FINANCE_EXPENSE_source"] = "东财 RPT_LICO_FN_CPD"
        # 其余费用明细仍不可得（非零值，v7.2 语义）
        item["RESEARCH_EXPENSE"] = 0
        item["RESEARCH_EXPENSE_unavailable"] = True
        item["SALE_EXPENSE"] = 0
        item["SALE_EXPENSE_unavailable"] = True
        item["MANAGE_EXPENSE"] = 0
        item["MANAGE_EXPENSE_unavailable"] = True
        item["INCOME_TAX"] = 0
        item["INCOME_TAX_unavailable"] = True
        # v7.2: 标记数据质量元信息
        item["_data_quality"] = {
            "source": "东方财富 RPT_LICO_FN_CPD",
            "fields_available": ["TOTAL_OPERATE_INCOME","PARENT_NETPROFIT","BASIC_EPS",
                "ROE","BPS","GROSS_MARGIN","REVENUE_GROWTH","PROFIT_GROWTH","OCF_PER_SHARE",
                "FINANCE_EXPENSE"] if fin_exp != 0 else
                ["TOTAL_OPERATE_INCOME","PARENT_NETPROFIT","BASIC_EPS",
                 "ROE","BPS","GROSS_MARGIN","REVENUE_GROWTH","PROFIT_GROWTH","OCF_PER_SHARE"],
            "fields_derived": ["OPERATE_COST","OPERATE_PROFIT","TOTAL_PROFIT"],
            "fields_unavailable": (
                [] if fin_exp != 0 else ["FINANCE_EXPENSE"]
            ) + ["RESEARCH_EXPENSE","SALE_EXPENSE","MANAGE_EXPENSE","INCOME_TAX"],
        }
        parsed.append(item)
    parsed.sort(key=lambda x: x.get("report_date", ""), reverse=True)
    return parsed


# ─────────────────────────────────────────────────────
# 资产负债表（RPT_DMSK_FN_BALANCE）
# ─────────────────────────────────────────────────────

@cached(ttl=TTL_FINANCIAL_STATEMENT, key_fn=lambda code, years=5: f"{_normalize_code(code)}_balance_{years}")
def fetch_balance_sheet(code: str, years: int = 5) -> List[dict]:
    """
    资产负债表（东财 RPT_DMSK_FN_BALANCE）。

    返回字段:
    - report_date, TOTAL_ASSETS, TOTAL_LIABILITIES, TOTAL_EQUITY
    - FIXED_ASSET, CASH (MONETARYFUNDS), ACCOUNTS_RECE, INVENTORY
    - CURRENT_RATIO, DEBT_ASSET_RATIO
    - 派生: TOTAL_PARENT_EQUITY=TOTAL_EQUITY, TOTAL_CURRENT_LIAB=TOTAL_LIABILITIES×0.6
    """
    secucode = _normalize_code(code)
    limit = max(years * 4, 20)
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get"
           f"?reportName=RPT_DMSK_FN_BALANCE&columns=ALL"
           f"&filter=(SECUCODE%3D%22{urllib.parse.quote(secucode)}%22)"
           f"&pageSize={limit}&pageNumber=1"
           f"&sortColumns=REPORT_DATE&sortTypes=-1")
    data = _http_get_json(url)
    if not isinstance(data, dict) or not data.get("success"):
        return []
    rows = (data.get("result") or {}).get("data") or []
    parsed: List[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        total_assets = _safe_float(row.get("TOTAL_ASSETS"))
        total_liab = _safe_float(row.get("TOTAL_LIABILITIES"))
        total_equity = _safe_float(row.get("TOTAL_EQUITY"))
        current_ratio = _safe_float(row.get("CURRENT_RATIO"))
        # 派生流动负债：用总负债 × 0.6 近似（流动负债通常占总负债 50-70%）
        current_liab = total_liab * 0.6 if total_liab > 0 else 0
        # 派生流动资产 = 流动负债 × 流动比率
        current_assets = current_liab * current_ratio / 100 if (current_liab > 0 and current_ratio > 0) else 0
        item = {
            "report_date": str(row.get("REPORT_DATE", ""))[:10],
            "TOTAL_ASSETS": total_assets,
            "TOTAL_LIABILITIES": total_liab,
            "TOTAL_EQUITY": total_equity,
            "TOTAL_PARENT_EQUITY": total_equity,
            "FIXED_ASSET": _safe_float(row.get("FIXED_ASSET")),
            "CASH": _safe_float(row.get("MONETARYFUNDS")),
            "MONETARY_FUNDS": _safe_float(row.get("MONETARYFUNDS")),
            "END_CASH": _safe_float(row.get("MONETARYFUNDS")),
            "ACCOUNTS_RECE": _safe_float(row.get("ACCOUNTS_RECE")),
            "INVENTORY": _safe_float(row.get("INVENTORY")),
            "CURRENT_RATIO": current_ratio,
            "LDBL": current_ratio,  # 兼容下游
            "DEBT_ASSET_RATIO": _safe_float(row.get("DEBT_ASSET_RATIO")),
            "ZCFZL": _safe_float(row.get("DEBT_ASSET_RATIO")),  # 兼容下游
            "TOTAL_CURRENT_ASSETS": current_assets,
            "TOTAL_CURRENT_LIAB": current_liab,
            # v8.0: 探测真实有息负债字段（东财字段名可能为 SHORT_TERM_LOAN 等），
            # 无则 0（接口未提供）→ 激活 DCF 债务计算（此前硬编码 0 导致 WACC 债务权重恒 0）
            "GOODWILL": _pick_first(row, ["GOODWILL"]),
            "SHORT_LOAN": _pick_first(row, ["SHORT_LOAN", "SHORT_TERM_LOAN"]),
            "LONG_LOAN": _pick_first(row, ["LONG_LOAN", "LONG_TERM_LOAN"]),
            "BOND_PAYABLE": _pick_first(row, ["BOND_PAYABLE"]),
            "NONCURRENT_LIAB_1YEAR": _pick_first(row, ["NONCURRENT_LIAB_1YEAR", "ONE_YEAR_NON_CURRENT_LIAB"]),
            "INTEREST_BEARING_DEBT": (
                _pick_first(row, ["SHORT_LOAN", "SHORT_TERM_LOAN"])
                + _pick_first(row, ["LONG_LOAN", "LONG_TERM_LOAN"])
                + _pick_first(row, ["BOND_PAYABLE"])
                + _pick_first(row, ["NONCURRENT_LIAB_1YEAR", "ONE_YEAR_NON_CURRENT_LIAB"])
            ),
            "UNDISTRIBUTED_PROFIT": _pick_first(row, ["RETAINED_EARNINGS", "UNDISTRIBUTED_PROFIT"]),
            "RETAINED_EARNINGS": _pick_first(row, ["RETAINED_EARNINGS", "UNDISTRIBUTED_PROFIT"]),
        }
        parsed.append(item)
    parsed.sort(key=lambda x: x.get("report_date", ""), reverse=True)
    return parsed


# ─────────────────────────────────────────────────────
# 现金流量表（RPT_DMSK_FN_CASHFLOW）
# ─────────────────────────────────────────────────────

@cached(ttl=TTL_FINANCIAL_STATEMENT, key_fn=lambda code, years=5: f"{_normalize_code(code)}_cashflow_{years}")
def fetch_cashflow_statement(code: str, years: int = 5) -> List[dict]:
    """
    现金流量表（东财 RPT_DMSK_FN_CASHFLOW）。

    返回字段:
    - report_date, NETCASH_OPERATE, NETCASH_INVEST, NETCASH_FINANCE
    - 派生: BUY_FIX_ASSET_OTHER = max(0, -NETCASH_INVEST)（资本支出近似）
    """
    secucode = _normalize_code(code)
    limit = max(years * 4, 20)
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get"
           f"?reportName=RPT_DMSK_FN_CASHFLOW&columns=ALL"
           f"&filter=(SECUCODE%3D%22{urllib.parse.quote(secucode)}%22)"
           f"&pageSize={limit}&pageNumber=1"
           f"&sortColumns=REPORT_DATE&sortTypes=-1")
    data = _http_get_json(url)
    if not isinstance(data, dict) or not data.get("success"):
        return []
    rows = (data.get("result") or {}).get("data") or []
    parsed: List[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        net_invest = _safe_float(row.get("NETCASH_INVEST"))
        item = {
            "report_date": str(row.get("REPORT_DATE", ""))[:10],
            "NETCASH_OPERATE": _safe_float(row.get("NETCASH_OPERATE")),
            "NETCASH_INVEST": net_invest,
            "NETCASH_FINANCE": _safe_float(row.get("NETCASH_FINANCE")),
            # 资本支出近似：投资活动现金流出（NETCASH_INVEST 为负表示净流出）
            "BUY_FIX_ASSET_OTHER": max(0, -net_invest),
        }
        parsed.append(item)
    parsed.sort(key=lambda x: x.get("report_date", ""), reverse=True)
    return parsed


# ─────────────────────────────────────────────────────
# 主要财务指标（多期，复用利润表数据）
# ─────────────────────────────────────────────────────

@cached(ttl=TTL_FINANCIAL_STATEMENT, key_fn=lambda code, years=5: f"{_normalize_code(code)}_indicators_{years}")
def fetch_financial_indicators(code: str, years: int = 5) -> List[dict]:
    """
    主要财务指标（多期）。复用 fetch_income_statement + fetch_balance_sheet 的数据合成。
    返回字段同利润表 + 资产负债表的关键指标。
    """
    income = fetch_income_statement(code, years)
    balance = fetch_balance_sheet(code, years)
    # 按报告期对齐合并
    bal_by_date = {b["report_date"]: b for b in balance if b.get("report_date")}
    parsed: List[dict] = []
    for inc in income:
        rdate = inc.get("report_date", "")
        bal = bal_by_date.get(rdate, {})
        parsed.append({
            "report_date": rdate,
            "ROE": inc.get("ROE", 0),
            "ROEJQ": inc.get("ROEJQ", 0),
            "GROSS_PROFIT_RATIO": inc.get("GROSS_MARGIN", 0),
            "XSJLL": inc.get("XSJLL", 0),
            "REVENUE_GROWTH": inc.get("REVENUE_GROWTH", 0),
            "PROFIT_GROWTH": inc.get("PROFIT_GROWTH", 0),
            "DEBT_ASSET_RATIO": bal.get("DEBT_ASSET_RATIO", 0),
            "ZCFZL": bal.get("ZCFZL", 0),
            "CURRENT_RATIO": bal.get("CURRENT_RATIO", 0),
            "LDBL": bal.get("LDBL", 0),
            "ROA": inc.get("ROE", 0) * 0.5,  # 粗略 ROA ≈ ROE × (1-资产负债率)
            "TOTAL_OPERATE_INCOME": inc.get("TOTAL_OPERATE_INCOME", 0),
            "PARENT_NETPROFIT": inc.get("PARENT_NETPROFIT", 0),
            "TOTAL_ASSETS": bal.get("TOTAL_ASSETS", 0),
        })
    return parsed


# ─────────────────────────────────────────────────────
# F10 股东 / 分红 / 治理（部分接口可能不稳定，提供兜底）
# ─────────────────────────────────────────────────────

@cached(ttl=TTL_F10_GOVERNANCE, key_fn=lambda code: _normalize_code(code))
def fetch_f10_shareholders(code: str) -> dict:
    """
    十大股东 + 实控人 + 机构持股比例。
    接口可能不稳定，失败返回带 error 的 dict（不抛异常）。
    """
    secucode = _normalize_code(code)
    bare = _bare_code(code)
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get"
           f"?reportName=RPT_F10_EH_HOLDERS&columns=ALL"
           f"&filter=(SECUCODE%3D%22{urllib.parse.quote(secucode)}%22)"
           f"&pageSize=10&pageNumber=1"
           f"&sortColumns=END_DATE&sortTypes=-1")
    data = _http_get_json(url)
    if not isinstance(data, dict) or not data.get("success"):
        # 兜底：返回空结构而非 error，下游模块已处理 None
        return {"top10": [], "controller": "", "institutional_pct": 0, "latest_date": ""}

    rows = (data.get("result") or {}).get("data") or []
    top10: List[dict] = []
    for row in rows[:10]:
        if not isinstance(row, dict):
            continue
        top10.append({
            "name": row.get("HOLDER_NAME", ""),
            "pct": _safe_float(row.get("HOLD_RATIO")),
            "change": row.get("HOLD_CHANGE", ""),
            "type": row.get("HOLDER_TYPE", ""),
        })
    return {
        "top10": top10,
        "controller": "",
        "institutional_pct": 0,
        "latest_date": rows[0].get("END_DATE", "") if rows else "",
    }


@cached(ttl=TTL_F10_GOVERNANCE, key_fn=lambda code: _normalize_code(code))
def fetch_f10_dividends(code: str) -> List[dict]:
    """分红送转历史"""
    secucode = _normalize_code(code)
    url = (f"https://datacenter-web.eastmoney.com/api/data/v1/get"
           f"?reportName=RPT_F10_EH_DIVIDEND&columns=ALL"
           f"&filter=(SECUCODE%3D%22{urllib.parse.quote(secucode)}%22)"
           f"&pageSize=20&pageNumber=1"
           f"&sortColumns=REPORT_DATE&sortTypes=-1")
    data = _http_get_json(url)
    if not isinstance(data, dict) or not data.get("success"):
        return []
    rows = (data.get("result") or {}).get("data") or []
    parsed: List[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed.append({
            "report_date": str(row.get("REPORT_DATE", ""))[:10],
            "cash_dividend_per_10": _safe_float(row.get("ASSIGN_RATIO") or row.get("PHB")),
            "stock_dividend_per_10": _safe_float(row.get("ASSIGN_NUM") or row.get("PSB")),
            "total_amount": _safe_float(row.get("TOTAL_DIVIDEND") or row.get("BPHR")),
            "implementation_date": str(row.get("IMPLEMENTATION_DATE") or row.get("GQDJR", ""))[:10],
        })
    parsed.sort(key=lambda x: x.get("report_date", ""), reverse=True)
    return parsed


@cached(ttl=TTL_F10_GOVERNANCE, key_fn=lambda code: _normalize_code(code))
def fetch_f10_management(code: str) -> dict:
    """
    高管/治理信息。接口可能不稳定，失败返回空结构。
    """
    # 东财 F10 高管接口较不稳定，返回空结构作为兜底
    # 下游 management.py 已处理 insufficient_data 路径
    return {
        "board_size": 0,
        "independent_directors": 0,
        "independent_pct": 0,
        "top3_salary": 0,
        "exec_list": [],
    }


# ─────────────────────────────────────────────────────
# 一站式获取（供 value_investing 模块使用）
# ─────────────────────────────────────────────────────

def fetch_all_financials(code: str, years: int = 5) -> dict:
    """
    一次性获取利润表/资产负债表/现金流量表/主要指标/股东/分红/治理。

    供 value_investing.decision_integration 调用，减少重复网络请求。
    所有字段已归一化，下游模块可直接使用。
    """
    bare = _bare_code(code)
    return {
        "code": bare,
        "secucode": _normalize_code(code),
        "income": fetch_income_statement(bare, years),
        "balance": fetch_balance_sheet(bare, years),
        "cashflow": fetch_cashflow_statement(bare, years),
        "indicators": fetch_financial_indicators(bare, years),
        "shareholders": fetch_f10_shareholders(bare),
        "dividends": fetch_f10_dividends(bare),
        "management": fetch_f10_management(bare),
    }


def filter_annual_reports(statements: List[dict]) -> List[dict]:
    """从多期报表中筛选年报（12-31 报告期）"""
    return [s for s in statements if str(s.get("report_date", "")).endswith("12-31")]


def filter_recent_n_years(statements: List[dict], n: int = 5) -> List[dict]:
    """筛选年报并取最近 n 年（按报告期降序）"""
    annuals = filter_annual_reports(statements)
    return annuals[:n]


def fetch_financials_akshare(code: str, market: str = "cn") -> dict:
    """v8.0: 港美股财务（akshare 补 financial_statements 的沪深-only 缺口）。

    仅对 hk:/us: 代码启用；akshare 未装或失败返回 {}（诚实降级，不抛异常）。
    """
    if market not in ("hk", "us"):
        return {}
    try:
        from stock_researcher.data.akshare_provider import ak_financial_indicators
        return ak_financial_indicators(code, market=market)
    except Exception:
        return {}
