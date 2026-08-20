# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 多因子选股
============================================

功能概览:
  - multi_factor_screen: 全A多因子筛选（PE/PB/ROE/市值/换手率/行业）
  - index_constituents: 指数成分股（沪深300/中证500/上证50）

数据源:
  - 筛选: 腾讯批量行情 + 条件过滤
  - 成分股: akshare index_stock_cons
"""

from __future__ import annotations

import sys
import os
from typing import Optional

# 路径设置: 确保 core/ 和 providers/ 可导入
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get
from core.cache import cache_get, cache_set, make_key, TTL_KLINE, TTL_FUNDAMENTAL
from core.throttle import throttled_get
from core.ticker import normalize

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

_akshare_available = True
try:
    import akshare
except ImportError:
    _akshare_available = False


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数。"""
    if val is None or val == "" or val == "—" or val == "-":
        return None
    try:
        return float(str(val).replace(",", "").replace("%", ""))
    except (ValueError, TypeError):
        return None


def _safe_int(val) -> Optional[int]:
    """安全转换为整数。"""
    if val is None or val == "" or val == "—":
        return None
    try:
        return int(float(str(val).replace(",", "")))
    except (ValueError, TypeError):
        return None


def _safe_to_list(df) -> list:
    """安全将 DataFrame 转换为字典列表。"""
    if df is None:
        return []
    try:
        if hasattr(df, "to_dict"):
            return df.to_dict("records")
        return list(df) if df is not None else []
    except (TypeError, ValueError, AttributeError):
        return []


# 腾讯批量行情接口
_TENCENT_BATCH_URL = "http://qt.gtimg.cn/q="


def _fetch_all_stocks_batch() -> list[dict]:
    """通过腾讯接口批量获取全A股行情数据。

    分批请求(每批最多80只)以避免URL过长。
    结果包含实时PE/PB/市值/换手率等筛选所需字段。

    Returns:
        全A股行情列表
    """
    # 尝试通过 akshare 获取全市场实时行情
    if _akshare_available:
        try:
            df = akshare.stock_zh_a_spot_em()
            if df is not None and hasattr(df, "to_dict"):
                raw = df.to_dict("records")
                result = []
                for item in raw:
                    code = str(item.get("代码", item.get("code", ""))).zfill(6)
                    result.append({
                        "code": code,
                        "name": item.get("名称", item.get("name", "")),
                        "price": _safe_float(item.get("最新价", item.get("price"))),
                        "change_pct": _safe_float(item.get("涨跌幅", item.get("change_pct"))),
                        "volume": _safe_float(item.get("成交量", item.get("volume"))),
                        "amount": _safe_float(item.get("成交额", item.get("amount"))),
                        "pe": _safe_float(item.get("市盈率-动态", item.get("pe"))),
                        "pb": _safe_float(item.get("市净率", item.get("pb"))),
                        "market_cap": _safe_float(item.get("总市值", item.get("market_cap"))),
                        "circulation_cap": _safe_float(item.get("流通市值", item.get("circulation_cap"))),
                        "turnover_rate": _safe_float(item.get("换手率", item.get("turnover_rate"))),
                        "roe": _safe_float(item.get("ROE", item.get("roe"))),
                        "sector": item.get("所属行业", item.get("sector", item.get("industry", ""))),
                    })
                if result:
                    return result
        except Exception:
            pass

    # Fallback: 新浪行情中心分页(东财 push2 被封时)。
    # 提供 PE/PB/总市值/换手率(无 ROE/行业)。
    return _fetch_all_stocks_sina()


_SINA_MKT_URL = (
    "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/"
    "Market_Center.getHQNodeData"
)
_SINA_MKT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://vip.stock.finance.sina.com.cn/",
}


