"""交易所官方数据源模块

提供上交所（SSE）和深交所（SZSE）的龙虎榜、公告等官方数据接口。
需要伪装 Referer 等请求头以通过交易所反爬策略。
"""

from core.client import http_get, http_post
import random

# ─── 上交所 ──────────────────────────────────────────────────
_SSE_DRAGON_URL = "https://query.sse.com.cn/infodisplay/querySpecialTips.do"
_SSE_HEADERS = {
    "Referer": "https://www.sse.com.cn",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

# ─── 深交所 ──────────────────────────────────────────────────
_SZSE_DRAGON_URL = "https://www.szse.cn/api/report/ShowReport/data"
_SZSE_ANN_URL = "https://www.szse.cn/api/disc/announcement/annList"
_SZSE_HEADERS = {
    "Referer": "https://www.szse.cn/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}


def sse_dragon_tiger(date: str) -> list:
    """上交所龙虎榜数据。

    通过 query.sse.com.cn 的 querySpecialTips 接口获取指定日期龙虎榜。
    必须携带 Referer: www.sse.com.cn 请求头。

    Args:
        date: 交易日期，格式 'YYYY-MM-DD'

    Returns:
        龙虎榜记录列表
    """
    params = {
        "isPagination": "true",
        "pageHelp.pageSize": "100",
        "pageHelp.pageNo": "1",
        "pageHelp.beginPage": "1",
        "pageHelp.cacheSize": "1",
        "type": "inParams",
        "reportDate": date,
    }
    resp = http_get(_SSE_DRAGON_URL, params=params, headers=_SSE_HEADERS)
    if resp is None:
        return []
    try:
        data = resp.json()
        page_help = data.get("pageHelp", {})
        records = page_help.get("data", [])
        return records if isinstance(records, list) else []
    except (ValueError, AttributeError, KeyError):
        return []


def szse_dragon_tiger(date: str) -> list:
    """深交所龙虎榜数据。

    通过深交所 ShowReport/data 接口获取指定日期龙虎榜。

    Args:
        date: 交易日期，格式 'YYYY-MM-DD'

    Returns:
        龙虎榜记录列表
    """
    params = {
        "SHOWTYPE": "JSON",
        "CATALOGID": "1815_stock",
        "TABKEY": "tab1",
        "txtDate": date,
        "random": str(random.random()),
    }
    resp = http_get(_SZSE_DRAGON_URL, params=params, headers=_SZSE_HEADERS)
    if resp is None:
        return []
    try:
        data = resp.json()
        # 深交所返回数组结构，第一个元素为龙虎榜主表
        if isinstance(data, list) and len(data) > 0:
            records = data[0].get("data", [])
            return records if isinstance(records, list) else []
        return []
    except (ValueError, AttributeError, KeyError, IndexError):
        return []


def szse_announcements(code: str) -> list:
    """深交所公告查询。

    通过深交所 annList 接口按证券代码查询公告。

    Args:
        code: 股票代码，如 '000001'

    Returns:
        公告列表，每条含 title / announcementTime / url 等
    """
    payload = {
        "seDate": ["", ""],
        "stock": [code],
        "channelCode": ["listedNotice_disc"],
        "pageSize": 30,
        "pageNum": 1,
    }
    # 深交所此接口需 POST JSON
    headers = {
        **_SZSE_HEADERS,
        "Content-Type": "application/json",
    }
    resp = http_post(
        _SZSE_ANN_URL,
        json_data=payload,
        headers=headers,
    )
    if resp is None:
        return []
    try:
        data = resp.json()
        items = data.get("data", [])
        return [
            {
                "title": item.get("title", ""),
                "announcementTime": item.get("announcementTime", ""),
                "url": (
                    f"https://disc.szse.cn/download"
                    f"/{item.get('attachPath', '')}"
                    if item.get("attachPath")
                    else ""
                ),
            }
            for item in items
        ] if isinstance(items, list) else []
    except (ValueError, AttributeError, KeyError):
        return []
