# -*- coding: utf-8 -*-
"""akshare 数据源提供者（akshare_provider.py，v8.0 新增）

唯一 import akshare 的模块；akshare 未安装时 HAS_AKSHARE=False，所有函数返回空/None，
保持核心零依赖语义。akshare 覆盖：基金净值 / 债券 / 可转债 / 宏观 / 港美股财务 / ETF 成分。

用法：
    from stock_researcher.data.akshare_provider import ak_fund_nav, has_akshare
    if has_akshare():
        nav = ak_fund_nav("000001")
"""

import logging

logger = logging.getLogger(__name__)

try:
    import akshare as ak  # noqa: F401
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    ak = None  # type: ignore


def has_akshare() -> bool:
    return HAS_AKSHARE


def _safe_call(func_name: str, *args, **kwargs):
    """门控调用 akshare 函数（按名解析）；未装/函数缺失/失败返回 None。"""
    if not HAS_AKSHARE or ak is None:
        return None
    func = getattr(ak, func_name, None)
    if func is None:
        return None
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.debug("akshare %s 调用失败: %s", func_name, e)
        return None


def _df_to_records(result):
    """DataFrame → list[dict]（或原样返回 list）。"""
    if result is None:
        return None
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict("records")
        except Exception:
            return None
    return result


# ============================================================
# 基金净值
# ============================================================

def ak_fund_nav(fund_code: str) -> dict:
    """基金净值走势（akshare fund_open_fund_info_em）。"""
    result = _safe_call("fund_open_fund_info_em", fund=fund_code, indicator="单位净值走势")
    records = _df_to_records(result)
    if not records:
        return {}
    navs = []
    for r in records:
        v = r.get("单位净值") or r.get("净值") or r.get("value")
        if v is not None:
            try:
                navs.append(float(v))
            except (TypeError, ValueError):
                pass
    return {"nav_series": navs, "source": "akshare", "data_quality": "actual"}


# ============================================================
# 债券 / 可转债
# ============================================================

def ak_bond_yield() -> list:
    """中债国债收益率曲线（akshare bond_china_yield）。"""
    records = _df_to_records(_safe_call("bond_china_yield"))
    return records or []


def ak_convertible_quote(code: str) -> dict:
    """可转债行情（转股价/正股价等）— 尽力而为，字段可能随 akshare 版本变化。"""
    records = _df_to_records(_safe_call("bond_zh_hs_cov_spot")) or []
    for r in records:
        c = str(r.get("代码", ""))
        if c == code:
            return {
                "cb_price": r.get("最新价") or r.get("价格"),
                "conversion_price": r.get("转股价"),
                "stock_price": r.get("正股价"),
                "maturity_years": r.get("剩余年限"),
                "cb_name": r.get("名称", ""),
                "source": "akshare",
            }
    return {}


# ============================================================
# 宏观指标（与 data/macro.py 协作兜底）
# ============================================================

_AK_MACRO = {
    "gdp": "macro_china_gdp",
    "cpi": "macro_china_cpi",
    "ppi": "macro_china_ppi",
    "pmi": "macro_china_pmi",
    "m2": "macro_china_m2_yearly",
}


def ak_macro(indicator: str) -> dict:
    """宏观指标（akshare macro_china_* 系列），返回最新一期。"""
    func_name = _AK_MACRO.get(indicator)
    if not func_name or not HAS_AKSHARE:
        return {}
    records = _df_to_records(_safe_call(func_name)) or []
    if not records:
        return {}
    # 取最新一期（日期字符串最大；升序/降序均兼容）
    def _date_key(r):
        for k in ("日期", "月份", "时间", "date", "报告期"):
            v = r.get(k)
            if v:
                return str(v)
        return ""
    latest = max(records, key=_date_key)
    # 字段名随 akshare 版本而异，尽力提取
    value = (latest.get("数值") or latest.get("值") or latest.get("今值")
             or latest.get("value") or latest.get("指标值")
             or latest.get("current") or latest.get("今值(%)"))
    date = (latest.get("日期") or latest.get("月份") or latest.get("时间")
            or latest.get("date") or "")
    return {"indicator": indicator, "value": value, "date": str(date),
            "source": "akshare", "data_quality": "actual"}


# ============================================================
# 港美股财务（补 financial_statements 的沪深-only 缺口）
# ============================================================

def ak_financial_indicators(code: str, market: str = "cn") -> dict:
    """财务指标（A股/港股/美股均可尝试）。
    A股: stock_financial_abstract（东财）
    港股: stock_financial_hk_analysis_indicator_em
    美股: stock_financial_analysis_indicator_em
    """
    if market == "hk":
        records = _df_to_records(_safe_call("stock_financial_hk_analysis_indicator_em", symbol=code))
    elif market == "us":
        records = _df_to_records(_safe_call("stock_financial_analysis_indicator_em", symbol=code))
    else:
        records = _df_to_records(_safe_call("stock_financial_abstract", symbol=code))
    if not records:
        return {}
    latest = records[-1]
    return {
        "roe": latest.get("净资产收益率") or latest.get("ROE"),
        "eps": latest.get("每股收益") or latest.get("EPS"),
        "revenue": latest.get("营业总收入") or latest.get("营业收入"),
        "net_profit": latest.get("净利润") or latest.get("归母净利润"),
        "report_date": latest.get("报告期") or latest.get("日期") or "",
        "source": "akshare",
        "data_quality": "actual",
    }


# ============================================================
# ETF 成分
# ============================================================

def ak_etf_components(etf_code: str) -> list:
    """ETF 成分股（akshare fund_etf_fund_info_em）。"""
    records = _df_to_records(_safe_call("fund_etf_fund_info_em", fund=etf_code))
    return records or []


def self_check() -> dict:
    return {
        "akshare_installed": HAS_AKSHARE,
        "providers": ["fund_nav", "bond_yield", "convertible", "macro",
                      "hk_us_financial", "etf_components"],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(self_check(), ensure_ascii=False, indent=2))
