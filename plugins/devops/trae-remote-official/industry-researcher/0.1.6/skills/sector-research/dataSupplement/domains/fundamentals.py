# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 基本面数据
============================================

提供公司财务报表、关键指标和公司概况的统一查询接口。
根据市场自动路由至最合适的数据源并实现 fallback。

数据源分配:
  - A股财报: 新浪 CompanyFinanceService
  - A股指标: 通达信季报 + 腾讯行情(PE/PB)
  - A股公司: 通达信 F10
  - 美股/港股: Yahoo quoteSummary
"""

from __future__ import annotations

import os
import sys
import logging
from typing import List, Optional

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.ticker import detect_market, normalize, to_yahoo_symbol, to_tencent_code
from providers import sina, tdx, yahoo, tencent

logger = logging.getLogger(__name__)


def financial_statements(code: str, report_type: str = "income") -> list[dict]:
    """获取财报三表数据（利润表/资产负债表/现金流量表）。

    根据市场自动路由数据源:
    - A股: 新浪 CompanyFinanceService
    - 美股: Yahoo quoteSummary → SEC XBRL
    - 港股: Yahoo quoteSummary

    Args:
        code: 证券代码，如 "600519", "AAPL", "00700"
        report_type: 报表类型，可选值:
            - "income": 利润表（默认）
            - "balance": 资产负债表
            - "cashflow": 现金流量表

    Returns:
        报表数据列表，每项为一个报告期的字段字典:
        [
            {
                report_date: 报告期日期,
                ... (各报表具体字段)
            },
            ...
        ]
        获取失败返回空列表 []。

    Fallback:
        A股: 新浪 CompanyFinanceService
        美股: Yahoo quoteSummary → SEC XBRL
        港股: Yahoo quoteSummary
    """
    market = detect_market(code)
    normalized = normalize(code)

    # 报表类型映射统一
    type_alias = {
        "income": "income",
        "profit": "income",
        "balance": "balance_sheet",
        "balance_sheet": "balance_sheet",
        "cashflow": "cashflow",
        "cash_flow": "cashflow",
    }
    report_type = type_alias.get(report_type, "income")

    if market == "CN":
        return _financial_cn(normalized, report_type)
    elif market == "US":
        return _financial_us(normalized, report_type)
    else:
        return _financial_hk(normalized, report_type)


def key_metrics(code: str) -> dict:
    """获取关键财务指标。

    汇总 PE/PB/ROE/毛利率/净利率/营收增长/净利增长等核心估值与盈利指标。

    数据源:
        A股: 通达信季报(ROE/毛利率等) + 腾讯行情(PE/PB/市值)
        美股/港股: Yahoo quoteSummary defaultKeyStatistics + financialData

    Args:
        code: 证券代码

    Returns:
        关键指标字典:
        {
            code: 证券代码,
            name: 证券名称,
            pe: 市盈率(动态),
            pe_ttm: 市盈率(TTM),
            pb: 市净率,
            roe: 净资产收益率(%),
            gross_margin: 毛利率(%),
            net_margin: 净利率(%),
            revenue_growth: 营收同比增长(%),
            profit_growth: 净利润同比增长(%),
            market_cap: 总市值,
            market: 市场标识,
        }
        获取失败返回空字典 {}。
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        return _metrics_cn(normalized)
    elif market == "US":
        return _metrics_us(normalized)
    else:
        return _metrics_hk(normalized)


