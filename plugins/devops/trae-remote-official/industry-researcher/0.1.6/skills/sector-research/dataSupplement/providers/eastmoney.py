"""东方财富数据源模块

覆盖 datacenter 通用查询、龙虎榜、解禁、融资融券、大宗交易、
股东户数、分红、新闻、人气榜、概念热度、搜索、研报、公告等接口。
所有请求经 throttled_get 限流（最小间隔 1.2s）。
"""

from core.throttle import throttled_get
from core.client import http_post

# ─── 基础 URL ───────────────────────────────────────────────
_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_SEARCH_API = "https://search-api-web.eastmoney.com/search/jsonp"
_NEWS_LIST_API = "https://np-weblist-emt.eastmoney.com/np/weblist/article"
_POPULARITY_API = "https://emappdata.eastmoney.com/stockrank/getAllCurrentList"
_CONCEPT_HITS_API = "https://emappdata.eastmoney.com/stockrank/getHotStockRank"
_STOCK_SEARCH_API = "https://searchapi.eastmoney.com/api/suggest/get"
_REPORT_API = "https://reportapi.eastmoney.com/report/list"
_ANNOUNCE_API = "https://np-anotice-stock.eastmoney.com/api/security/ann"


def _parse_datacenter(resp: dict) -> list:
    """统一解析 datacenter 返回结构，提取数据列表。"""
    if not resp or not isinstance(resp, dict):
        return []
    result = resp.get("result", {})
    if result is None:
        return []
    data = result.get("data", [])
    return data if isinstance(data, list) else []


def datacenter_query(report_name: str, filters: str = None,
                     columns: str = None, sort: str = None,
                     page: int = 1, size: int = 50) -> list:
    """通用 datacenter-web 查询包装器。

    Args:
        report_name: 报表标识，如 RPT_DAILYBILLBOARD_DETAILS
        filters: 筛选条件表达式
        columns: 返回字段列表
        sort: 排序字段与方向
        page: 页码，从 1 开始
        size: 每页条数，默认 50

    Returns:
        解析后的数据记录列表
    """
    params = {
        "sortColumns": sort or "",
        "sortTypes": "-1",
        "pageSize": str(size),
        "pageNumber": str(page),
        "reportName": report_name,
        "columns": columns or "ALL",
        "source": "WEB",
        "client": "WEB",
    }
    if filters:
        params["filter"] = filters

    resp = throttled_get(_DATACENTER_URL, params=params)
    if resp is None:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []
    return _parse_datacenter(data)


def dragon_tiger(code: str = None, date: str = None) -> list:
    """龙虎榜明细查询。

    Args:
        code: 股票代码，如 '600519'，可选
        date: 交易日期 'YYYY-MM-DD'，可选

    Returns:
        龙虎榜记录列表
    """
    filters_parts = []
    if code:
        filters_parts.append(f'(SECURITY_CODE="{code}")')
    if date:
        filters_parts.append(f'(TRADE_DATE=\'{date}\')')
    filters = " AND ".join(filters_parts) if filters_parts else None
    return datacenter_query(
        report_name="RPT_DAILYBILLBOARD_DETAILS",
        filters=filters,
        sort="TRADE_DATE",
    )


def lockup_schedule(code: str = None, date: str = None) -> list:
    """限售解禁计划查询。

    Args:
        code: 股票代码，可选
        date: 解禁日期 'YYYY-MM-DD'，可选

    Returns:
        解禁记录列表
    """
    filters_parts = []
    if code:
        filters_parts.append(f'(SECURITY_CODE="{code}")')
    if date:
        filters_parts.append(f'(FREE_DATE=\'{date}\')')
    filters = " AND ".join(filters_parts) if filters_parts else None
    return datacenter_query(
        report_name="RPT_LIFT_STAGE",
        filters=filters,
        sort="FREE_DATE",
    )


def margin_detail(code: str) -> list:
    """融资融券个股明细。

    Args:
        code: 股票代码

    Returns:
        融资融券数据列表
    """
    filters = f'(SCODE="{code}")'
    return datacenter_query(
        report_name="RPTA_WEB_RZRQ_GGMX",
        filters=filters,
        sort="DATE",
    )


def block_trades(code: str) -> list:
    """大宗交易明细。

    Args:
        code: 股票代码

    Returns:
        大宗交易记录列表
    """
    filters = f'(SECURITY_CODE="{code}")'
    return datacenter_query(
        report_name="RPT_BLOCKTRADE_DETAILS",
        filters=filters,
        sort="TRADE_DATE",
    )


def holder_count(code: str) -> list:
    """股东户数最新数据。

    Args:
        code: 股票代码

    Returns:
        股东户数记录列表
    """
    filters = f'(SECURITY_CODE="{code}")'
    return datacenter_query(
        report_name="RPT_HOLDERNUMLATEST",
        filters=filters,
        sort="END_DATE",
    )


def dividend_history(code: str) -> list:
    """分红送转历史。

    Args:
        code: 股票代码

    Returns:
        分红记录列表
    """
    filters = f'(SECURITY_CODE="{code}")'
    return datacenter_query(
        report_name="RPT_SHAREBONUS_DET",
        filters=filters,
        sort="EX_DIVIDEND_DATE",
    )


