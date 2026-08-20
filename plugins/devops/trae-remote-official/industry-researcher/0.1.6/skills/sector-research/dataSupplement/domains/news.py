# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 新闻层
=======================================

功能概览:
  - stock_news: 个股相关新闻
  - market_flash: 7x24 市场快讯
  - global_news: 全球财经资讯
  - us_stock_news: 美股个股新闻

数据源优先级与 Fallback 链:
  个股新闻: 东财 search-api-web (JSONP)
  市场快讯: 财联社 cls.cn → 东财 np-weblist
  全球资讯: 东财 np-weblist-emt
  美股新闻: Yahoo Finance news

零外部依赖 — 仅使用 Python 标准库 + 项目内部模块。
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime as _datetime
from typing import Optional

# 设置模块搜索路径
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get
from core.throttle import throttled_get
from core.ticker import normalize, to_yahoo_symbol

__all__ = [
    "stock_news",
    "market_flash",
    "global_news",
    "us_stock_news",
]

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


def _strip_html(text: str) -> str:
    """移除 HTML 标签。"""
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text)


def _ts_to_str(ts) -> str:
    """Unix 时间戳转为格式化时间字符串。"""
    if not ts:
        return ""
    try:
        return _datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, OSError, TypeError):
        return str(ts)


# ===========================================================================
# 公开 API
# ===========================================================================


def stock_news(code: str, count: int = 20) -> list[dict]:
    """个股新闻

    通过东财搜索接口（JSONP 格式）获取指定股票的相关新闻资讯。
    接口返回 JSONP 格式需手动剥离回调函数包装后解析 JSON。

    Source: 东财 search-api-web.eastmoney.com (JSONP)

    Args:
        code: 股票代码（6位数字），如 "600519"
        count: 获取条数，默认 20，最大 50

    Returns:
        新闻列表，每项包含:
        - title: 新闻标题（已去除 HTML 高亮标签）
        - url: 新闻原文链接
        - source: 来源媒体名称
        - publish_time: 发布时间（YYYY-MM-DD HH:MM:SS）
        - summary: 摘要（如有）

    示例:
        >>> stock_news("600519", count=5)
        [{title: "贵州茅台2024年报发布...", url: "...", source: "证券时报", ...}]
    """
    normalized = normalize(code)
    count = min(count, 50)

    # 构建 JSONP 请求
    _SEARCH_API = "https://search-api-web.eastmoney.com/search/jsonp"

    search_param = json.dumps({
        "uid": "",
        "keyword": normalized,
        "type": ["cmsArticleWebOld"],
        "client": "web",
        "clientType": "web",
        "clientVersion": "curr",
        "param": {
            "cmsArticleWebOld": {
                "searchScope": "default",
                "sort": "default",
                "pageIndex": 1,
                "pageSize": count,
                "preTag": "<em>",
                "postTag": "</em>",
            }
        },
    }, ensure_ascii=False)

    params = {
        "cb": "jQuery_fin_data_cb",
        "param": search_param,
    }

    resp = throttled_get(_SEARCH_API, params=params)
    if not resp or not resp.ok:
        return []

    # 剥离 JSONP 包装: jQuery_fin_data_cb({...})
    try:
        text = resp.text
        start = text.index("(") + 1
        end = text.rindex(")")
        data = json.loads(text[start:end])
    except (ValueError, IndexError):
        return []

    # 解析新闻列表
    result = data.get("result", {})
    cms_data = result.get("cmsArticleWebOld", [])
    # cmsArticleWebOld 可能是 list(文章列表) 或 dict(含 list 字段)
    if isinstance(cms_data, dict):
        articles = cms_data.get("list", [])
    elif isinstance(cms_data, list):
        articles = cms_data
    else:
        articles = []

    results = []
    for item in articles:
        title = _strip_html(item.get("title", ""))
        results.append({
            "title": title,
            "url": item.get("url", ""),
            "source": item.get("mediaName", item.get("source", "")),
            "publish_time": item.get("date", item.get("publishDate", "")),
            "summary": _strip_html(item.get("content", ""))[:200],
        })

    return results


def market_flash(count: int = 50, category: str = None) -> list[dict]:
    """7x24 市场快讯

    获取实时财经快讯流，包含重要性级别、关联股票等信息。
    优先使用财联社数据源（更快更全），财联社不可用时降级到东财。

    Fallback 链:
        1. 财联社 cls.cn roll_list（优先）
        2. 东财 np-weblist（降级）

    Args:
        count: 获取条数，默认 50，最大 100
        category: 分类筛选，可选:
            - None: 全部快讯（默认）
            - "重要": 仅重要快讯
            - "A股": A股相关
            - "美股": 美股相关
            - "港股": 港股相关
            - "外汇": 外汇相关
            - "商品": 大宗商品
            - "宏观": 宏观经济
            - "公司": 公司动态
            - "科技": 科技资讯

    Returns:
        快讯列表，每项包含:
        - title: 标题（如有）
        - content: 快讯正文
        - time: 发布时间（YYYY-MM-DD HH:MM:SS）
        - importance: 重要性级别（0=普通, 1=重要, 2=非常重要）
        - tags: 关联标签列表
        - stocks: 关联股票代码列表
        - source: 数据来源标识

    示例:
        >>> market_flash(count=10, category="重要")
        [{title: "", content: "央行今日开展...", time: "...", importance: 2, ...}]
    """
    count = min(count, 100)

    # ─── 主源: 财联社 ───
    results = _market_flash_cls(count, category)
    if results:
        return results

    # ─── Fallback: 东财 ───
    return _market_flash_eastmoney(count)


