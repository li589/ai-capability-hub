# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 实时行情
==========================================

多市场统一行情接口，自动识别证券市场并选择最优数据源。
支持 A股/港股/美股，内置 fallback 降级链。

Fallback 策略:
  - A股: 腾讯 → 新浪 → 通达信
  - 港股: 腾讯 → 新浪
  - 美股: 腾讯 → 新浪
"""

from __future__ import annotations

import os
import sys
import logging
from typing import List, Optional

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.ticker import detect_market, normalize, to_tencent_code, to_sina_code
from providers import tencent, sina, tdx

logger = logging.getLogger(__name__)


def realtime_quote(code: str) -> dict:
    """获取单只证券实时行情，自动识别市场并选择最优数据源。

    根据证券代码自动判断所属市场（A股/港股/美股），依次尝试
    多个数据源直到成功获取数据。

    Args:
        code: 证券代码，支持多种格式:
              - A股: "600519", "sh600519", "600519.SH"
              - 港股: "00700", "0700.HK"
              - 美股: "AAPL", "AAPL.US"

    Returns:
        标准化行情字典，包含:
        {
            code: 证券代码（标准化后）,
            name: 证券名称,
            price: 当前价格,
            change: 涨跌额,
            change_pct: 涨跌幅(%),
            open: 开盘价,
            high: 最高价,
            low: 最低价,
            prev_close: 昨收价,
            volume: 成交量,
            amount: 成交额,
            pe: 市盈率,
            pb: 市净率,
            market_cap: 总市值,
            turnover_rate: 换手率(%),
            market: 市场标识(CN/HK/US),
        }
        获取失败时返回空字典 {}。

    Fallback 链:
        A股: 腾讯 → 新浪 → 通达信(仅A股)
        港股: 腾讯 → 新浪
        美股: 腾讯 → 新浪
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        return _quote_cn(normalized)
    elif market == "HK":
        return _quote_hk(normalized)
    else:
        return _quote_us(normalized)


def batch_quotes(codes: list) -> list[dict]:
    """批量获取行情，A股走腾讯批量接口（逗号拼接），非A股逐个获取。

    对传入的代码列表进行市场分类：
    - A股代码统一走腾讯批量接口（一次请求获取全部）
    - 港股/美股逐个调用 realtime_quote

    Args:
        codes: 证券代码列表，如 ["600519", "000858", "00700", "AAPL"]

    Returns:
        行情字典列表，每个元素格式同 realtime_quote 返回值。
        获取失败的代码不会出现在结果中。

    示例:
        >>> results = batch_quotes(["600519", "000858", "AAPL"])
        >>> len(results)
        3
    """
    if not codes:
        return []

    # 分类：A股 vs 非A股
    cn_codes = []
    other_codes = []

    for code in codes:
        try:
            market = detect_market(code)
            if market == "CN":
                cn_codes.append(code)
            else:
                other_codes.append(code)
        except ValueError:
            logger.warning(f"无法识别的代码，跳过: {code}")
            continue

    results = []

    # A股批量获取（腾讯接口支持逗号拼接）
    if cn_codes:
        cn_results = _batch_cn_quotes(cn_codes)
        results.extend(cn_results)

    # 非A股逐个获取
    for code in other_codes:
        quote = realtime_quote(code)
        if quote:
            results.append(quote)

    return results


# ---------------------------------------------------------------------------
# A股行情 fallback 链
# ---------------------------------------------------------------------------


def _quote_cn(code: str) -> dict:
    """A股行情 fallback: 腾讯 → 新浪 → 通达信"""

    # 第一优先: 腾讯
    try:
        tencent_code = to_tencent_code(code)
        result = tencent.quote([tencent_code])
        if result and len(result) > 0:
            data = result[0]
            data["market"] = "CN"
            data["source"] = "tencent"
            return data
    except Exception as e:
        logger.debug(f"腾讯行情获取失败({code}): {e}")

    # 第二优先: 新浪（A股格式与腾讯相同: sh/sz + code）
    try:
        sina_code = to_sina_code(code)
        # 新浪 hq 接口返回格式不同，使用 hk_quote 风格解析
        # 但A股直接走腾讯兼容格式（新浪A股行情格式解析）
        from core.client import http_get
        url = f"http://hq.sinajs.cn/list={sina_code}"
        resp = http_get(url, encoding="gbk")
        text = resp.text if hasattr(resp, 'text') else str(resp)
        data = _parse_sina_cn_quote(text, code)
        if data:
            data["market"] = "CN"
            data["source"] = "sina"
            return data
    except Exception as e:
        logger.debug(f"新浪行情获取失败({code}): {e}")

    # 第三优先: 通达信（仅A股可用）
    try:
        data = tdx.realtime(code)
        if data:
            normalized = _normalize_tdx_quote(data, code)
            normalized["market"] = "CN"
            normalized["source"] = "tdx"
            return normalized
    except Exception as e:
        logger.debug(f"通达信行情获取失败({code}): {e}")

    logger.warning(f"所有数据源均获取失败: {code}")
    return {}