def _fetch_all_stocks_sina(max_pages: int = 60) -> list[dict]:
    """新浪行情中心分页拉取全 A 股(每页100)。

    字段: per=PE动态, pb, mktcap(总市值/万元), nmc(流通市值/万元),
    turnoverratio=换手率(%)。不含 ROE 与所属行业。
    """
    import json as _json

    result: list[dict] = []
    for page in range(1, max_pages + 1):
        params = {
            "page": str(page),
            "num": "100",
            "sort": "symbol",
            "asc": "1",
            "node": "hs_a",
            "symbol": "",
            "_s_r_a": "page",
        }
        resp = throttled_get(_SINA_MKT_URL, params=params, headers=_SINA_MKT_HEADERS)
        if not resp or not resp.ok:
            break
        try:
            rows = _json.loads(resp.text)
        except (ValueError, TypeError):
            break
        if not isinstance(rows, list) or not rows:
            break

        for item in rows:
            code = str(item.get("code", "")).zfill(6)
            mktcap_wan = _safe_float(item.get("mktcap"))
            nmc_wan = _safe_float(item.get("nmc"))
            result.append({
                "code": code,
                "name": item.get("name", ""),
                "price": _safe_float(item.get("trade")),
                "change_pct": _safe_float(item.get("changepercent")),
                "volume": _safe_float(item.get("volume")),
                "amount": _safe_float(item.get("amount")),
                "pe": _safe_float(item.get("per")),
                "pb": _safe_float(item.get("pb")),
                # 新浪市值单位为万元 → 转换为元
                "market_cap": (mktcap_wan * 10000) if mktcap_wan is not None else None,
                "circulation_cap": (nmc_wan * 10000) if nmc_wan is not None else None,
                "turnover_rate": _safe_float(item.get("turnoverratio")),
                "roe": None,
                "sector": "",
            })

        if len(rows) < 100:
            break

    return result


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def multi_factor_screen(pe_max: float = None, pe_min: float = None,
                        pb_max: float = None, pb_min: float = None,
                        roe_min: float = None,
                        market_cap_min: float = None, market_cap_max: float = None,
                        turnover_min: float = None,
                        sector: str = None,
                        limit: int = 50) -> list[dict]:
    """全A多因子筛选

    从全市场股票中按多个财务/交易因子筛选，支持自定义条件组合。
    
    Source: 腾讯批量行情 + akshare 全市场行情 + 条件过滤

    Args:
        pe_max: 市盈率上限（排除 PE > pe_max 的股票）
        pe_min: 市盈率下限（排除 PE < pe_min 的股票）
        pb_max: 市净率上限
        pb_min: 市净率下限
        roe_min: ROE 最低要求(%)
        market_cap_min: 最小总市值（元），如 1e10 = 100亿
        market_cap_max: 最大总市值（元）
        turnover_min: 最低换手率(%)
        sector: 行业过滤关键词，如 "半导体", "白酒"
        limit: 返回结果数量上限，默认 50

    Returns:
        筛选结果列表:
        [{code, name, price, pe, pb, market_cap, roe, 
          turnover_rate, sector, change_pct, ...}]
    """
    ck = make_key("multi_factor_screen", pe_max, pe_min, pb_max, pb_min,
                  roe_min, market_cap_min, market_cap_max, turnover_min, sector)
    cached = cache_get(ck)
    if cached is not None:
        return cached[:limit]

    # 获取全市场数据
    all_stocks = _fetch_all_stocks_batch()
    if not all_stocks:
        return []

    # 多因子过滤
    filtered = []
    for stock in all_stocks:
        pe = stock.get("pe")
        pb = stock.get("pb")
        roe = stock.get("roe")
        mcap = stock.get("market_cap")
        turnover = stock.get("turnover_rate")
        stock_sector = stock.get("sector", "")
        price = stock.get("price")

        # 跳过停牌/无效数据
        if price is None or price <= 0:
            continue

        # PE 过滤
        if pe_max is not None:
            if pe is None or pe > pe_max or pe <= 0:
                continue
        if pe_min is not None:
            if pe is None or pe < pe_min:
                continue

        # PB 过滤
        if pb_max is not None:
            if pb is None or pb > pb_max:
                continue
        if pb_min is not None:
            if pb is None or pb < pb_min:
                continue

        # ROE 过滤
        if roe_min is not None:
            if roe is None or roe < roe_min:
                continue

        # 市值过滤
        if market_cap_min is not None:
            if mcap is None or mcap < market_cap_min:
                continue
        if market_cap_max is not None:
            if mcap is None or mcap > market_cap_max:
                continue

        # 换手率过滤
        if turnover_min is not None:
            if turnover is None or turnover < turnover_min:
                continue

        # 行业过滤
        if sector is not None:
            if sector not in stock_sector:
                continue

        filtered.append(stock)

    # 按市值降序排列
    filtered.sort(key=lambda x: x.get("market_cap") or 0, reverse=True)

    result = filtered[:limit]
    if result:
        cache_set(ck, filtered, ttl=TTL_FUNDAMENTAL)
    return result


def index_constituents(index_code: str = "000300") -> list[dict]:
    """指数成分股（沪深300/中证500/上证50）

    获取指定指数的全部成分股列表。

    Source: akshare index_stock_cons

    Args:
        index_code: 指数代码，常用:
            - "000300": 沪深300
            - "000905": 中证500
            - "000016": 上证50
            - "000852": 中证1000
            - "399006": 创业板指
            - "000688": 科创50

    Returns:
        成分股列表:
        [{code, name, weight(如有), ...}]
    """
    normalized = normalize(index_code)

    ck = make_key("index_constituents", normalized)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    # 主源: akshare
    if _akshare_available:
        try:
            df = akshare.index_stock_cons(symbol=normalized)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("品种代码", item.get("stock_code", item.get("code", "")))).zfill(6),
                    "name": item.get("品种名称", item.get("stock_name", item.get("name", ""))),
                    "weight": _safe_float(item.get("权重", item.get("weight"))),
                })
        except Exception:
            pass

    # 备源: akshare 另一个接口
    if not result and _akshare_available:
        try:
            df = akshare.index_stock_cons_csindex(symbol=normalized)
            raw = _safe_to_list(df)
            for item in raw:
                result.append({
                    "code": str(item.get("成分券代码", item.get("code", ""))).zfill(6),
                    "name": item.get("成分券名称", item.get("name", "")),
                    "weight": _safe_float(item.get("权重", item.get("weight"))),
                })
        except Exception:
            pass

    # 再备用: 东财 datacenter
    if not result:
        try:
            from providers.eastmoney import datacenter_query
            # 指数映射
            index_name_map = {
                "000300": "沪深300",
                "000905": "中证500",
                "000016": "上证50",
            }
            filters = f'(INDEX_CODE="{normalized}")'
            data = datacenter_query(
                report_name="RPT_INDEX_TS_COMPONENT",
                filters=filters,
                sort="WEIGHT",
                size=500,
            )
            for item in data:
                result.append({
                    "code": str(item.get("SEC_CODE", item.get("SECURITY_CODE", ""))).zfill(6),
                    "name": item.get("SEC_NAME", item.get("SECURITY_NAME_ABBR", "")),
                    "weight": _safe_float(item.get("WEIGHT")),
                })
        except Exception:
            pass

    if result:
        cache_set(ck, result, ttl=TTL_FUNDAMENTAL)
    return result
