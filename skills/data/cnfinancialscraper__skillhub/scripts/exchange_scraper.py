# -*- coding: utf-8 -*-
"""
沪深交易所公告与数据爬虫模块

数据源: sse.com.cn（上交所）、szse.cn（深交所）
提供 IPO 日历、上市公司列表、公告搜索等功能。
可作为巨潮资讯 (cninfo.com.cn) 的补充数据源。

主要函数:
    - get_ipo_calendar()                          — 获取近期 IPO 日历
    - get_listed_companies(market="sh")           — 获取上市公司列表
    - search_announcements(keyword, market="both") — 搜索公告（跨交易所）

API:
    深交所:
      - 上市公司列表: http://www.szse.cn/api/report/ShowReport/data (POST)
        SHOWTYPE=JSON, CATALOGID=1110, TABKEY=tab1
    上交所:
      - 股票列表: http://query.sse.com.cn/security/stock/getStockListData.do (GET)
        jsonCallBack=jsonpCallback, isPagination=false, sqlId=COMMON_SSE_GP_GPLB_C
        Referer: www.sse.com.cn

注意事项:
    - 上交所 API 需要 Referer: https://www.sse.com.cn/
    - 两个交易所均可能对请求频率有限制，使用 rate_limit 控制
    - 数据更新频率: 交易日盘后更新
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List

try:
    from .http_utils import http_get, http_get_json, http_post, rate_limit, get_session
except ImportError:
    from http_utils import http_get, http_get_json, http_post, rate_limit, get_session

log = logging.getLogger(__name__)

# ==================== 常量 ====================

# 深交所 API
SZSE_BASE = "http://www.szse.cn"
SZSE_LISTED_COMPANIES_URL = "http://www.szse.cn/api/report/ShowReport/data"
SZSE_IPO_CALENDAR_URL = "http://www.szse.cn/api/report/ShowReport/data"
SZSE_ANNOUNCEMENT_URL = "http://www.szse.cn/api/disc/announcement/annList"

# 上交所 API
SSE_BASE = "https://www.sse.com.cn"
SSE_STOCK_LIST_URL = "http://query.sse.com.cn/security/stock/getStockListData.do"
SSE_IPO_CALENDAR_URL = "http://query.sse.com.cn/security/stock/getStockListData.do"

# 深交所报表系统目录/标签参数（提取为常量，便于交易所改版时集中维护）
SZSE_CATALOG_IPO = "1110"        # IPO 日历目录ID
SZSE_CATALOG_LISTED = "1110"     # 上市公司列表目录ID
SZSE_CATALOG_ANNOUNCEMENT = "1800_cxda"  # 公告查询目录ID
SZSE_TABKEY = "tab1"

# 请求头
SZSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "http://www.szse.cn/",
    "X-Requested-With": "XMLHttpRequest",
    "Content-Type": "application/json",
}

SSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.sse.com.cn/",
    "X-Requested-With": "XMLHttpRequest",
}


# ==================== 安全类型转换 ====================

def _safe_float(val, default=None):
    """安全转换为浮点数"""
    if val is None or val == "" or val == "-":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _safe_str(val, default=""):
    """安全转换为字符串"""
    if val is None:
        return default
    return str(val)


# ==================== IPO 日历 ====================


def _get_szse_ipo_calendar() -> List[Dict[str, Any]]:
    """
    获取深交所 IPO 日历（内部函数）。
    """
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": SZSE_CATALOG_IPO,
        "TABKEY": SZSE_TABKEY,
        "PAGENO": "1",
        "random": "0.123456789",
    }

    rate_limit(url=SZSE_BASE)
    log.info("正在获取深交所 IPO 日历...")

    try:
        resp = http_post(
            SZSE_LISTED_COMPANIES_URL,
            data=params,
            headers=SZSE_HEADERS,
            timeout=30,
        )
        if resp is None:
            log.warning("深交所 IPO 日历请求失败")
            return []

        data = resp.json()
    except Exception as e:
        log.error(f"深交所 IPO 日历解析失败: {e}")
        return []

    # 解析返回数据
    items = data if isinstance(data, list) else data.get("data", [])
    if not items:
        return []

    result = []
    for item in items:
        result.append({
            "market": "sz",
            "stock_code": _safe_str(item.get("zqdm", "")),
            "stock_name": _safe_str(item.get("zqjc", "")),
            "ipo_date": _safe_str(item.get("ssrq", "")),
            "ipo_price": _safe_float(item.get("fxjg")),
            "ipo_pe": _safe_float(item.get("fxssrpe")),
            "status": _safe_str(item.get("status", "")),
        })

    log.info(f"深交所 IPO 日历: {len(result)} 条")
    return result


def _get_sse_ipo_calendar() -> List[Dict[str, Any]]:
    """
    获取上交所 IPO 日历（内部函数）。
    上交所股票查询接口也可查到待上市/新上市股票。
    """
    params = {
        "jsonCallBack": "jsonpCallback",
        "isPagination": "false",
        "sqlId": "COMMON_SSE_GP_GPLB_C",   # 股票列表通用查询
        "pageHelp.cacheSize": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.pageSize": "200",
        "pageHelp.pageNo": "1",
        "pageHelp.endPage": "1",
    }

    rate_limit(url=SSE_BASE)
    log.info("正在获取上交所 IPO 日历...")

    resp = http_get(
        SSE_IPO_CALENDAR_URL,
        params=params,
        headers=SSE_HEADERS,
        timeout=30,
    )
    if resp is None:
        log.warning("上交所 IPO 日历请求失败")
        return []

    # 上交所返回 JSONP 格式，需要提取 JSON 部分
    text = resp.text
    json_match = re.search(r'jsonpCallback\((.*)\)', text, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            log.error("上交所 IPO 数据 JSON 提取失败")
            return []

    try:
        data = json.loads(json_match.group(1) if json_match.lastindex else json_match.group(0))
    except json.JSONDecodeError as e:
        log.error(f"上交所 IPO 数据解析失败: {e}")
        return []

    items = data.get("result", []) or data.get("pageHelp", {}).get("data", [])
    if not items:
        return []

    result = []
    for item in items:
        result.append({
            "market": "sh",
            "stock_code": _safe_str(item.get("SECURITY_CODE_A", "")),
            "stock_name": _safe_str(item.get("SECURITY_ABBR_A", "")),
            "list_date": _safe_str(item.get("LISTING_DATE", "")),
            "total_shares": _safe_float(item.get("TOTAL_SHARES")),
            "info": _safe_str(item.get("REMARK", "")),
        })

    log.info(f"上交所 IPO 日历: {len(result)} 条")
    return result


def get_ipo_calendar(market: str = "both") -> List[Dict[str, Any]]:
    """
    获取近期 IPO 日历（新上市公司信息）。

    分别从深交所和上交所获取最近上市/待上市的公司数据。

    Args:
        market: 交易所选择，可选值:
            - "sh"   : 仅上交所
            - "sz"   : 仅深交所
            - "both" : 沪深两市（默认）

    Returns:
        IPO 日历列表，每项包含:
        - market: 交易所 (sh/sz)
        - stock_code: 股票代码
        - stock_name: 股票名称
        - ipo_date / list_date: 上市日期
        失败返回空列表
    """
    results = []

    if market in ("sz", "both"):
        try:
            results.extend(_get_szse_ipo_calendar())
        except Exception as e:
            log.error(f"深交所 IPO 日历获取异常: {e}")

    if market in ("sh", "both"):
        try:
            results.extend(_get_sse_ipo_calendar())
        except Exception as e:
            log.error(f"上交所 IPO 日历获取异常: {e}")

    log.info(f"IPO 日历汇总: {len(results)} 条（market={market}）")
    return results


# ==================== 上市公司列表 ====================


def _get_szse_listed_companies() -> List[Dict[str, Any]]:
    """
    获取深交所上市公司列表（内部函数）。
    使用深交所报表接口以 POST 请求获取。
    """
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": SZSE_CATALOG_LISTED,
        "TABKEY": SZSE_TABKEY,
        "PAGENO": "1",
        "random": "0.123456789",
    }

    rate_limit(url=SZSE_BASE)
    log.info("正在获取深交所上市公司列表...")

    try:
        resp = http_post(
            SZSE_LISTED_COMPANIES_URL,
            data=params,
            headers=SZSE_HEADERS,
            timeout=30,
        )
        if resp is None:
            log.warning("深交所上市公司列表请求失败")
            return []

        data = resp.json()
    except Exception as e:
        log.error(f"深交所上市公司列表解析失败: {e}")
        return []

    items = data if isinstance(data, list) else data.get("data", [])
    if not items:
        return []

    companies = []
    for item in items:
        company = {
            "market": "sz",
            "stock_code": _safe_str(item.get("zqdm", "")),
            "stock_name": _safe_str(item.get("zqjc", "")),
            "company_name": _safe_str(item.get("gsjc", "")),
            "industry": _safe_str(item.get("ssrq", "")),  # 上市板块
            "list_date": _safe_str(item.get("ssrq", "")),
            "total_shares": _safe_float(item.get("zgb")),
            "area": _safe_str(item.get("area", "")),
        }
        companies.append(company)

    log.info(f"深交所上市公司: {len(companies)} 家")
    return companies


def _get_sse_listed_companies() -> List[Dict[str, Any]]:
    """
    获取上交所上市公司列表（内部函数）。
    """
    params = {
        "jsonCallBack": "jsonpCallback",
        "isPagination": "false",
        "sqlId": "COMMON_SSE_GP_GPLB_C",
        "pageHelp.cacheSize": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.pageSize": "2000",   # 上交所约2000家公司
        "pageHelp.pageNo": "1",
        "pageHelp.endPage": "1",
    }

    rate_limit(url=SSE_BASE)
    log.info("正在获取上交所上市公司列表...")

    resp = http_get(
        SSE_STOCK_LIST_URL,
        params=params,
        headers=SSE_HEADERS,
        timeout=30,
    )
    if resp is None:
        log.warning("上交所上市公司列表请求失败")
        return []

    text = resp.text
    json_match = re.search(r'jsonpCallback\((.*)\)', text, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            log.error("上交所股票列表 JSON 提取失败")
            return []

    try:
        data = json.loads(json_match.group(1) if json_match.lastindex else json_match.group(0))
    except json.JSONDecodeError as e:
        log.error(f"上交所股票列表解析失败: {e}")
        return []

    items = data.get("result", []) or data.get("pageHelp", {}).get("data", [])
    if not items:
        return []

    companies = []
    for item in items:
        company = {
            "market": "sh",
            "stock_code": _safe_str(item.get("SECURITY_CODE_A", "")),
            "stock_name": _safe_str(item.get("SECURITY_ABBR_A", "")),
            "company_name": _safe_str(item.get("COMPANY_ABBR", "")),
            "list_date": _safe_str(item.get("LISTING_DATE", "")),
            "total_shares": _safe_float(item.get("TOTAL_SHARES")),
            "remark": _safe_str(item.get("REMARK", "")),
        }
        companies.append(company)

    log.info(f"上交所上市公司: {len(companies)} 家")
    return companies


def get_listed_companies(market: str = "both") -> List[Dict[str, Any]]:
    """
    获取沪深上市公司列表。

    Args:
        market: 交易所选择，可选值:
            - "sh"   : 仅上交所
            - "sz"   : 仅深交所
            - "both" : 沪深两市（默认）

    Returns:
        上市公司列表，每项包含: market, stock_code, stock_name, list_date 等
        失败返回空列表
    """
    results = []

    if market in ("sz", "both"):
        try:
            results.extend(_get_szse_listed_companies())
        except Exception as e:
            log.error(f"深交所上市公司列表获取异常: {e}")

    if market in ("sh", "both"):
        try:
            results.extend(_get_sse_listed_companies())
        except Exception as e:
            log.error(f"上交所上市公司列表获取异常: {e}")

    log.info(f"上市公司列表汇总: {len(results)} 家（market={market}）")
    return results


# ==================== 公告搜索 ====================


def _search_szse_announcements(keyword: str,
                                max_results: int = 50) -> List[Dict[str, Any]]:
    """
    搜索深交所公告（内部函数）。
    """
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": SZSE_CATALOG_ANNOUNCEMENT,
        "TABKEY": SZSE_TABKEY,
        "txtK": keyword,            # 关键词
        "txtM": "",                 # 证券代码（可选）
        "PAGENO": "1",
        "pageSize": str(min(max_results, 50)),
    }

    rate_limit(url=SZSE_BASE)
    log.info(f"正在搜索深交所公告: keyword={keyword}")

    try:
        resp = http_post(
            SZSE_ANNOUNCEMENT_URL,
            data=params,
            headers=SZSE_HEADERS,
            timeout=30,
        )
        if resp is None:
            log.warning(f"深交所公告搜索请求失败: {keyword}")
            return []

        data = resp.json()
    except Exception as e:
        log.error(f"深交所公告搜索解析失败: {e}")
        return []

    items = data if isinstance(data, list) else data.get("data", [])
    if not items:
        return []

    results = []
    for item in items:
        ann = {
            "market": "sz",
            "title": _safe_str(item.get("title", "")
                               or item.get("gsggbt", "")
                               or item.get("announcementTitle", "")),
            "stock_code": _safe_str(item.get("stockCode", "")
                                    or item.get("zqdm", "")),
            "stock_name": _safe_str(item.get("stockName", "")
                                    or item.get("zqjc", "")),
            "publish_date": _safe_str(item.get("publishDate", "")
                                      or item.get("ggrq", "")),
            "url": _safe_str(item.get("url", "")
                             or item.get("attachPath", "")),
            "category": _safe_str(item.get("category", "")
                                  or item.get("announcementType", "")),
        }
        results.append(ann)

    log.info(f"深交所公告搜索结果: {len(results)} 条")
    return results


def _search_sse_announcements(keyword: str,
                               max_results: int = 50) -> List[Dict[str, Any]]:
    """
    搜索上交所公告（内部函数）。
    上交所公告搜索通过披露查询接口。
    """
    url = "http://query.sse.com.cn/security/stock/queryCompanyBulletin.do"
    params = {
        "jsonCallBack": "jsonpCallback",
        "isPagination": "true",
        "keyWord": keyword,
        "pageHelp.pageSize": str(min(max_results, 50)),
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.endPage": "1",
        "pageHelp.cacheSize": "1",
        "productId": "",
        "securityType": "0101",     # A股
        "reportType2": "DQGG",      # 定期公告
        "reportType": "ALL",        # 所有类型
        "beginDate": "",
        "endDate": "",
    }

    rate_limit(url=SSE_BASE)
    log.info(f"正在搜索上交所公告: keyword={keyword}")

    resp = http_get(url, params=params, headers=SSE_HEADERS, timeout=30)
    if resp is None:
        log.warning(f"上交所公告搜索请求失败: {keyword}")
        return []

    text = resp.text
    json_match = re.search(r'jsonpCallback\((.*)\)', text, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if not json_match:
            log.error("上交所公告 JSON 提取失败")
            return []

    try:
        data = json.loads(json_match.group(1) if json_match.lastindex else json_match.group(0))
    except json.JSONDecodeError as e:
        log.error(f"上交所公告解析失败: {e}")
        return []

    items = data.get("result", []) or data.get("pageHelp", {}).get("data", [])
    if not items:
        return []

    results = []
    for item in items:
        ann = {
            "market": "sh",
            "title": _safe_str(item.get("title", "")
                               or item.get("bulletinTitle", "")),
            "stock_code": _safe_str(item.get("securityCode", "")
                                    or item.get("stockCode", "")),
            "stock_name": _safe_str(item.get("securityAbbr", "")
                                    or item.get("stockName", "")),
            "publish_date": _safe_str(item.get("publishDate", "")
                                      or item.get("bulletinDate", "")),
            "url": _safe_str(item.get("URL", "")
                             or item.get("bulletinUrl", "")),
            "category": _safe_str(item.get("bulletinType", "")
                                  or item.get("reportType", "")),
        }
        results.append(ann)

    log.info(f"上交所公告搜索结果: {len(results)} 条")
    return results


def search_announcements(keyword: str,
                          market: str = "both",
                          max_results: int = 100) -> List[Dict[str, Any]]:
    """
    搜索沪深交易所公告（跨交易所合并结果）。

    作为巨潮资讯 (cninfo.com.cn) 的补充数据源，直接从交易所
    官方接口获取公告数据。

    Args:
        keyword: 搜索关键词（如 "分红"、"增发"、"重组" 等）
        market: 交易所选择，可选值:
            - "sh"   : 仅上交所
            - "sz"   : 仅深交所
            - "both" : 沪深两市（默认）
        max_results: 每个交易所最大返回条数（默认 100）

    Returns:
        公告列表，每项包含: market, title, stock_code, stock_name,
        publish_date, url, category
        失败返回空列表
    """
    results = []

    per_market_max = max_results if market != "both" else max_results // 2

    if market in ("sz", "both"):
        try:
            results.extend(_search_szse_announcements(keyword, per_market_max))
        except Exception as e:
            log.error(f"深交所公告搜索异常: {e}")

    if market in ("sh", "both"):
        try:
            results.extend(_search_sse_announcements(keyword, per_market_max))
        except Exception as e:
            log.error(f"上交所公告搜索异常: {e}")

    # 按发布日期降序排列
    results.sort(key=lambda x: x.get("publish_date", ""), reverse=True)

    log.info(f"公告搜索汇总: '{keyword}' 共 {len(results)} 条（market={market}）")
    return results


# ==================== 便捷查询 ====================


def get_recent_ipo_list(days: int = 30) -> List[Dict[str, Any]]:
    """
    获取最近 N 天内 IPO 的公司列表。

    Args:
        days: 最近天数（默认 30 天）

    Returns:
        近期 IPO 公司列表
    """
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    ipo_list = get_ipo_calendar(market="both")
    recent = []

    for ipo in ipo_list:
        date_str = ipo.get("ipo_date") or ipo.get("list_date", "")
        if date_str and date_str >= cutoff_str:
            recent.append(ipo)

    recent.sort(key=lambda x: x.get("ipo_date") or x.get("list_date", ""),
                reverse=True)
    log.info(f"近 {days} 天 IPO 公司: {len(recent)} 家")
    return recent


def find_company_announcements(stock_code: str,
                                keyword: str = "",
                                market: str = "both",
                                max_results: int = 30) -> List[Dict[str, Any]]:
    """
    查找指定公司的公告。
    将公司代码作为关键词的一部分进行搜索。

    Args:
        stock_code: 股票代码（如 "600519"）
        keyword: 额外搜索关键词（可选，如 "分红"）
        market: 交易所

    Returns:
        该公司相关公告列表
    """
    search_keyword = f"{stock_code} {keyword}".strip()
    return search_announcements(
        keyword=search_keyword,
        market=market,
        max_results=max_results,
    )


# ==================== 北交所（v4.7 新增） ====================

# 北交所官网接口
BSE_BASE = "https://www.bse.cn"
BSE_LISTED_COMPANIES_API = f"{BSE_BASE}/nqxxController/nqxxCnzq.do"
BSE_IPO_AUDIT_API = f"{BSE_BASE}/nqxxController/nqxxAuditList.do"

# 东方财富北交所板块（fs 参数），作为北交所数据的可靠降级源
EM_BSE_CLIST_API = "https://push2.eastmoney.com/api/qt/clist/get"


def _fetch_bse_native(params: Dict[str, Any], api_url: str) -> Optional[str]:
    """调用北交所官网 JSONP 接口，返回剥离回调后的原始文本。"""
    try:
        import urllib.parse
        body = urllib.parse.urlencode(params)
        rate_limit(url=BSE_BASE)
        full = f"{api_url}?{body}&callback=cb"
        resp = http_get(full, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            "Referer": f"{BSE_BASE}/nq/listedcompany.html",
        }, timeout=20)
        if resp is None:
            return None
        text = resp.text
        # 剥离 JSONP 回调: callback([...]) 或 null([...])
        m = re.search(r"\((.*)\)\s*;?\s*$", text, re.DOTALL)
        return m.group(1) if m else text
    except Exception as e:
        log.error(f"北交所原生接口请求失败: {e}")
        return None


def _fetch_em_bse_stocks(limit: int) -> List[Dict[str, Any]]:
    """通过东方财富 clist 接口获取北交所上市公司列表（降级源）。"""
    try:
        import urllib.parse
        params = {
            "pn": "1", "pz": str(min(limit, 200)), "po": "1", "np": "1",
            "fltt": "2", "invt": "2", "fid": "f26",
            "fs": "m:0+t:81+t:82+t:83",  # 北交所
            "fields": "f12,f14,f13,f26,f100,f2",
        }
        qs = urllib.parse.urlencode(params)
        rate_limit(url="push2.eastmoney.com")
        resp = http_get(f"{EM_BSE_CLIST_API}?{qs}", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0.0.0",
            "Referer": "https://quote.eastmoney.com/",
        }, timeout=20)
        if resp is None:
            return []
        data = json.loads(resp.text)
        items = data.get("data", {}).get("diff", []) if isinstance(data.get("data"), dict) else []
        results = []
        for it in items:
            results.append({
                "code": _safe_str(it.get("f12", "")),
                "name": _safe_str(it.get("f14", "")),
                "short_code": _safe_str(it.get("f13", "")),
                "listing_date": _safe_str(it.get("f26", "")),
                "industry": _safe_str(it.get("f100", "")),
                "market": "bj",
            })
        return results
    except Exception as e:
        log.error(f"东方财富北交所列表请求失败: {e}")
        return []


def get_bse_stocks(limit: int = 200) -> List[Dict[str, Any]]:
    """获取北交所上市公司列表。

    优先调用北交所官网接口，失败时降级到东方财富北交所板块数据。

    Args:
        limit: 返回条数，默认 200，最大 500

    Returns:
        [
            {"code": "837592", "name": "华信永道", "short_code": "837592",
             "listing_date": "2023-02-16", "industry": "信息技术", "market": "bj"}, ...
        ]
    """
    # 1) 北交所原生接口
    raw = _fetch_bse_native(
        {"page": 0, "typejb": "T", "xxfcbj": 2, "xxzqdm": "",
         "sortfield": "xxzqdm", "sorttype": "asc", "pagesize": min(limit, 100)},
        BSE_LISTED_COMPANIES_API,
    )
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data and isinstance(data[0], dict) and "msg" not in data[0]:
                results = []
                for it in data[:limit]:
                    results.append({
                        "code": _safe_str(it.get("xxzqdm", it.get("zqdm", ""))),
                        "name": _safe_str(it.get("jc", it.get("zqjc", ""))),
                        "short_code": _safe_str(it.get("zqdm", "")),
                        "listing_date": _safe_str(it.get("ssrq", "")),
                        "industry": _safe_str(it.get("hy", it.get("hymc", ""))),
                        "market": "bj",
                    })
                if results:
                    log.info(f"北交所原生接口获取 {len(results)} 条")
                    return results
        except Exception as e:
            log.warning(f"北交所原生接口解析失败，降级东方财富: {e}")

    # 2) 降级：东方财富北交所板块
    results = _fetch_em_bse_stocks(limit)
    log.info(f"北交所列表获取 {len(results)} 条（东方财富降级源）")
    return results


def get_bse_ipo(limit: int = 50) -> List[Dict[str, Any]]:
    """获取北交所 IPO 审核/发行信息。

    Args:
        limit: 返回条数，默认 50

    Returns:
        [
            {"code": "...", "name": "...", "status": "已注册",
             "audit_date": "2026-07-31", "market": "bj"}, ...
        ]
    """
    raw = _fetch_bse_native(
        {"page": 0, "xxfcbj": 2, "typejb": "T"},
        BSE_IPO_AUDIT_API,
    )
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data and isinstance(data[0], dict) and "msg" not in data[0]:
                results = []
                for it in data[:limit]:
                    results.append({
                        "code": _safe_str(it.get("xxzqdm", it.get("zqdm", ""))),
                        "name": _safe_str(it.get("jc", it.get("zqjc", ""))),
                        "status": _safe_str(it.get("zt", it.get("status", ""))),
                        "audit_date": _safe_str(it.get("sxrq", it.get("ssrq", ""))),
                        "market": "bj",
                    })
                if results:
                    log.info(f"北交所 IPO 审核获取 {len(results)} 条")
                    return results
        except Exception as e:
            log.warning(f"北交所 IPO 审核解析失败: {e}")

    # 降级：东方财富 IPO 日历（北交所部分由 get_ipo_calendar 覆盖）
    ipo = get_ipo_calendar(market="both")
    results = [i for i in ipo if str(i.get("stock_code", "")).startswith(("8", "4"))]
    log.info(f"北交所 IPO 获取 {len(results)} 条（降级源）")
    return results[:limit]


# ==================== 测试入口 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("沪深交易所数据爬虫 - 功能测试")
    print("=" * 60)

    # 测试1: 获取上市公司列表
    print("\n[测试1] 获取上交所上市公司列表（前10家）...")
    companies = get_listed_companies(market="sh")
    if companies:
        print(f"共获取 {len(companies)} 家上交所上市公司")
        for c in companies[:10]:
            print(f"  {c.get('market')} {c.get('stock_code')} {c.get('stock_name')} "
                  f"上市日:{c.get('list_date', 'N/A')}")
    else:
        print("获取失败（上交所接口可能需要特定 Referer）")

    # 测试2: 获取深交所上市公司列表
    print("\n[测试2] 获取深交所上市公司列表（前10家）...")
    sz_companies = get_listed_companies(market="sz")
    if sz_companies:
        print(f"共获取 {len(sz_companies)} 家深交所上市公司")
        for c in sz_companies[:10]:
            print(f"  {c.get('market')} {c.get('stock_code')} {c.get('stock_name')}")
    else:
        print("获取失败")

    # 测试3: 搜索公告
    print("\n[测试3] 搜索 '分红' 相关公告（深交所）...")
    anns = search_announcements(keyword="分红", market="sz", max_results=10)
    if anns:
        print(f"搜索到 {len(anns)} 条公告")
        for ann in anns[:5]:
            print(f"  [{ann.get('market')}] {ann.get('stock_code')} "
                  f"{ann.get('title', '')[:60]} "
                  f"日期:{ann.get('publish_date', '')}")
    else:
        print("搜索无结果或接口不可用")

    # 测试4: 搜索 '增发' 公告（上交所）
    print("\n[测试4] 搜索 '增发' 相关公告（上交所）...")
    anns_sse = search_announcements(keyword="增发", market="sh", max_results=10)
    if anns_sse:
        print(f"搜索到 {len(anns_sse)} 条公告")
        for ann in anns_sse[:5]:
            print(f"  [{ann.get('market')}] {ann.get('stock_code')} "
                  f"{ann.get('title', '')[:60]}")
    else:
        print("搜索无结果或接口不可用")

    # 测试5: 查找指定公司公告
    print("\n[测试5] 查找贵州茅台(600519)近期公告...")
    moutai_anns = find_company_announcements("600519", keyword="分红")
    if moutai_anns:
        for ann in moutai_anns[:5]:
            print(f"  [{ann.get('market')}] {ann.get('title', '')[:60]} "
                  f"日期:{ann.get('publish_date', '')}")
    else:
        print("未找到相关公告或接口不可用")

    print("\n" + "=" * 60)
    print("测试完成")
    print("提示: 交易所接口可能有反爬限制，如测试失败属正常现象。")
    print("      实际使用时建议在工作日盘后时段调用。")