def _market_flash_cls(count: int, category: str = None) -> list[dict]:
    """财联社 7x24 快讯。"""
    # 分类映射
    _CLS_CATEGORY_MAP = {
        "重要": "1",
        "A股": "5",
        "美股": "6",
        "港股": "7",
        "外汇": "8",
        "商品": "9",
        "宏观": "10",
        "公司": "11",
        "科技": "12",
    }

    now_ts = str(int(time.time()))
    params = {
        "app": "CailianpressWeb",
        "os": "web",
        "sv": "8.4.6",
        "rn": str(count),
        "last_time": now_ts,
    }

    if category and category in _CLS_CATEGORY_MAP:
        cat_id = _CLS_CATEGORY_MAP[category]
        if cat_id:
            params["category"] = cat_id

    # 计算签名: SHA1(sorted_params) → MD5
    sorted_keys = sorted(params.keys())
    query_parts = [f"{k}={params[k]}" for k in sorted_keys if params[k]]
    query_string = "&".join(query_parts)
    sha1_hash = hashlib.sha1(query_string.encode("utf-8")).hexdigest()
    sign = hashlib.md5(sha1_hash.encode("utf-8")).hexdigest()
    params["sign"] = sign

    url = "https://www.cls.cn/v1/roll/get_roll_list"
    resp = throttled_get(url, params=params)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    roll_data = data.get("data", {})
    roll_list = roll_data.get("roll_data", roll_data.get("roll_list", roll_data.get("data", [])))
    if not isinstance(roll_list, list):
        return []

    results = []
    for item in roll_list:
        # 提取关联股票
        stocks = []
        stock_list = item.get("stocks", item.get("associated_stocks", []))
        if isinstance(stock_list, list):
            for s in stock_list:
                if isinstance(s, dict):
                    stocks.append(s.get("code", s.get("symbol", "")))
                elif isinstance(s, str):
                    stocks.append(s)

        # 提取标签
        tags = []
        tag_list = item.get("tags", item.get("subjects", []))
        if isinstance(tag_list, list):
            for t in tag_list:
                if isinstance(t, dict):
                    tags.append(t.get("name", t.get("subject_name", "")))
                elif isinstance(t, str):
                    tags.append(t)

        # 时间处理
        ctime = item.get("ctime", item.get("time", 0))
        dt_str = _ts_to_str(ctime)

        results.append({
            "title": item.get("title", ""),
            "content": item.get("content", item.get("brief", "")),
            "time": dt_str,
            "importance": item.get("level", item.get("importance", 0)),
            "tags": tags,
            "stocks": stocks,
            "source": "cls",
        })

    return results


def _market_flash_eastmoney(count: int) -> list[dict]:
    """东财快讯（降级源）。"""
    url = "https://np-weblist-emt.eastmoney.com/np/weblist/article"
    params = {
        "fields": "title,content,showTime,url",
        "client": "wap",
        "article_type": "1",
        "pageSize": str(count),
        "pageNo": "1",
    }

    resp = throttled_get(url, params=params)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    items = data.get("data", {}).get("list", [])
    if not isinstance(items, list):
        return []

    results = []
    for item in items:
        results.append({
            "title": item.get("title", ""),
            "content": item.get("content", item.get("digest", "")),
            "time": item.get("showTime", item.get("display_time", "")),
            "importance": 0,
            "tags": [],
            "stocks": [],
            "source": "eastmoney",
        })

    return results