def _quote_hk(code: str) -> dict:
    """港股行情 fallback: 腾讯 → 新浪"""

    # 第一优先: 腾讯
    try:
        tencent_code = to_tencent_code(code)
        result = tencent.quote([tencent_code])
        if result and len(result) > 0:
            data = result[0]
            data["market"] = "HK"
            data["source"] = "tencent"
            return data
    except Exception as e:
        logger.debug(f"腾讯港股行情获取失败({code}): {e}")

    # 第二优先: 新浪
    try:
        data = sina.hk_quote(code)
        if data and data.get("price") is not None:
            data["market"] = "HK"
            data["source"] = "sina"
            return data
    except Exception as e:
        logger.debug(f"新浪港股行情获取失败({code}): {e}")

    logger.warning(f"港股所有数据源均获取失败: {code}")
    return {}


def _quote_us(code: str) -> dict:
    """美股行情 fallback: 腾讯 → 新浪"""

    # 第一优先: 腾讯
    try:
        tencent_code = to_tencent_code(code)
        result = tencent.quote([tencent_code])
        if result and len(result) > 0:
            data = result[0]
            data["market"] = "US"
            data["source"] = "tencent"
            return data
    except Exception as e:
        logger.debug(f"腾讯美股行情获取失败({code}): {e}")

    # 第二优先: 新浪
    try:
        data = sina.us_quote(code)
        if data and data.get("price") is not None:
            data["market"] = "US"
            data["source"] = "sina"
            return data
    except Exception as e:
        logger.debug(f"新浪美股行情获取失败({code}): {e}")

    logger.warning(f"美股所有数据源均获取失败: {code}")
    return {}


# ---------------------------------------------------------------------------
# A股批量获取
# ---------------------------------------------------------------------------


def _batch_cn_quotes(codes: list) -> list[dict]:
    """A股批量获取，走腾讯批量接口，失败则逐个 fallback。"""

    # 构建腾讯格式代码列表
    tencent_codes = []
    for code in codes:
        try:
            tencent_codes.append(to_tencent_code(code))
        except Exception:
            tencent_codes.append(code)

    # 尝试腾讯批量接口
    try:
        results = tencent.quote(tencent_codes)
        if results:
            for item in results:
                item["market"] = "CN"
                item["source"] = "tencent"
            return results
    except Exception as e:
        logger.debug(f"腾讯批量行情获取失败: {e}")

    # 降级: 逐个获取
    results = []
    for code in codes:
        normalized = normalize(code)
        quote = _quote_cn(normalized)
        if quote:
            results.append(quote)

    return results


# ---------------------------------------------------------------------------
# 辅助解析函数
# ---------------------------------------------------------------------------


def _parse_sina_cn_quote(text: str, code: str) -> Optional[dict]:
    """解析新浪A股实时行情文本。

    新浪A股行情格式（以逗号分隔的字符串）:
    var hq_str_sh600519="贵州茅台,开盘价,昨收,当前价,最高,最低,买一,卖一,
    成交量(股),成交额(元),...,日期,时间,...";

    字段索引:
    0=名称, 1=开盘, 2=昨收, 3=当前价, 4=最高, 5=最低,
    6=买入价, 7=卖出价, 8=成交量(股), 9=成交额(元),
    30=日期, 31=时间
    """
    import re

    match = re.search(r'"([^"]*)"', text)
    if not match:
        return None

    raw = match.group(1)
    if not raw or raw.strip() == "":
        return None

    fields = raw.split(",")
    if len(fields) < 32:
        return None

    def _float(idx: int) -> Optional[float]:
        try:
            val = fields[idx].strip()
            return float(val) if val else None
        except (IndexError, ValueError):
            return None

    price = _float(3)
    prev_close = _float(2)
    change = None
    change_pct = None

    if price is not None and prev_close is not None and prev_close != 0:
        change = round(price - prev_close, 4)
        change_pct = round(change / prev_close * 100, 2)

    volume_raw = _float(8)
    amount_raw = _float(9)

    return {
        "code": code,
        "name": fields[0].strip(),
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "open": _float(1),
        "high": _float(4),
        "low": _float(5),
        "prev_close": prev_close,
        "volume": int(volume_raw / 100) if volume_raw else None,  # 股→手
        "amount": round(amount_raw / 10000, 2) if amount_raw else None,  # 元→万元
        "pe": None,  # 新浪行情不含 PE
        "pb": None,
        "market_cap": None,
        "turnover_rate": None,
    }


def _normalize_tdx_quote(data: dict, code: str) -> dict:
    """将通达信 realtime 返回格式标准化为统一结构。

    通达信 quotes 返回的 DataFrame 转 dict 后字段名不统一，
    此函数做字段映射和数值规范化。
    """
    price = data.get("price", data.get("last_price"))
    prev_close = data.get("pre_close", data.get("last_close"))
    change = None
    change_pct = None

    if price and prev_close and prev_close != 0:
        change = round(price - prev_close, 4)
        change_pct = round(change / prev_close * 100, 2)

    return {
        "code": code,
        "name": data.get("name", ""),
        "price": price,
        "change": change,
        "change_pct": change_pct,
        "open": data.get("open"),
        "high": data.get("high"),
        "low": data.get("low"),
        "prev_close": prev_close,
        "volume": data.get("vol", data.get("volume")),
        "amount": data.get("amount"),
        "pe": None,
        "pb": None,
        "market_cap": None,
        "turnover_rate": None,
    }
