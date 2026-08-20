# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 公告层
=======================================

功能概览:
  - search_announcements: 沪深北公告全文检索
  - sec_filings: 美股 SEC Filing (10-K/10-Q/8-K)

数据源优先级与 Fallback 链:
  A股公告: 巨潮 cninfo → 东财 np-anotice → 深交所
  SEC Filing: SEC EDGAR submissions API

零外部依赖 — 仅使用 Python 标准库 + 项目内部模块。
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Optional

# 设置模块搜索路径
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get, http_post
from core.throttle import throttled_get
from core.ticker import normalize, cn_prefix

__all__ = [
    "search_announcements",
    "sec_filings",
]

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _strip_html(text: str) -> str:
    """移除 HTML 标签。"""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


# ---------------------------------------------------------------------------
# 巨潮公告相关常量
# ---------------------------------------------------------------------------

_CNINFO_ANN_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

# 公告分类映射（中文 → 巨潮分类ID）
_CNINFO_CATEGORY_MAP = {
    "年报": "category_ndbg_szsh",
    "半年报": "category_bndbg_szsh",
    "一季报": "category_yjdbg_szsh",
    "三季报": "category_sjdbg_szsh",
    "业绩预告": "category_yjyg_szsh",
    "业绩快报": "category_yjkb_szsh",
    "分红": "category_fhsg_szsh",
    "增减持": "category_zjc_szsh",
    "股权质押": "category_gqzr_szsh",
    "定增": "category_zf_szsh",
    "回购": "category_hg_szsh",
    "关联交易": "category_gljy_szsh",
    "资产重组": "category_zczg_szsh",
    "股东大会": "category_gddh_szsh",
    "董事会决议": "category_dshgg_szsh",
    "IPO": "category_sf_szsh",
}

# 东财公告接口
_EASTMONEY_ANN_URL = "https://np-anotice-stock.eastmoney.com/api/security/ann"

# 深交所公告接口
_SZSE_ANN_URL = "https://www.szse.cn/api/disc/announcement/annList"


# ===========================================================================
# 公开 API
# ===========================================================================


def search_announcements(
    code: str,
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    category: str = None,
) -> list[dict]:
    """沪深北公告全文检索

    搜索指定上市公司的历史公告，支持关键词、时间范围和分类过滤。
    内置三级 fallback 确保数据可用性。

    Fallback 链:
        1. 巨潮资讯 cninfo.com.cn（优先，覆盖最全）
        2. 东财 np-anotice-stock（降级）
        3. 深交所官方（仅深市股票）

    Args:
        code: 股票代码（6位数字），如 "600519"
        keyword: 搜索关键词，如 "分红"、"回购"、"业绩"。
                 None 表示不限关键词。
        start_date: 起始日期，格式 "YYYY-MM-DD"。
                    None 表示不限起始时间。
        end_date: 截止日期，格式 "YYYY-MM-DD"。
                  None 表示不限截止时间。
        category: 公告分类，可选:
            年报, 半年报, 一季报, 三季报, 业绩预告, 业绩快报,
            分红, 增减持, 股权质押, 定增, 回购, 关联交易,
            资产重组, 股东大会, 董事会决议, IPO
            None 表示全部分类。

    Returns:
        公告列表，每项包含:
        - title: 公告标题（已去除高亮标签）
        - url: 公告PDF/原文链接
        - publish_date: 发布日期（YYYY-MM-DD）
        - category: 公告分类
        - code: 证券代码
        - company: 公司简称
        - summary: 摘要（如有）
        - source: 数据来源标识

    示例:
        >>> search_announcements("600519", keyword="分红", category="分红")
        [{title: "贵州茅台关于2023年年度利润分配方案的公告", url: "...", ...}]
        >>> search_announcements("000001", start_date="2024-01-01", end_date="2024-03-31")
    """
    normalized = normalize(code)

    # ─── 主源: 巨潮 cninfo ───
    results = _announcements_cninfo(normalized, keyword, start_date, end_date, category)
    if results:
        return results

    # ─── Fallback 1: 东财 ───
    results = _announcements_eastmoney(normalized, keyword)
    if results:
        return results

    # ─── Fallback 2: 深交所（仅深市） ───
    prefix = cn_prefix(normalized)
    if prefix == "sz":
        return _announcements_szse(normalized)

    return []