def stock_news(code: str) -> list:
    """个股新闻搜索（JSONP 接口）。

    Args:
        code: 股票代码

    Returns:
        新闻列表，每条包含 title / url / date 等字段
    """
    params = {
        "cb": "jQuery_callback",
        "param": (
            '{"uid":"",'
            f'"keyword":"{code}",'
            '"type":["cmsArticleWebOld"],'
            '"client":"web",'
            '"clientType":"web",'
            '"clientVersion":"curr",'
            '"param":{"cmsArticleWebOld":'
            '{"searchScope":"default","sort":"default",'
            '"pageIndex":1,"pageSize":20,"preTag":"<em>","postTag":"</em>"}}}'
        ),
    }
    resp = throttled_get(_SEARCH_API, params=params)
    if resp is None:
        return []
    try:
        text = resp.text
        # 剥离 JSONP 回调: jQuery_callback({...})
        start = text.index("(") + 1
        end = text.rindex(")")
        import json
        data = json.loads(text[start:end])
        result = data.get("result", {})
        articles = result.get("cmsArticleWebOld", {}).get("list", [])
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "date": item.get("date", ""),
                "mediaName": item.get("mediaName", ""),
            }
            for item in articles
        ]
    except (ValueError, KeyError, IndexError):
        return []


def global_news(count: int = 50) -> list:
    """全球财经新闻列表。

    Args:
        count: 获取条数，默认 50

    Returns:
        新闻列表
    """
    params = {
        "fields": "title,content,showTime,url",
        "client": "wap",
        "article_type": "1",
        "pageSize": str(count),
        "pageNo": "1",
    }
    resp = throttled_get(_NEWS_LIST_API, params=params)
    if resp is None:
        return []
    try:
        data = resp.json()
        items = data.get("data", {}).get("list", [])
        return [
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "showTime": item.get("showTime", ""),
            }
            for item in items
        ]
    except (ValueError, AttributeError, KeyError):
        return []


def popularity_rank(top: int = 50) -> list:
    """人气榜排名。

    Args:
        top: 返回前 N 名，默认 50

    Returns:
        人气排名列表，含 code / name / rank 等
    """
    import json as _json
    payload = {
        "appId": "appId01",
        "globalId": "786e4c21-70dc-435a-93bb-38",
        "pageNo": 1,
        "pageSize": top,
    }
    resp = http_post(
        _POPULARITY_API,
        json_data=payload,
    )
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
        return data.get("data", [])
    except (ValueError, AttributeError):
        return []


def concept_hits(code: str) -> list:
    """个股概念热度排名。

    Args:
        code: 股票代码

    Returns:
        概念热度列表
    """
    import json as _json
    payload = {
        "appId": "appId01",
        "globalId": "786e4c21-70dc-435a-93bb-38",
        "srcSecurityCode": code,
    }
    resp = http_post(
        _CONCEPT_HITS_API,
        json_data=payload,
    )
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
        return data.get("data", [])
    except (ValueError, AttributeError):
        return []


def stock_search(keyword: str) -> list:
    """证券代码 / 名称模糊搜索，用于获取 secid 映射。

    Args:
        keyword: 搜索关键词（代码或简称）

    Returns:
        匹配结果列表，含 Code / Name / MktNum / SecurityTypeName 等
    """
    params = {
        "input": keyword,
        "type": "14",
        "token": "D43BF722C8E33BDC906FB84D85E326E8",
        "count": "5",
    }
    resp = throttled_get(_STOCK_SEARCH_API, params=params)
    if resp is None:
        return []
    try:
        data = resp.json()
        quote_list = data.get("QuotationCodeTable", {}).get("Data", [])
        return quote_list if isinstance(quote_list, list) else []
    except (ValueError, AttributeError, KeyError):
        return []


def report_list(code: str = None, industry: str = None,
                page: int = 1, size: int = 20) -> list:
    """研报列表查询。

    Args:
        code: 股票代码，可选
        industry: 行业分类，可选
        page: 页码
        size: 每页条数

    Returns:
        研报列表
    """
    params = {
        "pageNo": str(page),
        "pageSize": str(size),
        "qType": "0",
    }
    if code:
        params["code"] = code
    if industry:
        params["industry"] = industry

    resp = throttled_get(_REPORT_API, params=params)
    if resp is None:
        return []
    try:
        data = resp.json()
        items = data.get("data", [])
        return items if isinstance(items, list) else []
    except (ValueError, AttributeError):
        return []


def announcements_backup(code: str) -> list:
    """公告备用接口（巨潮风格）。

    Args:
        code: 股票代码

    Returns:
        公告列表
    """
    params = {
        "sr": "-1",
        "page_size": "30",
        "page_index": "1",
        "ann_type": "A",
        "stock_list": code,
        "f_node": "0",
        "s_node": "0",
    }
    resp = throttled_get(_ANNOUNCE_API, params=params)
    if resp is None:
        return []
    try:
        data = resp.json()
        items = data.get("data", {}).get("list", [])
        return items if isinstance(items, list) else []
    except (ValueError, AttributeError, KeyError):
        return []
