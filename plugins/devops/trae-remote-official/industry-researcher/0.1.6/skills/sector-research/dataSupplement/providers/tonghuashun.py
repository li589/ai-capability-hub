"""
同花顺数据 Provider

数据源：10jqka.com.cn 系列域名
协议：HTTPS GET，JSON 响应
封禁风险：低（需正常 User-Agent）
覆盖市场：A股

注意：所有请求需携带正常浏览器 User-Agent 头。
"""

from __future__ import annotations

from datetime import date as _date

from core.client import http_get
from core.throttle import throttled_get
from core.ticker import normalize


# 同花顺通用请求头
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "http://www.10jqka.com.cn/",
    "Accept": "application/json, text/plain, */*",
}


# ========== 热门个股 ==========

_HOT_STOCK_API = "https://eq.10jqka.com.cn/open/api/hot_stock_data"


def hot_stocks(date: str | None = None) -> list[dict]:
    """获取同花顺当日强势股（含题材归因）

    通过同花顺热门个股接口获取当日表现强劲的股票及其强势原因标签。

    Args:
        date: 日期字符串，格式 "YYYY-MM-DD"，默认为当天

    Returns:
        强势股列表，每项包含：
        - code: 股票代码
        - name: 股票名称
        - price: 当前价格
        - change_pct: 涨跌幅(%)
        - reason_tags: 强势原因标签列表
        - hot_rank: 热度排名
        - concept: 关联概念板块
    """
    if date is None:
        date = _date.today().strftime("%Y-%m-%d")

    params = {
        "date": date,
        "type": "strong",
    }
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_HOT_STOCK_API}?{query_str}"

    resp = throttled_get(url, headers=_HEADERS)
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    # 解析响应结构
    result_data = data.get("data", {})
    stock_list = result_data.get("stock_list", [])
    if not stock_list and isinstance(result_data, list):
        stock_list = result_data

    results = []
    for item in stock_list:
        results.append({
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "price": _safe_float(item.get("price")),
            "change_pct": _safe_float(item.get("change_pct") or item.get("rise")),
            "reason_tags": item.get("reason_tags", item.get("tag", [])),
            "hot_rank": item.get("rank", item.get("order")),
            "concept": item.get("concept", item.get("plate", "")),
            "continuous_days": item.get("continuous_days"),
        })

    return results


# ========== 北向资金 ==========

_NORTHBOUND_API = "https://data.10jqka.com.cn/dataCenter/hgt/hk2sh"


def northbound_flow() -> dict:
    """获取北向资金实时/分钟级数据

    通过同花顺互联互通数据中心获取北向资金（沪股通+深股通）实时流入情况。

    Returns:
        北向资金数据字典：
        - total_net_inflow: 北向合计净流入（亿元）
        - sh_net_inflow: 沪股通净流入（亿元）
        - sz_net_inflow: 深股通净流入（亿元）
        - sh_buy: 沪股通买入额
        - sh_sell: 沪股通卖出额
        - sz_buy: 深股通买入额
        - sz_sell: 深股通卖出额
        - minute_data: 分钟级净流入时间序列
        - update_time: 更新时间
    """
    url = _NORTHBOUND_API

    resp = throttled_get(url, headers=_HEADERS)
    if resp is None or not resp.ok:
        return {}
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    result = data.get("data", data)
    if not isinstance(result, dict):
        return {}

    # 解析分钟级数据
    minute_data = []
    minutes_raw = result.get("minute_data", result.get("minuteData", []))
    if isinstance(minutes_raw, list):
        for point in minutes_raw:
            minute_data.append({
                "time": point.get("time", ""),
                "net_inflow": _safe_float(point.get("value") or point.get("net")),
            })

    return {
        "total_net_inflow": _safe_float(result.get("total_net") or result.get("northMoney")),
        "sh_net_inflow": _safe_float(result.get("sh_net") or result.get("hk2sh")),
        "sz_net_inflow": _safe_float(result.get("sz_net") or result.get("hk2sz")),
        "sh_buy": _safe_float(result.get("sh_buy")),
        "sh_sell": _safe_float(result.get("sh_sell")),
        "sz_buy": _safe_float(result.get("sz_buy")),
        "sz_sell": _safe_float(result.get("sz_sell")),
        "minute_data": minute_data,
        "update_time": result.get("update_time", result.get("updateTime", "")),
    }


# ========== 机构一致预期 ==========

_CONSENSUS_API = "https://basic.10jqka.com.cn/basicapi/gdyj/yjbb/web"


