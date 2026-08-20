# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 信号层
=======================================

功能概览:
  - dragon_tiger: 龙虎榜数据（个股或全市场）
  - hot_stocks: 当日强势股 + 题材归因
  - northbound: 北向资金（沪股通 + 深股通）
  - lockup_calendar: 限售解禁日历
  - sector_ranking: 板块排行（行业/概念）
  - stock_sectors: 个股所属板块/概念

数据源优先级与 Fallback 链:
  龙虎榜: 东财 datacenter → 上交所 + 深交所官方
  热门股: 同花顺 eq.10jqka
  北向资金: 同花顺 data.10jqka
  解禁日历: 东财 datacenter RPT_LIFT_STAGE
  板块排行: akshare 概念板块/行业板块
  个股板块: akshare stock_board_concept_name_em

零外部依赖 — 仅使用 Python 标准库 + 项目内部模块。
akshare 为可选依赖，不可用时优雅降级。
"""

from __future__ import annotations

import sys
import os
from datetime import date as _date, datetime as _datetime, timedelta
from typing import Optional

# 设置模块搜索路径以便引用项目内模块
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get, http_post
from core.throttle import throttled_get
from core.ticker import normalize, cn_prefix, to_eastmoney_secid

__all__ = [
    "dragon_tiger",
    "hot_stocks",
    "northbound",
    "lockup_calendar",
    "sector_ranking",
    "stock_sectors",
]

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

def _safe_float(val) -> Optional[float]:
    """安全浮点数转换，处理 None / 空字符串 / 百分号等。"""
    if val is None or val == "" or val == "-":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


def _today_str() -> str:
    """返回当天日期字符串 YYYY-MM-DD。"""
    return _date.today().strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# 东财 datacenter 通用查询
# ---------------------------------------------------------------------------

_DATACENTER_URL = "https://datacenter-web.eastmoney.com/api/data/v1/get"


def _datacenter_query(report_name: str, filters: str = None,
                      columns: str = "ALL", sort: str = None,
                      page: int = 1, size: int = 50) -> list[dict]:
    """东财 datacenter-web 通用查询封装。"""
    params = {
        "sortColumns": sort or "",
        "sortTypes": "-1",
        "pageSize": str(size),
        "pageNumber": str(page),
        "reportName": report_name,
        "columns": columns,
        "source": "WEB",
        "client": "WEB",
    }
    if filters:
        params["filter"] = filters

    resp = throttled_get(_DATACENTER_URL, params=params)
    if not resp or not resp.ok:
        return []
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    result = data.get("result") or {}
    records = result.get("data") or []
    return records if isinstance(records, list) else []


# ===========================================================================
# 公开 API
# ===========================================================================


def dragon_tiger(code: str = None, date: str = None) -> list[dict]:
    """龙虎榜数据（个股或全市场）

    获取指定日期/个股的龙虎榜明细，包含买卖席位、净买入金额等。
    支持全市场查询（不传 code）或单股查询。

    Fallback 链:
        1. 东财 datacenter RPT_DAILYBILLBOARD_DETAILS（优先）
        2. 上交所 + 深交所官方接口（datacenter 被封时降级）

    Args:
        code: 股票代码（6位纯数字），如 "600519"。
              None 表示获取全市场龙虎榜。
        date: 交易日期，格式 "YYYY-MM-DD"。
              None 表示最近一个交易日。

    Returns:
        龙虎榜记录列表，每项包含:
        - code: 股票代码
        - name: 股票名称
        - reason: 上榜原因
        - buy_seats: 买入席位列表 [{name, amount}]
        - sell_seats: 卖出席位列表 [{name, amount}]
        - net_buy: 净买入金额（万元）
        - trade_date: 交易日期
        - close_price: 收盘价
        - change_pct: 涨跌幅(%)
        - turnover: 成交额（万元）

    示例:
        >>> dragon_tiger("600519", "2024-03-15")
        [{code: "600519", name: "贵州茅台", reason: "日涨幅偏离值达7%", ...}]
        >>> dragon_tiger(date="2024-03-15")  # 全市场
    """
    # ─── 主源: 东财 datacenter ───
    results = _dragon_tiger_eastmoney(code, date)
    if results:
        return results

    # ─── Fallback: 上交所 + 深交所官方 ───
    return _dragon_tiger_exchange(code, date)


def _dragon_tiger_eastmoney(code: str = None, date: str = None) -> list[dict]:
    """东财 datacenter 龙虎榜查询。"""
    filters_parts = []
    if code:
        normalized = normalize(code)
        filters_parts.append(f'(SECURITY_CODE="{normalized}")')
    if date:
        filters_parts.append(f"(TRADE_DATE='{date}')")
    filters = "".join(filters_parts) if filters_parts else None

    raw = _datacenter_query(
        report_name="RPT_DAILYBILLBOARD_DETAILS",
        filters=filters,
        sort="TRADE_DATE",
        size=100,
    )
    if not raw:
        return []

    results = []
    for item in raw:
        results.append({
            "code": item.get("SECURITY_CODE", ""),
            "name": item.get("SECURITY_NAME_ABBR", ""),
            "reason": item.get("EXPLAIN", item.get("CHANGE_REASON", "")),
            "buy_seats": _parse_seats(item, "BUY"),
            "sell_seats": _parse_seats(item, "SELL"),
            "net_buy": _safe_float(item.get("NET_BUY_AMT")),
            "trade_date": str(item.get("TRADE_DATE", ""))[:10],
            "close_price": _safe_float(item.get("CLOSE_PRICE")),
            "change_pct": _safe_float(item.get("CHANGE_RATE")),
            "turnover": _safe_float(item.get("TURNOVERRATE")),
            "accum_amount": _safe_float(item.get("ACCUM_AMOUNT")),
        })
    return results


def _parse_seats(item: dict, direction: str) -> list[dict]:
    """解析龙虎榜席位信息。"""
    seats = []
    for i in range(1, 6):
        name_key = f"{direction}_OPERATEDEPT_NAME{i}" if i > 1 else f"{direction}_OPERATEDEPT_NAME"
        amt_key = f"{direction}_OPERATEDEPT_AMT{i}" if i > 1 else f"{direction}_OPERATEDEPT_AMT"
        name = item.get(name_key, "")
        amt = _safe_float(item.get(amt_key))
        if name:
            seats.append({"name": name, "amount": amt})
    return seats


def _dragon_tiger_exchange(code: str = None, date: str = None) -> list[dict]:
    """上交所+深交所官方龙虎榜(降级源)。"""
    if not date:
        date = _today_str()

    results = []

    # 上交所
    try:
        sse_params = {
            "isPagination": "true",
            "pageHelp.pageSize": "100",
            "pageHelp.pageNo": "1",
            "pageHelp.beginPage": "1",
            "pageHelp.cacheSize": "1",
            "type": "inParams",
            "reportDate": date,
        }
        sse_headers = {
            "Referer": "https://www.sse.com.cn",
        }
        resp = http_get(
            "https://query.sse.com.cn/infodisplay/querySpecialTips.do",
            params=sse_params,
            headers=sse_headers,
        )
        if resp and resp.ok:
            data = resp.json()
            page_help = data.get("pageHelp", {})
            records = page_help.get("data", [])
            for r in records:
                rec_code = r.get("stockCode", r.get("SECURITY_CODE", ""))
                if code and normalize(code) != rec_code:
                    continue
                results.append({
                    "code": rec_code,
                    "name": r.get("stockName", r.get("SECURITY_NAME", "")),
                    "reason": r.get("typeDesc", r.get("CHANGE_REASON", "")),
                    "buy_seats": [],
                    "sell_seats": [],
                    "net_buy": None,
                    "trade_date": date,
                    "close_price": _safe_float(r.get("closePrice")),
                    "change_pct": _safe_float(r.get("changeRate")),
                    "turnover": _safe_float(r.get("turnover")),
                    "source": "SSE",
                })
    except Exception:
        pass

    # 深交所
    try:
        szse_params = {
            "SHOWTYPE": "JSON",
            "CATALOGID": "1815_stock",
            "TABKEY": "tab1",
            "txtDate": date,
            "random": "0.5",
        }
        szse_headers = {
            "Referer": "https://www.szse.cn/",
        }
        resp = http_get(
            "https://www.szse.cn/api/report/ShowReport/data",
            params=szse_params,
            headers=szse_headers,
        )
        if resp and resp.ok:
            data = resp.json()
            if isinstance(data, list) and len(data) > 0:
                records = data[0].get("data", [])
                for r in records:
                    rec_code = r.get("证券代码", r.get("SECURITY_CODE", ""))
                    if code and normalize(code) != rec_code:
                        continue
                    results.append({
                        "code": rec_code,
                        "name": r.get("证券简称", r.get("SECURITY_NAME", "")),
                        "reason": r.get("上榜原因", ""),
                        "buy_seats": [],
                        "sell_seats": [],
                        "net_buy": None,
                        "trade_date": date,
                        "close_price": _safe_float(r.get("收盘价")),
                        "change_pct": _safe_float(r.get("涨跌幅")),
                        "turnover": _safe_float(r.get("成交额")),
                        "source": "SZSE",
                    })
    except Exception:
        pass

    return results


def hot_stocks(date: str = None) -> list[dict]:
    """当日强势股 + 题材归因

    通过同花顺热门个股接口获取当日市场上表现强劲的股票及其强势原因标签,
    便于快速了解市场主线、题材轮动方向。

    Source: 同花顺 eq.10jqka.com.cn

    Args:
        date: 日期字符串，格式 "YYYY-MM-DD"。
              None 表示当天。

    Returns:
        强势股列表，每项包含:
        - code: 股票代码
        - name: 股票名称
        - change_pct: 涨跌幅(%)
        - reason_tags: 强势原因标签列表，如 ["人工智能", "芯片"]
        - hot_rank: 热度排名
        - concept: 关联概念板块
        - price: 当前/收盘价
        - continuous_days: 连续强势天数

    示例:
        >>> hot_stocks("2024-03-15")
        [{code: "300059", name: "东方财富", change_pct: 5.2, reason_tags: ["券商"], ...}]
    """
    if date is None:
        date = _date.today().strftime("%Y-%m-%d")

    _THS_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "http://www.10jqka.com.cn/",
        "Accept": "application/json, text/plain, */*",
    }

    # 旧接口 eq.10jqka.com.cn/open/api/hot_stock_data 已下线，
    # 改用同花顺问财热榜 dq.10jqka.com.cn/fuyao/hot_list_data。
    url = "https://dq.10jqka.com.cn/fuyao/hot_list_data/out/hot_list/v1/stock"
    params = {"stock_type": "a", "type": "hour", "list_type": "normal"}

    resp = throttled_get(url, params=params, headers=_THS_HEADERS)
    if not resp or not resp.ok:
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
        tag = item.get("tag", {}) or {}
        concept_tags = tag.get("concept_tag", []) if isinstance(tag, dict) else []
        results.append({
            "code": item.get("code", ""),
            "name": item.get("name", ""),
            "change_pct": _safe_float(item.get("rise_and_fall") or item.get("change_pct")),
            "reason_tags": concept_tags if isinstance(concept_tags, list) else [],
            "hot_rank": item.get("order", item.get("rank")),
            "concept": ", ".join(concept_tags) if isinstance(concept_tags, list) else "",
            "price": _safe_float(item.get("price")),
            "continuous_days": (tag.get("popularity_tag") if isinstance(tag, dict) else None),
        })

    return results


def northbound(realtime: bool = True) -> dict:
    """北向资金（沪股通 + 深股通）

    获取北向资金实时/当日累计净流入数据及分钟级时间序列，
    用于判断外资动向和市场情绪。

    Source: 东财 datacenter / 同花顺 data.10jqka.com.cn (fallback)

    Args:
        realtime: 是否获取实时分钟级数据。
                  True 返回含分钟时序的完整数据；
                  False 仅返回当日汇总。

    Returns:
        北向资金数据字典:
        - sh_net: 沪股通净流入（亿元）
        - sz_net: 深股通净流入（亿元）
        - total_net: 北向合计净流入（亿元）
        - timestamp: 数据更新时间戳
        - minutes: 分钟级净流入序列 [{time, sh, sz, total}]
          （仅 realtime=True 时包含）

    示例:
        >>> northbound()
        {sh_net: 35.2, sz_net: 18.7, total_net: 53.9, timestamp: "2024-03-15 14:30:00", ...}
    """
    # 优先尝试东财 datacenter 北向资金接口
    result = _northbound_eastmoney()
    if result and result.get("total_net") is not None:
        if not realtime:
            result.pop("minutes", None)
        return result

    # Fallback: 同花顺
    _THS_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "http://data.10jqka.com.cn/",
        "Accept": "application/json, text/plain, */*",
    }

    # 获取沪股通数据
    sh_url = "https://data.10jqka.com.cn/dataCenter/hgt/hk2sh"
    sz_url = "https://data.10jqka.com.cn/dataCenter/hgt/hk2sz"

    sh_data = _fetch_northbound_single(sh_url, _THS_HEADERS)
    sz_data = _fetch_northbound_single(sz_url, _THS_HEADERS)

    sh_net = _safe_float(sh_data.get("net") or sh_data.get("hk2sh"))
    sz_net = _safe_float(sz_data.get("net") or sz_data.get("hk2sz"))
    total_net = None
    if sh_net is not None and sz_net is not None:
        total_net = round(sh_net + sz_net, 4)

    result = {
        "sh_net": sh_net,
        "sz_net": sz_net,
        "total_net": total_net,
        "timestamp": sh_data.get("update_time", sz_data.get("update_time", "")),
    }

    # 解析分钟级数据
    if realtime:
        minutes = []
        sh_minutes = sh_data.get("minute_data", [])
        sz_minutes = sz_data.get("minute_data", [])

        # 合并沪深分钟数据
        sh_map = {}
        for point in sh_minutes:
            t = point.get("time", "")
            sh_map[t] = _safe_float(point.get("value") or point.get("net"))

        for point in sz_minutes:
            t = point.get("time", "")
            sz_val = _safe_float(point.get("value") or point.get("net"))
            sh_val = sh_map.get(t)
            total = None
            if sh_val is not None and sz_val is not None:
                total = round(sh_val + sz_val, 4)
            minutes.append({
                "time": t,
                "sh": sh_val,
                "sz": sz_val,
                "total": total,
            })

        result["minutes"] = minutes

    return result


def _northbound_eastmoney() -> dict:
    """东财 datacenter 北向资金（主源）。"""
    from datetime import date as _date
    today = _date.today().strftime("%Y-%m-%d")

    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    params = {
        "sortColumns": "TRADE_DATE",
        "sortTypes": "-1",
        "pageSize": "1",
        "pageNumber": "1",
        "reportName": "RPT_MUTUAL_DEAL_HISTORY",
        "columns": "ALL",
        "source": "WEB",
        "client": "WEB",
        "filter": f'(MUTUAL_TYPE="001")',
    }

    try:
        resp = throttled_get(url, params=params)
    except Exception:
        return {}
    if not resp or not resp.ok:
        return {}
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    result_data = data.get("result", {})
    if not result_data:
        return {}
    records = result_data.get("data", [])
    if not records:
        return {}

    rec = records[0]
    # 东财字段: FUNDS_DIRECTION / NET_DEAL_AMT / DEAL_AMT / BUY_AMT / SELL_AMT
    # 沪股通: MUTUAL_TYPE=003, 深股通: MUTUAL_TYPE=001(汇总)/004
    # 这里 001 是北向汇总

    sh_net = _safe_float(rec.get("SH_NET_BUY_AMT"))
    sz_net = _safe_float(rec.get("SZ_NET_BUY_AMT"))
    total_net = _safe_float(rec.get("NET_DEAL_AMT") or rec.get("NET_BUY_AMT"))

    # 转换为亿元（datacenter 单位为元）
    if sh_net is not None:
        sh_net = round(sh_net / 1e8, 4)
    if sz_net is not None:
        sz_net = round(sz_net / 1e8, 4)
    if total_net is not None:
        total_net = round(total_net / 1e8, 4)
    elif sh_net is not None and sz_net is not None:
        total_net = round(sh_net + sz_net, 4)

    return {
        "sh_net": sh_net,
        "sz_net": sz_net,
        "total_net": total_net,
        "timestamp": rec.get("TRADE_DATE", ""),
        "minutes": [],
    }


def _fetch_northbound_single(url: str, headers: dict) -> dict:
    """获取单个方向的北向资金数据。"""
    resp = throttled_get(url, headers=headers)
    if not resp or not resp.ok:
        return {}
    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return {}

    result = data.get("data", data)
    return result if isinstance(result, dict) else {}


def lockup_calendar(code: str = None, days_ahead: int = 90) -> list[dict]:
    """限售解禁日历

    查询未来一段时间内的限售股解禁计划，用于规避解禁压力。
    支持按个股查询或全市场扫描。

    Source: 东财 datacenter RPT_LIFT_STAGE

    Args:
        code: 股票代码（6位数字），如 "600519"。
              None 表示全市场查询。
        days_ahead: 向前查询天数，默认 90 天。
                    传 0 查询历史全部记录。

    Returns:
        解禁记录列表，每项包含:
        - code: 股票代码
        - name: 股票名称
        - free_date: 解禁日期（YYYY-MM-DD）
        - free_shares: 解禁股数（万股）
        - free_market_value: 解禁市值（万元）
        - free_ratio: 解禁占总股本比例(%)
        - lock_type: 限售类型（如"首发原股东限售"）
        - holder_name: 股东名称

    示例:
        >>> lockup_calendar("600519", days_ahead=30)
        [{code: "600519", name: "贵州茅台", free_date: "2024-04-20", ...}]
        >>> lockup_calendar(days_ahead=7)  # 未来7天全市场解禁
    """
    filters_parts = []
    if code:
        normalized = normalize(code)
        filters_parts.append(f'(SECURITY_CODE="{normalized}")')

    # 时间范围过滤
    if days_ahead > 0:
        today = _date.today()
        end_date = today + timedelta(days=days_ahead)
        filters_parts.append(
            f"(FREE_DATE>='{today.strftime('%Y-%m-%d')}')"
        )
        filters_parts.append(
            f"(FREE_DATE<='{end_date.strftime('%Y-%m-%d')}')"
        )

    filters = "".join(filters_parts) if filters_parts else None

    raw = _datacenter_query(
        report_name="RPT_LIFT_STAGE",
        filters=filters,
        sort="FREE_DATE",
        size=200,
    )

    results = []
    for item in raw:
        results.append({
            "code": item.get("SECURITY_CODE", ""),
            "name": item.get("SECURITY_NAME_ABBR", item.get("SECURITY_NAME", "")),
            "free_date": str(item.get("FREE_DATE", ""))[:10],
            "free_shares": _safe_float(item.get("FREE_SHARES_QUANTITY")),
            "free_market_value": _safe_float(item.get("FREE_MARKET_CAP")),
            "free_ratio": _safe_float(item.get("FREE_RATIO")),
            "lock_type": item.get("LIFT_REASON", item.get("RESTRICTIVE_TYPE", "")),
            "holder_name": item.get("HOLDER_NAME", ""),
        })

    return results


def sector_ranking(board_type: str = "industry") -> list[dict]:
    """板块排行（行业/概念）

    获取当前市场板块涨跌排名，包含领涨股、成交量等信息。
    用于快速把握市场轮动方向和主线板块。

    Source: akshare stock_board_concept_name_em / stock_board_industry_name_em

    Args:
        board_type: 板块类型，可选:
            - "industry": 行业板块排行（默认）
            - "concept": 概念板块排行

    Returns:
        板块排行列表，每项包含:
        - name: 板块名称
        - change_pct: 涨跌幅(%)
        - leader_stock: 领涨股名称
        - leader_code: 领涨股代码
        - volume: 总成交量（手）
        - turnover: 总成交额（元）
        - stock_count: 板块内股票数量
        - rise_count: 上涨股票数
        - fall_count: 下跌股票数

    示例:
        >>> sector_ranking("concept")
        [{name: "人工智能", change_pct: 3.5, leader_stock: "...", ...}]
    """
    try:
        import akshare
    except ImportError:
        return _sector_ranking_fallback(board_type)

    try:
        if board_type == "concept":
            df = akshare.stock_board_concept_name_em()
        else:
            df = akshare.stock_board_industry_name_em()
    except Exception:
        return _sector_ranking_fallback(board_type)

    if df is None or not hasattr(df, "to_dict"):
        return []

    records = df.to_dict("records")
    results = []
    for item in records:
        results.append({
            "name": item.get("板块名称", item.get("name", "")),
            "change_pct": _safe_float(item.get("涨跌幅", item.get("change_pct"))),
            "leader_stock": item.get("领涨股票", item.get("leader_stock", "")),
            "leader_code": item.get("领涨股票-代码", item.get("leader_code", "")),
            "volume": _safe_float(item.get("总手", item.get("volume"))),
            "turnover": _safe_float(item.get("成交额", item.get("turnover"))),
            "stock_count": item.get("上市家数", item.get("stock_count")),
            "rise_count": item.get("上涨家数", item.get("rise_count")),
            "fall_count": item.get("下跌家数", item.get("fall_count")),
        })

    return results


def _sector_ranking_fallback(board_type: str) -> list[dict]:
    """板块排行降级方案 — 新浪(行业) → push2 → datacenter-web。"""
    # 路径0: 新浪行业板块（东财 push2 已 IP 级封禁，新浪最稳）
    try:
        from providers import sina
        result = sina.sector_ranking(board_type)
        if result:
            return result
    except Exception:
        pass

    # 路径1: push2.eastmoney.com (实时，可能被封)
    result = _sector_ranking_push2(board_type)
    if result:
        return result

    # 路径2: datacenter-web.eastmoney.com (日频)
    return _sector_ranking_datacenter(board_type)


def _sector_ranking_push2(board_type: str) -> list[dict]:
    """push2 板块排行。"""
    if board_type == "concept":
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "50",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fs": "m:90+t:3",
            "fields": "f2,f3,f4,f12,f14,f128,f136,f140,f141",
        }
    else:
        url = "https://push2.eastmoney.com/api/qt/clist/get"
        params = {
            "pn": "1",
            "pz": "50",
            "po": "1",
            "np": "1",
            "fltt": "2",
            "invt": "2",
            "fs": "m:90+t:2",
            "fields": "f2,f3,f4,f12,f14,f128,f136,f140,f141",
        }

    try:
        resp = throttled_get(url, params=params)
    except Exception:
        return []
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    diff = data.get("data", {}).get("diff", [])
    if not isinstance(diff, list):
        return []

    results = []
    for item in diff:
        results.append({
            "name": item.get("f14", ""),
            "change_pct": _safe_float(item.get("f3")),
            "leader_stock": item.get("f128", ""),
            "leader_code": item.get("f140", ""),
            "volume": _safe_float(item.get("f136")),
            "turnover": _safe_float(item.get("f141")),
            "stock_count": None,
            "rise_count": None,
            "fall_count": None,
        })

    return results


def _sector_ranking_datacenter(board_type: str) -> list[dict]:
    """datacenter-web 板块排行（第二 fallback）。"""
    url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    if board_type == "concept":
        report_name = "RPT_BOARD_CONCEPT"
    else:
        report_name = "RPT_BOARD_INDUSTRY"

    params = {
        "sortColumns": "CHANGE_RATE",
        "sortTypes": "-1",
        "pageSize": "50",
        "pageNumber": "1",
        "reportName": report_name,
        "columns": "ALL",
        "source": "WEB",
        "client": "WEB",
    }

    try:
        resp = throttled_get(url, params=params)
    except Exception:
        return []
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    result_data = data.get("result", {})
    if not result_data:
        return []
    records = result_data.get("data", [])
    if not isinstance(records, list):
        return []

    results = []
    for item in records:
        results.append({
            "name": item.get("BOARD_NAME", item.get("INDUSTRY_NAME", "")),
            "change_pct": _safe_float(item.get("CHANGE_RATE")),
            "leader_stock": item.get("LEADER_STOCK_NAME", ""),
            "leader_code": item.get("LEADER_STOCK_CODE", ""),
            "volume": _safe_float(item.get("VOLUME")),
            "turnover": _safe_float(item.get("DEAL_AMOUNT")),
            "stock_count": item.get("STOCK_COUNT"),
            "rise_count": item.get("RISE_COUNT"),
            "fall_count": item.get("FALL_COUNT"),
        })

    return results


def stock_sectors(code: str) -> list[dict]:
    """个股所属板块/概念

    查询指定股票所属的所有概念板块和行业板块，
    便于理解个股的题材属性和板块联动关系。

    Source: akshare stock_board_concept_name_em（遍历匹配）
    Fallback: 东财个股概念接口

    Args:
        code: 股票代码（6位数字），如 "600519"

    Returns:
        所属板块列表，每项包含:
        - board_name: 板块名称
        - board_type: 板块类型（"concept" 或 "industry"）
        - change_pct: 板块当日涨跌幅(%)
        - rank: 板块排名

    示例:
        >>> stock_sectors("600519")
        [{board_name: "白酒", board_type: "industry", change_pct: 1.2, ...}]
    """
    normalized = normalize(code)

    # 优先尝试 akshare 方案
    try:
        import akshare
        results = _stock_sectors_akshare(normalized, akshare)
        if results:
            return results
    except ImportError:
        pass

    # Fallback: 东财个股概念
    return _stock_sectors_eastmoney(normalized)


def _stock_sectors_akshare(code: str, ak_module) -> list[dict]:
    """通过 akshare 获取个股所属概念板块。"""
    try:
        df = ak_module.stock_board_concept_name_em()
        if df is None or not hasattr(df, "iterrows"):
            return []
    except Exception:
        return []

    results = []
    concept_names = df.to_dict("records")

    for idx, board in enumerate(concept_names):
        board_name = board.get("板块名称", "")
        try:
            detail_df = ak_module.stock_board_concept_cons_em(symbol=board_name)
            if detail_df is None:
                continue
            codes_in_board = detail_df["代码"].tolist() if "代码" in detail_df.columns else []
            if code in codes_in_board:
                results.append({
                    "board_name": board_name,
                    "board_type": "concept",
                    "change_pct": _safe_float(board.get("涨跌幅")),
                    "rank": idx + 1,
                })
        except Exception:
            continue

        # 限制遍历数量以控制请求量
        if idx > 50:
            break

    return results


def _stock_sectors_eastmoney(code: str) -> list[dict]:
    """通过东财接口获取个股所属板块。"""
    secid = to_eastmoney_secid(code)
    url = "https://push2.eastmoney.com/api/qt/slist/get"
    params = {
        "secid": secid,
        "pn": "1",
        "pz": "50",
        "po": "1",
        "np": "1",
        "invt": "2",
        "fltt": "2",
        "fields": "f2,f3,f12,f14",
        "spt": "3",
    }

    resp = throttled_get(url, params=params)
    if not resp or not resp.ok:
        return []

    try:
        data = resp.json()
    except (ValueError, AttributeError):
        return []

    diff = data.get("data", {}).get("diff", [])
    if not isinstance(diff, list):
        return []

    results = []
    for idx, item in enumerate(diff):
        results.append({
            "board_name": item.get("f14", ""),
            "board_type": "concept",
            "change_pct": _safe_float(item.get("f3")),
            "rank": idx + 1,
        })

    return results