def _announcements_cninfo(
    code: str,
    keyword: str = None,
    start_date: str = None,
    end_date: str = None,
    category: str = None,
) -> list[dict]:
    """巨潮资讯公告查询（主源）。"""
    # 判断板块
    prefix = cn_prefix(code)
    if prefix == "sh":
        stock_param = f"{code},gssh{code}"
        column = "sse"
    elif prefix == "sz":
        stock_param = f"{code},gssz{code}"
        column = "szse"
    else:
        stock_param = code
        column = "szse"

    # 构建 POST 请求体
    payload = {
        "stock": stock_param,
        "tabName": "fulltext",
        "pageSize": 30,
        "pageNum": 1,
        "column": column,
        "isHLtitle": "true",
    }

    if keyword:
        payload["searchkey"] = keyword

    # 时间范围
    if start_date or end_date:
        se_start = start_date or ""
        se_end = end_date or ""
        payload["seDate"] = f"{se_start}~{se_end}"

    # 分类过滤
    if category and category in _CNINFO_CATEGORY_MAP:
        payload["category"] = _CNINFO_CATEGORY_MAP[category]

    _CNINFO_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Referer": "http://www.cninfo.com.cn/new/disclosure",
        "Origin": "http://www.cninfo.com.cn",
        "Accept": "application/json",
    }

    resp = http_post(_CNINFO_ANN_URL, data=payload, headers=_CNINFO_HEADERS)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    announcements_list = data.get("announcements", [])
    if not isinstance(announcements_list, list) or not announcements_list:
        return []

    results = []
    for ann in announcements_list:
        # 处理标题(去除高亮标签)
        title = _strip_html(ann.get("announcementTitle", ""))

        # 构建PDF链接
        pdf_url = ""
        adj_url = ann.get("adjunctUrl", "")
        if adj_url:
            pdf_url = f"http://static.cninfo.com.cn/{adj_url}"

        # 日期处理（巨潮返回时间戳或字符串）
        date_raw = ann.get("announcementTime", "")
        pub_date = ""
        if isinstance(date_raw, (int, float)) and date_raw > 0:
            try:
                from datetime import datetime
                pub_date = datetime.fromtimestamp(date_raw / 1000).strftime("%Y-%m-%d")
            except (ValueError, OSError):
                pub_date = str(date_raw)
        elif isinstance(date_raw, str):
            pub_date = date_raw[:10]

        results.append({
            "title": title,
            "url": pdf_url,
            "publish_date": pub_date,
            "category": ann.get("announcementTypeName", ""),
            "code": ann.get("secCode", code),
            "company": ann.get("secName", ""),
            "summary": _strip_html(ann.get("adjunctContent", ""))[:200],
            "source": "cninfo",
        })

    return results


def _announcements_eastmoney(code: str, keyword: str = None) -> list[dict]:
    """东财公告接口（Fallback 1）。"""
    params = {
        "sr": "-1",
        "page_size": "30",
        "page_index": "1",
        "ann_type": "A",
        "stock_list": code,
        "f_node": "0",
        "s_node": "0",
    }
    if keyword:
        params["searchkey"] = keyword

    resp = throttled_get(_EASTMONEY_ANN_URL, params=params)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    items = data.get("data", {}).get("list", [])
    if not isinstance(items, list) or not items:
        return []

    results = []
    for item in items:
        # 东财公告的标题与URL
        title = _strip_html(item.get("title", item.get("ann_title", "")))
        art_code = item.get("art_code", "")
        url = ""
        if art_code:
            url = f"https://data.eastmoney.com/notices/detail/{code}/{art_code}.html"

        results.append({
            "title": title,
            "url": url,
            "publish_date": item.get("display_time", item.get("notice_date", ""))[:10],
            "category": item.get("columns", [{}])[0].get("column_name", "") if item.get("columns") else "",
            "code": code,
            "company": item.get("codes", [{}])[0].get("short_name", "") if item.get("codes") else "",
            "summary": _strip_html(item.get("content", ""))[:200],
            "source": "eastmoney",
        })

    return results


def _announcements_szse(code: str) -> list[dict]:
    """深交所公告查询（Fallback 2，仅深市）。"""
    _SZSE_HEADERS = {
        "Referer": "https://www.szse.cn/",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
    }

    payload = json.dumps({
        "seDate": ["", ""],
        "stock": [code],
        "channelCode": ["listedNotice_disc"],
        "pageSize": 30,
        "pageNum": 1,
    })

    resp = http_post(
        _SZSE_ANN_URL,
        data=payload,
        headers=_SZSE_HEADERS,
    )
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    items = data.get("data", [])
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        attach_path = item.get("attachPath", "")
        url = f"https://disc.szse.cn/download/{attach_path}" if attach_path else ""

        pub_time = item.get("announcementTime", item.get("publishTime", ""))
        if isinstance(pub_time, (int, float)):
            try:
                from datetime import datetime
                pub_time = datetime.fromtimestamp(pub_time / 1000).strftime("%Y-%m-%d")
            except (ValueError, OSError):
                pub_time = str(pub_time)

        results.append({
            "title": item.get("title", ""),
            "url": url,
            "publish_date": str(pub_time)[:10],
            "category": item.get("bigCategoryName", ""),
            "code": code,
            "company": item.get("secName", ""),
            "summary": "",
            "source": "szse",
        })

    return results


# ===========================================================================
# SEC Filing
# ===========================================================================