def consensus_eps(code: str) -> dict:
    """获取机构一致预期EPS

    通过同花顺盈利预测接口获取机构对个股的一致预期数据。

    Args:
        code: 股票代码，如 "600519"

    Returns:
        一致预期字典：
        - code: 股票代码
        - eps_current_year: 当年预期EPS
        - eps_next_year: 明年预期EPS
        - eps_next2_year: 后年预期EPS
        - pe_current_year: 当年预期PE
        - target_price_avg: 平均目标价
        - target_price_high: 最高目标价
        - target_price_low: 最低目标价
        - rating: 综合评级
        - analyst_count: 覆盖分析师数量
    """
    normalized = normalize(code)
    url = f"{_CONSENSUS_API}/{normalized}"

    resp = throttled_get(url, headers=_HEADERS)
    if resp is None or not resp.ok:
        return {}
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    result = data.get("data", data)
    if not isinstance(result, dict):
        return {}

    # 解析预期数据
    forecasts = result.get("forecast", result.get("data", {}))
    eps_list = forecasts.get("eps", []) if isinstance(forecasts, dict) else []

    parsed = {
        "code": normalized,
        "eps_current_year": _safe_float(eps_list[0]) if len(eps_list) > 0 else None,
        "eps_next_year": _safe_float(eps_list[1]) if len(eps_list) > 1 else None,
        "eps_next2_year": _safe_float(eps_list[2]) if len(eps_list) > 2 else None,
        "pe_current_year": _safe_float(result.get("pe") or (forecasts.get("pe", [None])[0] if isinstance(forecasts, dict) else None)),
        "target_price_avg": _safe_float(result.get("target_price_avg") or result.get("avgPrice")),
        "target_price_high": _safe_float(result.get("target_price_high") or result.get("maxPrice")),
        "target_price_low": _safe_float(result.get("target_price_low") or result.get("minPrice")),
        "rating": result.get("rating", result.get("composite_rating", "")),
        "analyst_count": result.get("analyst_count", result.get("orgNum")),
    }

    return parsed


# ========== 涨停揭秘 ==========

_LIMIT_UP_API = "https://data.10jqka.com.cn/dataCenter/limit_up/info"


def limit_up_detail(date: str) -> list[dict]:
    """获取涨停板详情（涨停揭秘）

    获取指定日期的涨停股票列表及涨停原因、题材、封板率等。

    Args:
        date: 日期字符串，格式 "YYYY-MM-DD"

    Returns:
        涨停详情列表，每项包含：
        - code: 股票代码
        - name: 股票名称
        - reason: 涨停原因
        - theme: 关联题材
        - first_limit_time: 首次涨停时间
        - last_limit_time: 最后涨停时间
        - open_count: 开板次数
        - limit_up_type: 涨停类型（首板/二板/三板...）
        - seal_amount: 封单金额（万元）
        - seal_rate: 封板成功率(%)
    """
    params = {
        "date": date.replace("-", ""),
        "type": "all",
    }
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_LIMIT_UP_API}?{query_str}"

    resp = throttled_get(url, headers=_HEADERS)
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    result_data = data.get("data", {})
    stock_list = result_data.get("list", result_data.get("info", []))
    if not stock_list and isinstance(result_data, list):
        stock_list = result_data

    results = []
    for item in stock_list:
        results.append({
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "reason": item.get("reason", item.get("limit_reason", "")),
            "theme": item.get("theme", item.get("concept", "")),
            "first_limit_time": item.get("first_limit_time", item.get("first_time", "")),
            "last_limit_time": item.get("last_limit_time", item.get("last_time", "")),
            "open_count": item.get("open_count", item.get("open_num", 0)),
            "limit_up_type": item.get("limit_up_type", item.get("continuous", "")),
            "seal_amount": _safe_float(item.get("seal_amount") or item.get("seal_money")),
            "seal_rate": _safe_float(item.get("seal_rate") or item.get("success_rate")),
        })

    return results


# ========== 人气榜单 ==========

_HOT_LIST_API = "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list"


def hot_list(period: str = "hour") -> list[dict]:
    """获取同花顺人气排行榜

    通过同花顺扶摇人气榜接口获取实时关注度排名。

    Args:
        period: 时间维度，可选 "hour"（小时榜）, "day"（日榜）, "3day"（3日榜）

    Returns:
        人气排行列表，每项包含：
        - code: 股票代码
        - name: 股票名称
        - rank: 排名
        - hot_value: 人气值/热度得分
        - change_pct: 涨跌幅(%)
        - rank_change: 排名变动（正数=上升）
        - tag: 标签（如 "新晋", "连续上榜"）
    """
    period_map = {
        "hour": "hour",
        "day": "day",
        "3day": "3day",
        "week": "week",
    }
    p = period_map.get(period, "hour")

    params = {
        "period": p,
        "type": "stock",
    }
    query_str = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{_HOT_LIST_API}?{query_str}"

    resp = throttled_get(url, headers=_HEADERS)
    if resp is None or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    result_data = data.get("data", {})
    stock_list = result_data.get("stock_list", [])
    if not stock_list and isinstance(result_data, list):
        stock_list = result_data

    results = []
    for item in stock_list:
        results.append({
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "rank": item.get("rank", item.get("order")),
            "hot_value": _safe_float(item.get("hot_value") or item.get("score")),
            "change_pct": _safe_float(item.get("change_pct") or item.get("rise")),
            "rank_change": item.get("rank_change", item.get("change", 0)),
            "tag": item.get("tag", ""),
        })

    return results


# ========== 工具函数 ==========

def _safe_float(val) -> float | None:
    """安全转换为浮点数"""
    if val is None or val == "":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return None
