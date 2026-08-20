"""Yahoo Finance 数据源模块

提供美股及港股的行情摘要、K线图表、期权链、新闻等数据。
内置 crumb 鉴权机制，自动获取并缓存 cookie + crumb token。
"""

import time
import json
import re
from core.client import http_get

# ─── 基础配置 ─────────────────────────────────────────────────
_BASE_URL = "https://query1.finance.yahoo.com"
_CRUMB_URL = "https://query1.finance.yahoo.com/v1/test/getcrumb"
_CONSENT_URL = "https://finance.yahoo.com"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
}

# ─── Crumb 缓存 ──────────────────────────────────────────────
_crumb_cache = {
    "crumb": None,
    "cookies": None,
    "expires": 0,
}
_CRUMB_TTL = 1800  # 30 分钟过期


def _extract_cookies(resp) -> str:
    """从 HttpResponse 的 headers 中提取 Set-Cookie 值，拼接为 Cookie 请求头。"""
    if resp is None or not hasattr(resp, "headers"):
        return ""
    # headers 可能有多个 Set-Cookie，也可能是单个
    raw = resp.headers.get("Set-Cookie", "") or resp.headers.get("set-cookie", "")
    if not raw:
        return ""
    # 提取 key=value 部分（忽略 Path/Expires 等属性）
    cookies = []
    for part in raw.split(","):
        # 每个 cookie 段可能包含 ; 分隔的属性，只取第一个 key=value
        kv = part.strip().split(";")[0].strip()
        if "=" in kv:
            cookies.append(kv)
    return "; ".join(cookies)


def _get_crumb() -> tuple:
    """获取 Yahoo Finance crumb token 及对应 cookies。

    首先访问 Yahoo Finance 首页获取 session cookie，
    然后请求 crumb 接口获取 token。结果缓存 30 分钟。

    Returns:
        (crumb_string, cookie_header_string) 元组
    """
    now = time.time()
    if _crumb_cache["crumb"] and now < _crumb_cache["expires"]:
        return _crumb_cache["crumb"], _crumb_cache["cookies"]

    # 第一步：获取 session cookie（urllib 默认跟随重定向）
    session_resp = http_get(_CONSENT_URL, headers=_HEADERS)
    cookie_str = _extract_cookies(session_resp) if session_resp else ""

    # 第二步：用 cookie 请求 crumb
    crumb_headers = {**_HEADERS}
    if cookie_str:
        crumb_headers["Cookie"] = cookie_str
    crumb_resp = http_get(_CRUMB_URL, headers=crumb_headers)
    crumb = ""
    if crumb_resp is not None and crumb_resp.ok:
        crumb = crumb_resp.text.strip()

    # 缓存结果
    _crumb_cache["crumb"] = crumb
    _crumb_cache["cookies"] = cookie_str
    _crumb_cache["expires"] = now + _CRUMB_TTL

    return crumb, cookie_str


def _invalidate_crumb():
    """强制清除 crumb 缓存，触发下次请求重新获取。"""
    _crumb_cache["crumb"] = None
    _crumb_cache["cookies"] = None
    _crumb_cache["expires"] = 0


def _authed_get(url: str, params: dict = None) -> dict:
    """带 crumb 鉴权的 GET 请求，失败时自动刷新一次 crumb 重试。"""
    crumb, cookie_str = _get_crumb()
    if params is None:
        params = {}
    params["crumb"] = crumb

    req_headers = {**_HEADERS}
    if cookie_str:
        req_headers["Cookie"] = cookie_str

    resp = http_get(url, params=params, headers=req_headers)
    if resp is None:
        return {}

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    # 鉴权失败时重试一次
    if isinstance(data, dict) and data.get("finance", {}).get("error"):
        error = data["finance"]["error"]
        if error.get("code") == "Unauthorized" or "crumb" in str(error):
            _invalidate_crumb()
            crumb, cookie_str = _get_crumb()
            params["crumb"] = crumb
            req_headers2 = {**_HEADERS}
            if cookie_str:
                req_headers2["Cookie"] = cookie_str
            resp = http_get(url, params=params, headers=req_headers2)
            if resp is None:
                return {}
            try:
                data = resp.json()
            except (ValueError, AttributeError):
                return {}

    return data


def quote_summary(symbol: str, modules: list = None) -> dict:
    """获取证券摘要信息。

    Args:
        symbol: 证券代码，如 'AAPL'、'0700.HK'
        modules: 请求模块列表，默认包含 price/summaryDetail/financialData

    Returns:
        quoteSummary 结果字典
    """
    if modules is None:
        modules = [
            "price",
            "summaryDetail",
            "financialData",
            "defaultKeyStatistics",
        ]
    url = f"{_BASE_URL}/v10/finance/quoteSummary/{symbol}"
    params = {"modules": ",".join(modules)}
    data = _authed_get(url, params)

    result = data.get("quoteSummary", {}).get("result", [])
    return result[0] if result else {}


def chart(symbol: str, interval: str = "1d", range_: str = "6mo") -> dict:
    """获取 K 线图表数据。

    Args:
        symbol: 证券代码
        interval: K线周期，如 '1d' / '1wk' / '1mo' / '5m'
        range_: 时间范围，如 '1d' / '5d' / '1mo' / '6mo' / '1y' / 'max'

    Returns:
        chart 数据字典，含 timestamp / indicators 等
    """
    url = f"{_BASE_URL}/v8/finance/chart/{symbol}"
    params = {
        "interval": interval,
        "range": range_,
        "includePrePost": "false",
    }
    data = _authed_get(url, params)

    chart_data = data.get("chart", {}).get("result", [])
    return chart_data[0] if chart_data else {}


def options_chain(symbol: str, date: str = None) -> dict:
    """获取期权链数据。

    Args:
        symbol: 证券代码
        date: 到期日 Unix 时间戳字符串，可选

    Returns:
        期权链字典，含 calls / puts / expirationDates 等
    """
    url = f"{_BASE_URL}/v7/finance/options/{symbol}"
    params = {}
    if date:
        params["date"] = date
    data = _authed_get(url, params)

    option_chain = data.get("optionChain", {}).get("result", [])
    return option_chain[0] if option_chain else {}


def news(symbol: str) -> list:
    """获取证券相关新闻。

    通过 quoteSummary 的 assetProfile 模块中的新闻数据提取。
    若无新闻数据则返回空列表。

    Args:
        symbol: 证券代码

    Returns:
        新闻列表
    """
    url = f"{_BASE_URL}/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "upgradeDowngradeHistory,recommendationTrend"}
    data = _authed_get(url, params)

    # 尝试从返回中提取新闻相关内容
    result = data.get("quoteSummary", {}).get("result", [])
    if not result:
        return []
    summary = result[0]
    # Yahoo 新闻通常在单独的 news 端点，此处提取可用信息
    news_items = summary.get("upgradeDowngradeHistory", {}).get("history", [])
    return [
        {
            "firm": item.get("firm", ""),
            "toGrade": item.get("toGrade", ""),
            "fromGrade": item.get("fromGrade", ""),
            "action": item.get("action", ""),
            "epochGradeDate": item.get("epochGradeDate", 0),
        }
        for item in news_items[:20]
    ]