def company_profile(code: str) -> dict:
    """获取公司基本信息。

    包含行业、主营业务、市值、股本、上市日期等核心公司信息。

    数据源:
        A股: 通达信 F10 公司概况
        美股/港股: Yahoo quoteSummary assetProfile

    Args:
        code: 证券代码

    Returns:
        公司信息字典:
        {
            code: 证券代码,
            name: 公司名称,
            industry: 所属行业,
            business: 主营业务描述,
            market_cap: 总市值,
            total_shares: 总股本,
            float_shares: 流通股本,
            listing_date: 上市日期,
            market: 市场标识,
        }
        获取失败返回空字典 {}。
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        return _profile_cn(normalized)
    elif market == "US":
        return _profile_us(normalized)
    else:
        return _profile_hk(normalized)


# ===========================================================================
# A股 基本面实现
# ===========================================================================


def _financial_cn(code: str, report_type: str) -> list[dict]:
    """A股财报: 新浪 CompanyFinanceService → akshare(新浪封装) → Yahoo"""

    # 新浪接口的报表类型映射
    sina_type_map = {
        "income": "income",
        "balance_sheet": "balance_sheet",
        "cashflow": "cashflow",
    }
    sina_type = sina_type_map.get(report_type, "income")

    try:
        result = sina.financial_report(code=code, report_type=sina_type)
        if result:
            return result
    except Exception as e:
        logger.debug(f"新浪A股财报获取失败({code}, {report_type}): {e}")

    # 降级 1: akshare 封装的新浪财报（CompanyFinanceService 下线后的主力替代）
    try:
        from providers import akshare_bridge
        result = akshare_bridge.financial_report_cn(code=code, report_type=report_type)
        if result:
            return result
    except Exception as e:
        logger.debug(f"akshare A股财报降级获取失败({code}, {report_type}): {e}")

    # 降级 2: Yahoo（A股也有数据）
    try:
        yahoo_symbol = to_yahoo_symbol(code)
        return _yahoo_financial(yahoo_symbol, report_type)
    except Exception as e:
        logger.debug(f"Yahoo A股财报降级获取失败({code}): {e}")

    logger.warning(f"A股财报所有数据源获取失败: {code}")
    return []


def _financial_us(code: str, report_type: str) -> list[dict]:
    """美股财报: Yahoo quoteSummary → SEC XBRL"""

    # 第一优先: Yahoo
    try:
        yahoo_symbol = to_yahoo_symbol(code)
        result = _yahoo_financial(yahoo_symbol, report_type)
        if result:
            return result
    except Exception as e:
        logger.debug(f"Yahoo美股财报获取失败({code}, {report_type}): {e}")

    # TODO: SEC XBRL 作为二级降级源
    logger.warning(f"美股财报数据源获取失败: {code}")
    return []


def _financial_hk(code: str, report_type: str) -> list[dict]:
    """港股财报: Yahoo quoteSummary"""

    try:
        yahoo_symbol = to_yahoo_symbol(code)
        result = _yahoo_financial(yahoo_symbol, report_type)
        if result:
            return result
    except Exception as e:
        logger.debug(f"Yahoo港股财报获取失败({code}, {report_type}): {e}")

    logger.warning(f"港股财报数据源获取失败: {code}")
    return []


def _yahoo_financial(symbol: str, report_type: str) -> list[dict]:
    """通过 Yahoo quoteSummary 获取财报数据。

    使用 incomeStatementHistory / balanceSheetHistory / cashflowStatementHistory
    模块获取年度报表数据。
    """
    module_map = {
        "income": "incomeStatementHistory",
        "balance_sheet": "balanceSheetHistory",
        "cashflow": "cashflowStatementHistory",
    }
    module_name = module_map.get(report_type, "incomeStatementHistory")

    summary = yahoo.quote_summary(symbol=symbol, modules=[module_name])
    if not summary:
        return []

    history_data = summary.get(module_name, {})
    statements = history_data.get(
        module_name.replace("History", "s", 1) if "History" in module_name
        else "incomeStatementHistory",
        []
    )

    # Yahoo 返回嵌套结构，每个字段形如 {"raw": 123, "fmt": "123"}
    # 统一提取 raw 值
    results = []
    for stmt in statements:
        record = {}
        for key, val in stmt.items():
            if isinstance(val, dict) and "raw" in val:
                record[key] = val["raw"]
            elif isinstance(val, dict) and "fmt" in val:
                record[key] = val["fmt"]
            else:
                record[key] = val
        if record:
            results.append(record)

    return results


# ===========================================================================
# A股 关键指标
# ===========================================================================


def _metrics_cn(code: str) -> dict:
    """A股关键指标: 通达信季报 + 腾讯行情。"""

    result = {
        "code": code,
        "name": "",
        "pe": None,
        "pe_ttm": None,
        "pb": None,
        "roe": None,
        "gross_margin": None,
        "net_margin": None,
        "revenue_growth": None,
        "profit_growth": None,
        "market_cap": None,
        "market": "CN",
    }

    # 第一步: 通达信财务摘要（ROE/毛利率/增长率等）
    try:
        finance = tdx.finance_summary(code)
        if finance:
            result["roe"] = _safe_float(finance.get("roe", finance.get("净资产收益率")))
            result["gross_margin"] = _safe_float(
                finance.get("gross_profit_margin", finance.get("毛利率"))
            )
            result["net_margin"] = _safe_float(
                finance.get("net_profit_margin", finance.get("净利率"))
            )
            result["revenue_growth"] = _safe_float(
                finance.get("revenue_growth_rate", finance.get("营收增长率"))
            )
            result["profit_growth"] = _safe_float(
                finance.get("net_profit_growth_rate", finance.get("净利润增长率"))
            )
    except Exception as e:
        logger.debug(f"通达信财务摘要获取失败({code}): {e}")

    # 第二步: 腾讯行情补充 PE/PB/市值/名称
    try:
        tencent_code = to_tencent_code(code)
        quotes = tencent.quote([tencent_code])
        if quotes:
            q = quotes[0]
            result["name"] = q.get("name", "")
            result["pe"] = _safe_float(q.get("pe"))
            result["pe_ttm"] = _safe_float(q.get("pe_dynamic", q.get("pe")))
            result["pb"] = _safe_float(q.get("pb"))
            result["market_cap"] = _safe_float(q.get("market_cap"))
    except Exception as e:
        logger.debug(f"腾讯行情指标获取失败({code}): {e}")

    return result


def _metrics_us(code: str) -> dict:
    """美股关键指标: Yahoo quoteSummary defaultKeyStatistics + financialData"""
    return _metrics_yahoo(code, "US")


def _metrics_hk(code: str) -> dict:
    """港股关键指标: Yahoo quoteSummary defaultKeyStatistics + financialData"""
    return _metrics_yahoo(code, "HK")


def _metrics_yahoo(code: str, market: str) -> dict:
    """美股/港股关键指标统一实现: Yahoo quoteSummary defaultKeyStatistics + financialData"""

    try:
        yahoo_symbol = to_yahoo_symbol(code)
        summary = yahoo.quote_summary(
            symbol=yahoo_symbol,
            modules=["defaultKeyStatistics", "financialData", "price"]
        )
        if not summary:
            return {}

        key_stats = summary.get("defaultKeyStatistics", {})
        fin_data = summary.get("financialData", {})
        price_data = summary.get("price", {})

        return {
            "code": code,
            "name": _extract_raw(price_data.get("shortName", price_data.get("longName", ""))),
            "pe": _extract_raw(key_stats.get("forwardPE", key_stats.get("trailingPE"))),
            "pe_ttm": _extract_raw(key_stats.get("trailingPE")),
            "pb": _extract_raw(key_stats.get("priceToBook")),
            "roe": _pct_raw(fin_data.get("returnOnEquity")),
            "gross_margin": _pct_raw(fin_data.get("grossMargins")),
            "net_margin": _pct_raw(fin_data.get("profitMargins")),
            "revenue_growth": _pct_raw(fin_data.get("revenueGrowth")),
            "profit_growth": _pct_raw(fin_data.get("earningsGrowth")),
            "market_cap": _extract_raw(price_data.get("marketCap")),
            "market": market,
        }
    except Exception as e:
        logger.debug(f"Yahoo{market}股指标获取失败({code}): {e}")
        return {}


# ===========================================================================
# 公司概况
# ===========================================================================


def _profile_cn(code: str) -> dict:
    """A股公司概况: 通达信 F10"""

    result = {
        "code": code,
        "name": "",
        "industry": "",
        "business": "",
        "market_cap": None,
        "total_shares": None,
        "float_shares": None,
        "listing_date": "",
        "market": "CN",
    }

    # 通达信 F10 公司概况（category=0）
    try:
        info_text = tdx.company_info(code=code, category=0)
        if info_text:
            result["business"] = info_text[:500]  # 截取前 500 字符
            # 尝试从文本中提取结构化信息
            result.update(_parse_tdx_f10(info_text))
    except Exception as e:
        logger.debug(f"通达信F10获取失败({code}): {e}")

    # 补充行情数据中的名称和市值
    try:
        tencent_code = to_tencent_code(code)
        quotes = tencent.quote([tencent_code])
        if quotes:
            q = quotes[0]
            result["name"] = q.get("name", result["name"])
            result["market_cap"] = _safe_float(q.get("market_cap"))
    except Exception as e:
        logger.debug(f"腾讯补充公司信息失败({code}): {e}")

    return result


def _profile_us(code: str) -> dict:
    """美股公司概况: Yahoo quoteSummary assetProfile"""
    return _profile_yahoo(code, "US")


def _profile_hk(code: str) -> dict:
    """港股公司概况: Yahoo quoteSummary assetProfile"""
    return _profile_yahoo(code, "HK")


def _profile_yahoo(code: str, market: str) -> dict:
    """美股/港股公司概况统一实现: Yahoo quoteSummary assetProfile"""

    try:
        yahoo_symbol = to_yahoo_symbol(code)
        summary = yahoo.quote_summary(
            symbol=yahoo_symbol,
            modules=["assetProfile", "price", "defaultKeyStatistics"]
        )
        if not summary:
            return {}

        profile = summary.get("assetProfile", {})
        price_data = summary.get("price", {})
        key_stats = summary.get("defaultKeyStatistics", {})

        return {
            "code": code,
            "name": _extract_raw(price_data.get("shortName", price_data.get("longName", ""))),
            "industry": profile.get("industry", ""),
            "sector": profile.get("sector", ""),
            "business": profile.get("longBusinessSummary", "")[:500],
            "market_cap": _extract_raw(price_data.get("marketCap")),
            "total_shares": _extract_raw(key_stats.get("sharesOutstanding")),
            "float_shares": _extract_raw(key_stats.get("floatShares")),
            "listing_date": "",
            "country": profile.get("country", ""),
            "website": profile.get("website", ""),
            "employees": profile.get("fullTimeEmployees"),
            "market": market,
        }
    except Exception as e:
        logger.debug(f"Yahoo{market}股公司概况获取失败({code}): {e}")
        return {}


# ===========================================================================
# 辅助函数
# ===========================================================================


def _parse_tdx_f10(text: str) -> dict:
    """从通达信 F10 文本中尝试提取结构化字段。

    F10 文本为非结构化中文内容，尝试用关键词匹配提取:
    - 所属行业
    - 上市日期
    - 总股本/流通股本
    """
    import re

    result = {}

    # 行业匹配
    industry_match = re.search(r"(?:所属行业|行业分类)[：:\s]*([^\n\r，,]+)", text)
    if industry_match:
        result["industry"] = industry_match.group(1).strip()

    # 上市日期
    listing_match = re.search(r"(?:上市日期)[：:\s]*([\d\-/]+)", text)
    if listing_match:
        result["listing_date"] = listing_match.group(1).strip()

    # 总股本
    shares_match = re.search(r"(?:总股本)[：:\s]*([\d.]+)\s*(?:万股|亿股)?", text)
    if shares_match:
        result["total_shares"] = _safe_float(shares_match.group(1))

    # 流通股本
    float_match = re.search(r"(?:流通股|流通A股)[：:\s]*([\d.]+)\s*(?:万股|亿股)?", text)
    if float_match:
        result["float_shares"] = _safe_float(float_match.group(1))

    return result


def _extract_raw(val) -> Optional[float | str]:
    """从 Yahoo 嵌套结构中提取 raw 值。

    Yahoo API 字段格式: {"raw": 123.45, "fmt": "123.45"}
    也可能是直接的标量值或字符串。
    """
    if val is None:
        return None
    if isinstance(val, dict):
        return val.get("raw", val.get("fmt"))
    return val


def _pct_raw(val) -> Optional[float]:
    """提取百分比 raw 值并转为百分数（Yahoo 返回小数形式如 0.25 = 25%）。"""
    raw = _extract_raw(val)
    if raw is None:
        return None
    try:
        return round(float(raw) * 100, 2)
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数。"""
    if val is None:
        return None
    try:
        result = float(val)
        return result if result == result else None  # 过滤 NaN
    except (ValueError, TypeError):
        return None
