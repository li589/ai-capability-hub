# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 期权
======================================

功能概览:
  - option_chain: 期权合约清单（按标的/月份）
  - option_quote: 期权T型报价（买卖五档/持仓量/行权价/最新价）
  - option_greeks: 期权希腊字母 + 隐含波动率

数据源:
  - A股ETF期权(510050/510300/588000/510500): 新浪 hq.sinajs.cn
  - 美股期权: Yahoo Finance options chain
"""

from __future__ import annotations

import sys
import os
import re
import json
from typing import Optional

# 路径设置: 确保 core/ 和 providers/ 可导入
_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.client import http_get
from core.cache import cache_get, cache_set, make_key, TTL_QUOTE, TTL_KLINE
from core.throttle import throttled_get
from core.ticker import normalize, detect_market, to_yahoo_symbol

# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------

# 支持的A股ETF期权标的
_CN_OPTION_UNDERLYINGS = {"510050", "510300", "588000", "510500", "159919", "159901"}

_SINA_OPTION_API = "https://stock.finance.sina.com.cn/futures/api/openapi.php"
_SINA_HQ_API = "http://hq.sinajs.cn/list="

_SINA_HEADERS = {
    "Referer": "https://finance.sina.com.cn/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


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


def _is_cn_option_underlying(code: str) -> bool:
    """判断是否为A股ETF期权标的。"""
    normalized = normalize(code)
    return normalized in _CN_OPTION_UNDERLYINGS


# ---------------------------------------------------------------------------
# A股期权 — 新浪数据源
# ---------------------------------------------------------------------------


def _sina_option_months(underlying: str) -> list[str]:
    """获取新浪期权可用合约月份列表。

    Args:
        underlying: 标的代码，如 '510050'

    Returns:
        月份列表，如 ['2407', '2408', '2409', '2412']
    """
    url = f"{_SINA_OPTION_API}?app=option&cat=OptionService&exec=getRemainderDay&underlying={underlying}"
    try:
        resp = throttled_get(url, headers=_SINA_HEADERS)
        if resp and resp.ok:
            data = resp.json()
            result = data.get("result", {})
            month_data = result.get("data", [])
            if isinstance(month_data, list):
                return [str(m.get("month", m.get("contractMonth", ""))) for m in month_data if m]
            # 尝试从 keys 获取
            if isinstance(result, dict) and "data" not in result:
                return list(result.keys())
    except Exception:
        pass
    return []


def _sina_option_contracts(underlying: str, month: str, direction: str = "call") -> list[dict]:
    """获取新浪期权指定月份合约列表。"""
    url = (
        f"{_SINA_OPTION_API}?app=option&cat=OptionService"
        f"&exec=getContractList&underlying={underlying}"
        f"&month={month}&direction={direction}"
    )
    try:
        resp = throttled_get(url, headers=_SINA_HEADERS)
        if resp and resp.ok:
            data = resp.json()
            result = data.get("result", {})
            contracts = result.get("data", [])
            if isinstance(contracts, list):
                return contracts
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# 美股期权 — Yahoo Finance
# ---------------------------------------------------------------------------


def _yahoo_options_chain(symbol: str, date: str = None) -> dict:
    """从 Yahoo Finance 获取期权链数据。"""
    try:
        from providers.yahoo import options_chain as yahoo_options
        return yahoo_options(symbol, date=date)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------


def option_chain(underlying: str, month: str = None) -> list[dict]:
    """期权合约清单

    获取指定标的的期权合约列表。
    - A股ETF(510050/510300/588000/510500): 通过新浪获取
    - 美股: 通过 Yahoo Finance 获取

    Args:
        underlying: 标的代码，如 '510050'(50ETF)、'AAPL'(苹果)
        month: 合约月份，如 '2407'；None 则返回最近月所有合约

    Returns:
        合约列表:
        [{contract_code, strike, expiry, type(call/put), underlying, ...}]
    """
    normalized = normalize(underlying)

    # 缓存检查
    ck = make_key("option_chain", normalized, month or "all")
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = []

    # A股ETF期权 → 新浪
    if _is_cn_option_underlying(normalized):
        # 获取可用月份
        if month is None:
            months = _sina_option_months(normalized)
            month = months[0] if months else None

        if month:
            for direction in ("call", "put"):
                contracts = _sina_option_contracts(normalized, month, direction)
                for c in contracts:
                    result.append({
                        "contract_code": c.get("contractCode", c.get("code", "")),
                        "contract_symbol": c.get("contractSymbol", c.get("symbol", "")),
                        "strike": _safe_float(c.get("strike", c.get("exercisePrice"))),
                        "expiry": c.get("expireDate", c.get("expire_date", month)),
                        "type": direction,
                        "underlying": normalized,
                        "last_price": _safe_float(c.get("lastPrice")),
                    })

        # 降级: 新浪 OptionService 无返回时，用 akshare 上交所接口补齐合约代码
        if not result:
            try:
                from providers import akshare_bridge
                for call_flag, direction in ((True, "call"), (False, "put")):
                    for c in akshare_bridge.option_contracts_cn(normalized, call=call_flag):
                        result.append({
                            "contract_code": c.get("contract_code", ""),
                            "contract_symbol": c.get("contract_code", ""),
                            "strike": None,
                            "expiry": c.get("month", ""),
                            "type": direction,
                            "underlying": normalized,
                            "last_price": None,
                        })
            except Exception:
                pass
    else:
        # 美股 → Yahoo Finance
        try:
            market = detect_market(underlying)
        except ValueError:
            market = "US"

        if market in ("US", "HK"):
            yahoo_symbol = to_yahoo_symbol(underlying)
            chain_data = _yahoo_options_chain(yahoo_symbol)

            if chain_data:
                # 解析 Yahoo 期权链
                calls = chain_data.get("options", [{}])[0].get("calls", []) if chain_data.get("options") else []
                puts = chain_data.get("options", [{}])[0].get("puts", []) if chain_data.get("options") else []

                for c in calls:
                    result.append({
                        "contract_code": c.get("contractSymbol", ""),
                        "contract_symbol": c.get("contractSymbol", ""),
                        "strike": _safe_float(c.get("strike")),
                        "expiry": c.get("expiration", {}).get("fmt", "") if isinstance(c.get("expiration"), dict) else str(c.get("expiration", "")),
                        "type": "call",
                        "underlying": normalized,
                        "last_price": _safe_float(c.get("lastPrice", {}).get("raw") if isinstance(c.get("lastPrice"), dict) else c.get("lastPrice")),
                        "bid": _safe_float(c.get("bid", {}).get("raw") if isinstance(c.get("bid"), dict) else c.get("bid")),
                        "ask": _safe_float(c.get("ask", {}).get("raw") if isinstance(c.get("ask"), dict) else c.get("ask")),
                        "volume": _safe_int(c.get("volume", {}).get("raw") if isinstance(c.get("volume"), dict) else c.get("volume")),
                        "open_interest": _safe_int(c.get("openInterest", {}).get("raw") if isinstance(c.get("openInterest"), dict) else c.get("openInterest")),
                        "iv": _safe_float(c.get("impliedVolatility", {}).get("raw") if isinstance(c.get("impliedVolatility"), dict) else c.get("impliedVolatility")),
                    })

                for p in puts:
                    result.append({
                        "contract_code": p.get("contractSymbol", ""),
                        "contract_symbol": p.get("contractSymbol", ""),
                        "strike": _safe_float(p.get("strike")),
                        "expiry": p.get("expiration", {}).get("fmt", "") if isinstance(p.get("expiration"), dict) else str(p.get("expiration", "")),
                        "type": "put",
                        "underlying": normalized,
                        "last_price": _safe_float(p.get("lastPrice", {}).get("raw") if isinstance(p.get("lastPrice"), dict) else p.get("lastPrice")),
                        "bid": _safe_float(p.get("bid", {}).get("raw") if isinstance(p.get("bid"), dict) else p.get("bid")),
                        "ask": _safe_float(p.get("ask", {}).get("raw") if isinstance(p.get("ask"), dict) else p.get("ask")),
                        "volume": _safe_int(p.get("volume", {}).get("raw") if isinstance(p.get("volume"), dict) else p.get("volume")),
                        "open_interest": _safe_int(p.get("openInterest", {}).get("raw") if isinstance(p.get("openInterest"), dict) else p.get("openInterest")),
                        "iv": _safe_float(p.get("impliedVolatility", {}).get("raw") if isinstance(p.get("impliedVolatility"), dict) else p.get("impliedVolatility")),
                    })

    if result:
        cache_set(ck, result, ttl=TTL_KLINE)
    return result


def option_quote(contract_code: str) -> dict:
    """期权T型报价（买卖五档/持仓量/行权价/最新价）

    获取单个期权合约的实时行情报价。
    - A股: 通过新浪 hq.sinajs.cn CON_OP_ 前缀获取
    - 美股: 通过 Yahoo Finance options chain 获取

    Args:
        contract_code: 期权合约代码
            - A股: 纯数字如 '10007306'
            - 美股: Yahoo 格式如 'AAPL240719C00200000'

    Returns:
        T型报价字典:
        {contract_code, latest_price, bid_price, ask_price,
         position, volume, strike, bid1~5, ask1~5, ...}
    """
    ck = make_key("option_quote", contract_code)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = {}

    # 判断A股还是美股: A股合约代码为纯数字
    if contract_code.isdigit():
        # A股期权 → 新浪 hq.sinajs.cn
        try:
            from providers.sina import option_tquote
            result = option_tquote(contract_code)
        except Exception:
            pass

        # 如果 providers 调用失败，直接请求
        if not result:
            try:
                url = f"{_SINA_HQ_API}CON_OP_{contract_code}"
                resp = http_get(url, encoding="gbk", headers=_SINA_HEADERS)
                text = resp.text if hasattr(resp, "text") else str(resp)

                match = re.search(r'"([^"]*)"', text)
                if match:
                    fields = match.group(1).split(",")
                    if len(fields) >= 42:
                        def _f(idx):
                            try:
                                v = fields[idx].strip()
                                return float(v) if v else None
                            except (IndexError, ValueError):
                                return None

                        def _i(idx):
                            try:
                                v = fields[idx].strip()
                                return int(float(v)) if v else None
                            except (IndexError, ValueError):
                                return None

                        result = {
                            "contract_code": contract_code,
                            "buy_price": _f(0),
                            "sell_price": _f(1),
                            "latest_price": _f(2),
                            "position": _i(5),
                            "volume": _i(41),
                            "bid1_price": _f(6),
                            "bid1_vol": _i(7),
                            "bid2_price": _f(8),
                            "bid2_vol": _i(9),
                            "bid3_price": _f(10),
                            "bid3_vol": _i(11),
                            "bid4_price": _f(12),
                            "bid4_vol": _i(13),
                            "bid5_price": _f(14),
                            "bid5_vol": _i(15),
                            "ask1_price": _f(16),
                            "ask1_vol": _i(17),
                            "ask2_price": _f(18),
                            "ask2_vol": _i(19),
                            "ask3_price": _f(20),
                            "ask3_vol": _i(21),
                            "ask4_price": _f(22),
                            "ask4_vol": _i(23),
                            "ask5_price": _f(24),
                            "ask5_vol": _i(25),
                            "strike": _f(37),
                            "settle_price": _f(38),
                            "expire_date": fields[36].strip() if len(fields) > 36 else None,
                        }
            except Exception:
                pass
    else:
        # 美股期权 → 提取标的符号后通过 Yahoo 获取
        # Yahoo 合约格式: AAPL240719C00200000 → underlying=AAPL
        match = re.match(r'^([A-Z]+)\d', contract_code)
        if match:
            underlying_symbol = match.group(1)
            chain_data = _yahoo_options_chain(underlying_symbol)
            if chain_data and chain_data.get("options"):
                options = chain_data["options"][0]
                all_contracts = options.get("calls", []) + options.get("puts", [])
                for c in all_contracts:
                    if c.get("contractSymbol") == contract_code:
                        def _raw(v):
                            return v.get("raw") if isinstance(v, dict) else v

                        result = {
                            "contract_code": contract_code,
                            "latest_price": _safe_float(_raw(c.get("lastPrice", {}))),
                            "bid_price": _safe_float(_raw(c.get("bid", {}))),
                            "ask_price": _safe_float(_raw(c.get("ask", {}))),
                            "volume": _safe_int(_raw(c.get("volume", {}))),
                            "position": _safe_int(_raw(c.get("openInterest", {}))),
                            "strike": _safe_float(_raw(c.get("strike", {}))),
                            "change": _safe_float(_raw(c.get("change", {}))),
                            "change_pct": _safe_float(_raw(c.get("percentChange", {}))),
                            "iv": _safe_float(_raw(c.get("impliedVolatility", {}))),
                            "in_the_money": c.get("inTheMoney", None),
                        }
                        break

    if result:
        cache_set(ck, result, ttl=TTL_QUOTE)
    return result


def option_greeks(contract_code: str) -> dict:
    """期权希腊字母 + 隐含波动率

    获取期权合约的 Greeks 指标和隐含波动率。
    - A股: 通过新浪 CON_OP_GREEKS 接口获取
    - 美股: 通过 Yahoo Finance options chain 计算

    Args:
        contract_code: 期权合约代码
            - A股: 纯数字如 '10007306'
            - 美股: Yahoo 格式如 'AAPL240719C00200000'

    Returns:
        Greeks 字典:
        {delta, gamma, theta, vega, iv, theoretical_price, ...}
    """
    ck = make_key("option_greeks", contract_code)
    cached = cache_get(ck)
    if cached is not None:
        return cached

    result = {}

    # A股期权 → 新浪 CON_OP_GREEKS
    if contract_code.isdigit():
        try:
            from providers.sina import option_greeks as sina_greeks
            result = sina_greeks(contract_code)
        except Exception:
            pass

        # 直接请求作为备用
        if not result:
            try:
                url = f"{_SINA_HQ_API}CON_OP_GREEKS_{contract_code}"
                resp = http_get(url, encoding="gbk", headers=_SINA_HEADERS)
                text = resp.text if hasattr(resp, "text") else str(resp)

                match = re.search(r'"([^"]*)"', text)
                if match:
                    fields = match.group(1).split(",")
                    if len(fields) >= 7:
                        def _f(idx):
                            try:
                                v = fields[idx].strip()
                                return float(v) if v else None
                            except (IndexError, ValueError):
                                return None

                        result = {
                            "contract_code": contract_code,
                            "delta": _f(0),
                            "gamma": _f(1),
                            "theta": _f(2),
                            "vega": _f(3),
                            "iv": _f(4),
                            "theoretical_price": _f(5),
                            "underlying_price": _f(6),
                        }
            except Exception:
                pass
    else:
        # 美股期权 → Yahoo Finance
        match = re.match(r'^([A-Z]+)\d', contract_code)
        if match:
            underlying_symbol = match.group(1)
            chain_data = _yahoo_options_chain(underlying_symbol)
            if chain_data and chain_data.get("options"):
                options = chain_data["options"][0]
                all_contracts = options.get("calls", []) + options.get("puts", [])
                for c in all_contracts:
                    if c.get("contractSymbol") == contract_code:
                        def _raw(v):
                            return v.get("raw") if isinstance(v, dict) else v

                        # Yahoo 直接提供 IV，Greeks 需计算或从扩展数据获取
                        iv = _safe_float(_raw(c.get("impliedVolatility", {})))
                        result = {
                            "contract_code": contract_code,
                            "iv": iv,
                            "delta": None,  # Yahoo 基础接口不直接提供
                            "gamma": None,
                            "theta": None,
                            "vega": None,
                            "strike": _safe_float(_raw(c.get("strike", {}))),
                            "last_price": _safe_float(_raw(c.get("lastPrice", {}))),
                            "underlying_price": None,
                        }

                        # 尝试使用 Black-Scholes 近似计算 Greeks
                        if iv and iv > 0:
                            strike = _safe_float(_raw(c.get("strike", {})))
                            # 获取标的当前价格
                            try:
                                from providers.yahoo import quote_summary
                                summary = quote_summary(underlying_symbol, modules=["price"])
                                price_data = summary.get("price", {})
                                underlying_price = _safe_float(
                                    price_data.get("regularMarketPrice", {}).get("raw")
                                    if isinstance(price_data.get("regularMarketPrice"), dict)
                                    else price_data.get("regularMarketPrice")
                                )
                                result["underlying_price"] = underlying_price

                                # 简化 Greeks 近似（仅作参考，精确值需完整BSM模型）
                                if underlying_price and strike:
                                    import math
                                    S = underlying_price
                                    K = strike
                                    T = 30 / 365.0  # 默认假设30天到期
                                    sigma = iv
                                    r = 0.05  # 无风险利率近似

                                    d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T)) if T > 0 and sigma > 0 else 0
                                    # 标准正态分布 CDF 近似
                                    nd1 = 0.5 * (1 + math.erf(d1 / math.sqrt(2)))

                                    is_call = "C" in contract_code.upper()
                                    result["delta"] = round(nd1 if is_call else nd1 - 1, 4)
                            except Exception:
                                pass
                        break

    if result:
        cache_set(ck, result, ttl=TTL_QUOTE)
    return result