def global_news(count: int = 30) -> list[dict]:
    """全球财经资讯

    获取东方财富全球财经新闻列表，涵盖海外市场动态、宏观政策、
    央行决议等国际财经要闻。

    Source: 东财 np-weblist-emt.eastmoney.com

    Args:
        count: 获取条数，默认 30，最大 100

    Returns:
        全球资讯列表，每项包含:
        - title: 新闻标题
        - content: 内容摘要
        - time: 发布时间
        - url: 原文链接
        - category: 分类标签

    示例:
        >>> global_news(count=10)
        [{title: "美联储维持利率不变...", content: "...", time: "...", ...}]
    """
    count = min(count, 100)

    # 东财 7x24 全球财经快讯(栏目 102)。
    # 旧接口 np-weblist-emt.eastmoney.com 已改版返回 HTML，改用 newsapi kuaixun。
    # 返回 JSONP 包裹: var ajaxResult={...};
    page_size = min(max(count, 20), 100)
    url = (
        f"https://newsapi.eastmoney.com/kuaixun/v1/"
        f"getlist_102_ajaxResult_{page_size}_1_.html"
    )
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.eastmoney.com/",
    }

    resp = throttled_get(url, headers=headers)
    if not resp or not resp.ok:
        return []

    text = resp.text or ""
    match = re.search(r"var\s+ajaxResult\s*=\s*(\{.*\})\s*;?\s*$", text.strip(), re.S)
    if not match:
        match = re.search(r"=\s*(\{.*\})", text.strip(), re.S)
    if not match:
        return []

    try:
        data = json.loads(match.group(1))
    except (ValueError, TypeError):
        return []

    items = data.get("LivesList", [])
    if not isinstance(items, list):
        return []

    results = []
    for item in items[:count]:
        results.append({
            "title": item.get("title", ""),
            "content": _strip_html(item.get("digest", ""))[:300],
            "time": item.get("showtime", item.get("ordertime", "")),
            "url": item.get("url_unique", item.get("url_w", "")),
            "category": item.get("simtype_zh", item.get("topic", "")),
        })

    return results


def us_stock_news(symbol: str) -> list[dict]:
    """美股个股新闻

    通过 Yahoo Finance 获取指定美股的相关新闻，包含分析师评级变动等信息。
    自动处理 Yahoo Finance 的 crumb 鉴权机制。

    Source: Yahoo Finance news / quoteSummary

    Args:
        symbol: 美股代码，如 "AAPL"、"TSLA"、"MSFT"。
                支持原始格式输入，内部自动转换。

    Returns:
        新闻列表，每项包含:
        - title: 新闻标题
        - url: 原文链接
        - source: 来源
        - publish_time: 发布时间
        - related_tickers: 关联股票代码列表
        - thumbnail: 缩略图URL（如有）

    示例:
        >>> us_stock_news("AAPL")
        [{title: "Apple announces new...", url: "...", source: "Reuters", ...}]
    """
    yahoo_symbol = to_yahoo_symbol(symbol)

    # Yahoo Finance 新闻搜索端点
    _NEWS_URL = f"https://query1.finance.yahoo.com/v1/finance/search"
    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    params = {
        "q": yahoo_symbol,
        "quotesCount": "0",
        "newsCount": "20",
        "listsCount": "0",
        "enableFuzzyQuery": "false",
        "quotesQueryId": "tss_match_phrase_query",
        "newsQueryId": "news_cie_vespa",
        "enableCb": "false",
        "enableNavLinks": "false",
        "enableEnhancedTrivialQuery": "true",
    }

    resp = http_get(_NEWS_URL, params=params, headers=_HEADERS)
    if not resp or not resp.ok:
        # 降级: 尝试通过 quoteSummary 获取评级信息作为替代
        return _us_news_fallback(yahoo_symbol, _HEADERS)

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return _us_news_fallback(yahoo_symbol, _HEADERS)

    news_items = data.get("news", [])
    if not isinstance(news_items, list) or not news_items:
        return _us_news_fallback(yahoo_symbol, _HEADERS)

    results = []
    for item in news_items:
        # 提取关联代码
        related = []
        tickers_raw = item.get("relatedTickers", [])
        if isinstance(tickers_raw, list):
            related = [t for t in tickers_raw if isinstance(t, str)]

        # 缩略图
        thumbnail = ""
        thumb_data = item.get("thumbnail", {})
        if isinstance(thumb_data, dict):
            resolutions = thumb_data.get("resolutions", [])
            if resolutions and isinstance(resolutions, list):
                thumbnail = resolutions[0].get("url", "")

        pub_time = ""
        pub_ts = item.get("providerPublishTime")
        if pub_ts:
            pub_time = _ts_to_str(pub_ts)

        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", item.get("url", "")),
            "source": item.get("publisher", ""),
            "publish_time": pub_time,
            "related_tickers": related,
            "thumbnail": thumbnail,
        })

    return results


def _us_news_fallback(symbol: str, headers: dict) -> list[dict]:
    """美股新闻降级: 通过 quoteSummary 获取评级变动信息。"""
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "upgradeDowngradeHistory"}

    resp = http_get(url, params=params, headers=headers)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    result = data.get("quoteSummary", {}).get("result", [])
    if not result:
        return []

    summary = result[0]
    history = summary.get("upgradeDowngradeHistory", {}).get("history", [])

    results = []
    for item in history[:20]:
        epoch = item.get("epochGradeDate", 0)
        pub_time = _ts_to_str(epoch) if epoch else ""

        action = item.get("action", "")
        from_grade = item.get("fromGrade", "")
        to_grade = item.get("toGrade", "")
        firm = item.get("firm", "")

        title = f"{firm}: {action} {symbol}"
        if from_grade and to_grade:
            title += f" ({from_grade} → {to_grade})"

        results.append({
            "title": title,
            "url": "",
            "source": firm,
            "publish_time": pub_time,
            "related_tickers": [symbol],
            "thumbnail": "",
        })

    return results