# SEC 要求所有自动化请求携带规范 User-Agent
_SEC_HEADERS = {
    "User-Agent": "DataSupplement/7.1 (contact@dataSupplement.local)",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "application/json",
}

_SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
_SEC_TICKER_URL = "https://www.sec.gov/cgi-bin/browse-edgar"

# CIK 缓存
_cik_cache: dict[str, str] = {}


def _ticker_to_cik(ticker: str) -> str:
    """将美股代码转换为 SEC CIK 编号（10位零填充）。

    通过 SEC EDGAR 的 browse-edgar 接口查询 ticker 对应的 CIK。
    结果缓存于内存中避免重复请求。
    """
    ticker_upper = ticker.upper().strip()
    if ticker_upper in _cik_cache:
        return _cik_cache[ticker_upper]

    # 方案1: 通过 tickers.json 映射文件
    tickers_url = "https://www.sec.gov/files/company_tickers.json"
    resp = http_get(tickers_url, headers=_SEC_HEADERS)
    if resp and resp.ok:
        try:
            data = resp.json()
            for key, entry in data.items():
                if entry.get("ticker", "").upper() == ticker_upper:
                    cik = str(entry.get("cik_str", "")).zfill(10)
                    _cik_cache[ticker_upper] = cik
                    return cik
        except (ValueError, AttributeError, KeyError):
            pass

    # 方案2: 通过 browse-edgar
    params = {
        "action": "getcompany",
        "company": ticker_upper,
        "CIK": ticker_upper,
        "type": "10-K",
        "dateb": "",
        "owner": "include",
        "count": "1",
        "search_text": "",
        "output": "atom",
    }
    resp = http_get(_SEC_TICKER_URL, params=params, headers=_SEC_HEADERS)
    if not resp or not resp.ok:
        return ""

    try:
        text = resp.text
        cik_match = re.search(r"CIK=(\d{10})", text, re.IGNORECASE)
        if not cik_match:
            cik_match = re.search(r"cik=(\d+)", text, re.IGNORECASE)
        if not cik_match:
            return ""
        cik = cik_match.group(1).zfill(10)
        _cik_cache[ticker_upper] = cik
        return cik
    except (AttributeError, IndexError):
        return ""


def sec_filings(
    ticker: str,
    form_type: str = None,
    count: int = 10,
) -> list[dict]:
    """美股 SEC Filing (10-K/10-Q/8-K)

    查询指定美股公司在 SEC EDGAR 系统中的文件提交记录，
    支持按文件类型过滤（年报、季报、临时报告等）。

    Source: SEC EDGAR (data.sec.gov)

    Args:
        ticker: 美股代码，如 "AAPL"、"TSLA"、"MSFT"
        form_type: 文件类型筛选，可选:
            - "10-K": 年度报告
            - "10-Q": 季度报告
            - "8-K": 临时报告（重大事件）
            - "DEF 14A": 代理声明
            - "S-1": IPO 注册声明
            - None: 全部类型（默认）
        count: 返回条数，默认 10，最大 40

    Returns:
        Filing 列表，每项包含:
        - form_type: 文件类型（如 "10-K"）
        - filing_date: 提交日期（YYYY-MM-DD）
        - url: 文件原文链接（SEC EDGAR）
        - description: 文件描述
        - accession_number: SEC 存档编号
        - primary_document: 主文件名

    示例:
        >>> sec_filings("AAPL", form_type="10-K", count=5)
        [{form_type: "10-K", filing_date: "2024-11-01", url: "...", ...}]
        >>> sec_filings("TSLA", form_type="8-K")
    """
    count = min(count, 40)
    cik = _ticker_to_cik(ticker)
    if not cik:
        return []

    url = _SEC_SUBMISSIONS_URL.format(cik=cik)
    resp = http_get(url, headers=_SEC_HEADERS)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    # 提取最近提交记录
    recent = data.get("filings", {}).get("recent", {})
    if not recent:
        return []

    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    documents = recent.get("primaryDocument", [])
    accessions = recent.get("accessionNumber", [])
    descriptions = recent.get("primaryDocDescription", [])

    results = []
    total = min(len(forms), len(dates))

    for i in range(total):
        form = forms[i] if i < len(forms) else ""

        # 按 form_type 过滤
        if form_type and form != form_type:
            continue

        accession = accessions[i] if i < len(accessions) else ""
        document = documents[i] if i < len(documents) else ""

        # 构建 SEC 文件 URL
        filing_url = ""
        if accession and document:
            acc_no_dash = accession.replace("-", "")
            filing_url = (
                f"https://www.sec.gov/Archives/edgar/data/"
                f"{cik.lstrip('0')}/{acc_no_dash}/{document}"
            )

        results.append({
            "form_type": form,
            "filing_date": dates[i] if i < len(dates) else "",
            "url": filing_url,
            "description": descriptions[i] if i < len(descriptions) else "",
            "accession_number": accession,
            "primary_document": document,
        })

        if len(results) >= count:
            break

    return results
