# -*- coding: utf-8 -*-
"""
market_data_scraper.py v1.0 — 市场宏观数据爬虫（v4.7 新增）
============================================================
提供宏观利率类金融数据：
  1. LPR 贷款市场报价利率    — 全国银行间同业拆借中心（chinamoney.com.cn）
  2. 国债收益率曲线         — 中债登（chinabond.com.cn）

数据源:
    - LPR:      https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis
    - 国债收益率: https://yield.chinabond.com.cn/cbweb-mn/yc/inityc

设计要点:
    - 优先 requests，不可用时回退 http_utils（标准库）
    - 全部函数异常安全：失败返回空列表 / 空 dict + warning
    - 无第三方强依赖，可在缺包环境下 import 与测试
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

try:
    import requests as _requests
    _HAS_REQUESTS = True
except ImportError:
    _HAS_REQUESTS = False
    try:
        from .http_utils import http_get, http_post, rate_limit
    except ImportError:
        from http_utils import http_get, http_post, rate_limit  # type: ignore

log = logging.getLogger(__name__)

# ==================== 常量 ====================

CHINAMONEY_LPR_API = "https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/LprHis"
CHINABOND_YIELD_API = "https://yield.chinabond.com.cn/cbweb-mn/yc/inityc"

# 中国货币网请求头
CM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.chinamoney.com.cn/",
}

# 中债登请求头
CB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://yield.chinabond.com.cn/cbweb-mn/yield_main?locale=zh_CN",
}

# ==================== 工具函数 ====================


def _safe_float(val, default=0.0):
    """安全转换为浮点数。"""
    if val is None:
        return default
    if isinstance(val, str) and val.strip() in ("-", "--", "", "—"):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    """安全转换为字符串。"""
    if val is None:
        return default
    return str(val)


def _normalize_date(date_val) -> str:
    """将各类日期格式规范为 yyyy-MM-dd；None/空 返回空串。"""
    if date_val is None:
        return ""
    d = str(date_val).strip()
    if not d:
        return ""
    d = d.replace("/", "-").replace(".", "-")
    # "2026-7-1" → "2026-07-01"
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError:
        return d[:10]


# ==================== LPR 贷款市场报价利率 ====================


def get_lpr_rates(days: int = 365, start_date: str = "",
                  end_date: str = "") -> List[Dict]:
    """获取 LPR 贷款市场报价利率历史数据。

    数据来源: 全国银行间同业拆借中心 LprHis 接口
    对应页面: https://www.chinamoney.com.cn/chinese/bklpr/

    Args:
        days: 返回最近 N 天内的报价记录，默认 365
        start_date: 起始日期 yyyy-MM-dd（严格过滤）
        end_date: 截止日期 yyyy-MM-dd

    Returns:
        [
            {"date": "2026-07-20", "one_year": 3.00, "five_year": 3.50}, ...
        ]
    """
    page_size = max(1, min(days * 2 + 10, 200))
    url = CHINAMONEY_LPR_API
    if _HAS_REQUESTS:
        try:
            resp = _requests.post(
                url, json={"pageNum": 1, "pageSize": page_size},
                headers=CM_HEADERS, timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error(f"LPR 请求失败: {e}")
            return []
    else:
        try:
            from .http_utils import http_post, rate_limit
        except ImportError:
            from http_utils import http_post, rate_limit  # type: ignore
        rate_limit(url=url)
        body = json.dumps({"pageNum": 1, "pageSize": page_size}).encode("utf-8")
        resp = http_post(url, data=body, headers={**CM_HEADERS, "Content-Type": "application/json"}, timeout=15)
        if resp is None:
            return []
        try:
            data = json.loads(resp.text)
        except Exception:
            return []

    records = data.get("records") or data.get("data") or []
    results = []
    for r in records:
        date = _normalize_date(_safe_str(r.get("showDateCN", r.get("showDateEN", ""))))
        one_year = _safe_float(r.get("1Y"))
        five_year = _safe_float(r.get("5Y"))
        if not date:
            continue
        results.append({
            "date": date,
            "one_year": one_year,
            "five_year": five_year,
        })
    # 去重（同月可能多条），保留最新
    seen = {}
    for r in results:
        seen[r["date"]] = r
    results = sorted(seen.values(), key=lambda x: x["date"], reverse=True)

    # 严格日期过滤
    if start_date:
        results = [r for r in results if r["date"] >= start_date]
    if end_date:
        results = [r for r in results if r["date"] <= end_date]
    results = results[:max(1, days // 28 + 2)] if not (start_date or end_date) else results
    log.info(f"获取 LPR 利率 {len(results)} 条")
    return results


# ==================== 国债收益率曲线 ====================


def get_bond_yield_curve(curve_type: str = "treasury", date: str = "") -> Dict:
    """获取国债收益率曲线。

    数据来源: 中债登 yield.chinabond.com.cn inityc 接口
    对应页面: https://yield.chinabond.com.cn/cbweb-mn/yield_main

    Args:
        curve_type: 曲线类型，"treasury"(国债，默认) / "policy"(政策性金融债)
        date: 指定日期 yyyy-MM-dd，为空返回最新曲线

    Returns:
        {
            "date": "2026-07-31",          # 曲线日期
            "curve_type": "中债国债收益率曲线(到期)",
            "source": "中债登 chinabond.com.cn",
            "terms": {"1Y": 2.15, "2Y": 2.25, ..., "30Y": 3.05},
            "spread_10_2": 0.46,           # 10年-2年利差
            "spread_30_10": 0.34,          # 30年-10年利差
            "curve_points": [[0.0, 1.15], ...],  # 完整曲线点（年, 收益率）
        }
    """
    xyz = "txy" if curve_type != "policy" else "tpxy"
    params = {
        "xyzSelect": xyz,
        "workTime": "",
        "dxbj": "0",
        "qxll": "0",
        "yqqxN": "N",
        "yqqxK": "K",
        "wrjxCBFlag": "0",
        "locale": "zh_CN",
    }
    url = CHINABOND_YIELD_API

    if _HAS_REQUESTS:
        try:
            resp = _requests.post(url, data=params, headers=CB_HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error(f"国债收益率请求失败: {e}")
            return {"error": f"请求失败: {e}", "warning": "中债登接口不可用"}
    else:
        try:
            from .http_utils import http_post, rate_limit
        except ImportError:
            from http_utils import http_post, rate_limit  # type: ignore
        rate_limit(url=url)
        resp = http_post(url, data=params, headers=CB_HEADERS, timeout=15)
        if resp is None:
            return {"error": "请求失败", "warning": "中债登接口不可用"}
        try:
            data = json.loads(resp.text)
        except Exception:
            return {"error": "响应解析失败", "warning": "中债登接口不可用"}

    try:
        if not isinstance(data, list) or len(data) < 2:
            return {"error": "响应结构异常", "warning": "中债登接口返回格式异常"}
        curve_obj = data[1][1][0] if len(data) > 1 and isinstance(data[1], list) and data[1] else None
        if not isinstance(curve_obj, dict):
            return {"error": "曲线数据为空", "warning": "当前日期无曲线数据"}
        series = curve_obj.get("seriesData") or []
        worktime = _normalize_date(_safe_str(curve_obj.get("worktime", "")))
        curve_name = _safe_str(curve_obj.get("ycDefName", "国债收益率曲线"))
    except (IndexError, TypeError, KeyError) as e:
        log.error(f"国债收益率解析失败: {e}")
        return {"error": f"解析失败: {e}", "warning": "中债登接口返回格式异常"}

    # 从完整曲线点中提取标准期限收益率（年 → 收益率）
    target_years = {"1Y": 1, "2Y": 2, "3Y": 3, "5Y": 5, "7Y": 7, "10Y": 10, "30Y": 30}
    terms: Dict[str, float] = {}
    for label, year in target_years.items():
        # 找到最接近该年限的曲线点
        best = None
        best_diff = float("inf")
        for pt in series:
            try:
                y, v = float(pt[0]), float(pt[1])
            except (TypeError, ValueError, IndexError):
                continue
            diff = abs(y - year)
            if diff < best_diff:
                best_diff = diff
                best = v
        if best is not None and best_diff < 0.05:
            terms[label] = round(best, 4)

    result = {
        "date": worktime,
        "curve_type": curve_name,
        "source": "中债登 chinabond.com.cn",
        "terms": terms,
        "curve_points": [[round(float(p[0]), 3), round(float(p[1]), 4)] for p in series if len(p) >= 2],
    }
    if "2Y" in terms and "10Y" in terms:
        result["spread_10_2"] = round(terms["10Y"] - terms["2Y"], 4)
    if "10Y" in terms and "30Y" in terms:
        result["spread_30_10"] = round(terms["30Y"] - terms["10Y"], 4)
    log.info(f"获取国债收益率曲线 {worktime}，期限点 {len(terms)} 个")
    return result


# ==================== 便捷入口 ====================


def get_market_data(data_type: str, **kwargs) -> Any:
    """市场数据统一便捷入口。

    Args:
        data_type: "lpr_rates" / "bond_yield_curve" / "macro_cpi" / "macro_ppi"
                   / "macro_pmi" / "macro_gdp" / "macro_m2"
        **kwargs: 传递给对应函数的参数
    Returns:
        对应数据（LPR 为列表，国债收益率为 dict，宏观序列为列表）
    """
    if data_type == "lpr_rates":
        return get_lpr_rates(
            days=kwargs.get("days", 365),
            start_date=kwargs.get("start_date", ""),
            end_date=kwargs.get("end_date", ""),
        )
    if data_type == "bond_yield_curve":
        return get_bond_yield_curve(
            curve_type=kwargs.get("curve_type", "treasury"),
            date=kwargs.get("date", ""),
        )
    if data_type.startswith("macro_"):
        indicator = data_type[len("macro_"):]
        if indicator not in MACRO_REPORTS:
            log.error(f"不支持的宏观指标: {indicator}，"
                      f"可选: {'/'.join(MACRO_REPORTS)}")
            return {"error": f"不支持的数据类型: {data_type}"}
        return get_macro_indicator(indicator, limit=kwargs.get("limit", 24))
    log.error(f"不支持的数据类型: {data_type}，可选: lpr_rates / bond_yield_curve / "
              f"macro_cpi / macro_ppi / macro_pmi / macro_gdp / macro_m2")
    return {"error": f"不支持的数据类型: {data_type}"}


# ==================== v7.0.0 宏观经济序列（东财 datacenter 接口）====================

# 东财数据中心宏观报表名（datacenter-web 域名独立于 push2，互不影响）
EM_DATACENTER_API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
EM_DATACENTER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/133.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://data.eastmoney.com/",
}

MACRO_REPORTS = {
    # indicator: (reportName, 字段映射 → 统一输出键)
    "cpi": ("RPT_ECONOMY_CPI", {"NATIONAL_SAME": "yoy",
                                "NATIONAL_SEQUENTIAL": "mom",
                                "NATIONAL_ACCUMULATE": "accumulate"}),
    "ppi": ("RPT_ECONOMY_PPI", {"BASE_SAME": "yoy",
                                "BASE": "value",
                                "BASE_ACCUMULATE": "accumulate"}),
    "pmi": ("RPT_ECONOMY_PMI", {"MAKE_INDEX": "manufacturing",
                                "NO_MAKE_INDEX": "non_manufacturing"}),
    "gdp": ("RPT_ECONOMY_GDP", {"SUM_SAME": "yoy",
                                "DOMESTICL_PRODUCT_BASE": "value",
                                "FIRST_SAME": "primary_yoy",
                                "SECOND_SAME": "secondary_yoy",
                                "THIRD_SAME": "tertiary_yoy"}),
    "m2":  ("RPT_ECONOMY_CURRENCY_SUPPLY", {"CURRENCY": "m2",
                                            "CURRENCY_SAME": "m2_yoy",
                                            "BASIC_CURRENCY": "m0_m1_base",
                                            "FREE_CASH": "m0"}),
}


def get_macro_indicator(indicator: str = "cpi", limit: int = 24) -> List[Dict]:
    """宏观经济月度/季度序列（CPI/PPI/PMI/GDP/M2）。

    零 pip 依赖（纯 HTTP），作为 akshare 不可用时的兜底；
    返回按时间倒序的 [{"date","time",...指标}], 失败返回 []。
    """
    indicator = (indicator or "").lower().strip()
    if indicator not in MACRO_REPORTS:
        log.error(f"不支持的宏观指标: {indicator}，可选: {'/'.join(MACRO_REPORTS)}")
        return []
    report_name, field_map = MACRO_REPORTS[indicator]
    params = (
        f"?reportName={report_name}&columns=ALL&pageSize={max(1, min(limit, 200))}"
        f"&pageNumber=1&sortColumns=REPORT_DATE&sortTypes=-1&source=WEB"
    )
    url = EM_DATACENTER_API + params
    try:
        if _HAS_REQUESTS:
            r = _requests.get(url, headers=EM_DATACENTER_HEADERS, timeout=15)
            data = r.json()
        else:
            from http_utils import http_get  # type: ignore
            resp = http_get(url, headers=EM_DATACENTER_HEADERS, timeout=15,
                            rate_limit_delay=0)
            if resp is None:
                return []
            data = resp.json()
        rows = (data.get("result") or {}).get("data") or []
        out = []
        for row in rows:
            item = {"date": str(row.get("REPORT_DATE", ""))[:10],
                    "time": row.get("TIME", "")}
            for src, dst in field_map.items():
                if row.get(src) is not None:
                    item[dst] = _safe_float(row.get(src))
            if item["date"]:
                out.append(item)
        return out
    except Exception as e:
        log.warning(f"宏观指标 {indicator} 获取失败: {e}")
        return []


# ==================== CLI 测试入口 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("市场数据爬虫 v1.0 — 功能测试")
    print("=" * 60)
    print("\n[测试1] LPR 利率（近 5 条）")
    for r in get_lpr_rates(days=150)[:5]:
        print(f"  {r['date']}: 1Y={r['one_year']}% 5Y={r['five_year']}%")
    print("\n[测试2] 国债收益率曲线")
    curve = get_bond_yield_curve()
    print(f"  日期: {curve.get('date')} 类型: {curve.get('curve_type')}")
    print(f"  期限: {curve.get('terms')}")
    print(f"  10Y-2Y 利差: {curve.get('spread_10_2')}")
    print("\n" + "=" * 60)
