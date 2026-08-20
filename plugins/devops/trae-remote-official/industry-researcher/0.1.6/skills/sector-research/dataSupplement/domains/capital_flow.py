# -*- coding: utf-8 -*-
"""
dataSupplement V7.1 · 领域模块 · 资金面数据
============================================

提供个股资金流向、融资融券、大宗交易、股东户数、分红送转等
资金面维度数据的统一查询接口。

数据源分配:
  - 资金流向: akshare(首选) → 东财push2his(备用) → 新浪(已废弃)  [A股]  /  东财 push2his [美港股]
  - 融资融券: 东财 datacenter RPTA_WEB_RZRQ_GGMX  [仅A股]
  - 大宗交易: 东财 datacenter RPT_BLOCKTRADE_DETAILS  [仅A股]
  - 股东户数: 东财 datacenter RPT_HOLDERNUMLATEST  [仅A股]
  - 分红送转: 东财 datacenter RPT_SHAREBONUS_DET  [仅A股]
"""

from __future__ import annotations

import os
import sys
import logging
from typing import List, Optional

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SKILL_ROOT not in sys.path:
    sys.path.insert(0, _SKILL_ROOT)

from core.ticker import detect_market, normalize, to_eastmoney_secid
from providers import akshare_bridge, sina, eastmoney

logger = logging.getLogger(__name__)


def fund_flow(code: str, days: int = 5) -> list[dict]:
    """获取个股资金流向（主力/大单/中单/小单净流入）。

    按日统计各类资金的净流入净流出情况，帮助判断主力动向。

    数据源:
        A股: akshare(首选) → 东财push2his(备用) → 新浪(已废弃)
        美港股: 东财 push2his

    Args:
        code: 证券代码，如 "600519", "AAPL", "00700"
        days: 获取天数，默认 5 天

    Returns:
        资金流向列表，每天一条记录:
        [
            {
                date: 日期,
                main_net_inflow: 主力净流入（万元）,
                big_net_inflow: 大单净流入（万元）,
                mid_net_inflow: 中单净流入（万元）,
                small_net_inflow: 小单净流入（万元）,
                main_net_pct: 主力净流入占比(%),
                close_price: 收盘价（如有）,
                change_pct: 涨跌幅(%)(如有）,
            },
            ...
        ]
        获取失败返回空列表 []。
    """
    market = detect_market(code)
    normalized = normalize(code)

    if market == "CN":
        return _fund_flow_cn(normalized, days)
    else:
        return _fund_flow_foreign(normalized, market, days)


def margin_data(code: str) -> list[dict]:
    """获取融资融券明细数据（日级）。

    仅支持 A 股，返回个股每日融资融券余额及变化。

    数据源: 东财 datacenter RPTA_WEB_RZRQ_GGMX

    Args:
        code: A股证券代码，如 "600519"

    Returns:
        融资融券明细列表:
        [
            {
                date: 日期,
                rzye: 融资余额（元）,
                rzmre: 融资买入额（元）,
                rzche: 融资偿还额（元）,
                rqye: 融券余额（元）,
                rqmcl: 融券卖出量（股）,
                rqchl: 融券偿还量（股）,
                rzrqye: 融资融券余额（元）,
            },
            ...
        ]
        非A股或获取失败返回空列表 []。

    Raises:
        仅记录日志，不抛出异常。
    """
    market = detect_market(code)
    if market != "CN":
        logger.warning(f"融资融券数据仅支持A股，当前市场: {market}")
        return []

    normalized = normalize(code)

    try:
        raw = eastmoney.margin_detail(normalized)
        if raw:
            return _normalize_margin(raw)
    except Exception as e:
        logger.debug(f"东财融资融券获取失败({normalized}): {e}")

    logger.warning(f"融资融券数据获取失败: {normalized}")
    return []


def block_trade(code: str) -> list[dict]:
    """获取大宗交易明细（含溢价率+营业部信息）。

    仅支持 A 股，返回近期大宗交易记录。

    数据源: 东财 datacenter RPT_BLOCKTRADE_DETAILS

    Args:
        code: A股证券代码，如 "600519"

    Returns:
        大宗交易列表:
        [
            {
                date: 交易日期,
                price: 成交价（元）,
                volume: 成交量（万股）,
                amount: 成交额（万元）,
                premium_rate: 溢价率(%),
                buyer: 买方营业部,
                seller: 卖方营业部,
            },
            ...
        ]
        非A股或获取失败返回空列表 []。
    """
    market = detect_market(code)
    if market != "CN":
        logger.warning(f"大宗交易数据仅支持A股，当前市场: {market}")
        return []

    normalized = normalize(code)

    try:
        raw = eastmoney.block_trades(normalized)
        if raw:
            return _normalize_block_trade(raw)
    except Exception as e:
        logger.debug(f"东财大宗交易获取失败({normalized}): {e}")

    logger.warning(f"大宗交易数据获取失败: {normalized}")
    return []


def holder_count(code: str) -> list[dict]:
    """获取股东户数变化（季度级）。

    仅支持 A 股，反映筹码集中度变化趋势。

    数据源: 东财 datacenter RPT_HOLDERNUMLATEST

    Args:
        code: A股证券代码，如 "600519"

    Returns:
        股东户数列表（按报告期倒序）:
        [
            {
                end_date: 统计截止日期,
                holder_num: 股东总户数,
                holder_num_change: 较上期变动,
                holder_num_change_pct: 变动幅度(%),
                avg_hold_amount: 户均持股金额（元）,
                avg_hold_shares: 户均持股数量（股）,
            },
            ...
        ]
        非A股或获取失败返回空列表 []。
    """
    market = detect_market(code)
    if market != "CN":
        logger.warning(f"股东户数数据仅支持A股，当前市场: {market}")
        return []

    normalized = normalize(code)

    try:
        raw = eastmoney.holder_count(normalized)
        if raw:
            return _normalize_holder_count(raw)
    except Exception as e:
        logger.debug(f"东财股东户数获取失败({normalized}): {e}")

    logger.warning(f"股东户数数据获取失败: {normalized}")
    return []


def dividend_records(code: str) -> list[dict]:
    """获取分红送转历史记录。

    仅支持 A 股，返回历次分红/送股/转增方案。

    数据源: 东财 datacenter RPT_SHAREBONUS_DET

    Args:
        code: A股证券代码，如 "600519"

    Returns:
        分红记录列表（按除权日倒序）:
        [
            {
                report_date: 报告期,
                ex_date: 除权除息日,
                record_date: 股权登记日,
                plan: 分配方案描述,
                cash_dividend: 每股现金红利（元）,
                bonus_shares: 每股送股数,
                convert_shares: 每股转增数,
                progress: 实施进度,
            },
            ...
        ]
        非A股或获取失败返回空列表 []。
    """
    market = detect_market(code)
    if market != "CN":
        logger.warning(f"分红送转数据仅支持A股，当前市场: {market}")
        return []

    normalized = normalize(code)

    try:
        raw = eastmoney.dividend_history(normalized)
        if raw:
            return _normalize_dividend(raw)
    except Exception as e:
        logger.debug(f"东财分红数据获取失败({normalized}): {e}")

    logger.warning(f"分红送转数据获取失败: {normalized}")
    return []


# ===========================================================================
# 资金流向内部实现
# ===========================================================================


def _fund_flow_cn(code: str, days: int) -> list[dict]:
    """A股资金流向 fallback: akshare → 东财push2his → 新浪(已废弃)"""
    import json

    # 第一优先: akshare
    try:
        raw = akshare_bridge.individual_fund_flow(code)
        if raw:
            return _normalize_akshare_flow(raw, days)
    except Exception as e:
        logger.debug(f"akshare资金流向获取失败({code}): {e}")

    # 第二优先: 东财 push2his（与美港股同接口）
    try:
        from core.client import http_get
        secid = to_eastmoney_secid(code)
        url = (
            f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
            f"?secid={secid}&fields1=f1,f2,f3,f7"
            f"&fields2=f51,f52,f53,f54,f55,f56,f57"
            f"&lmt={days}"
        )
        resp = http_get(url)
        if resp and resp.ok:
            data = resp.json() if hasattr(resp, 'json') else json.loads(resp.text)
            klines = data.get("data", {}).get("klines", [])
            if klines:
                results = []
                for line in klines:
                    parts = line.split(",")
                    if len(parts) < 6:
                        continue
                    results.append({
                        "date": parts[0],
                        "main_net_inflow": _safe_float(parts[1]),
                        "big_net_inflow": _safe_float(parts[2]),
                        "mid_net_inflow": _safe_float(parts[3]),
                        "small_net_inflow": _safe_float(parts[4]),
                        "main_net_pct": _safe_float(parts[5]),
                        "close_price": _safe_float(parts[6]) if len(parts) > 6 else None,
                        "change_pct": None,
                    })
                if results:
                    return results
    except Exception as e:
        logger.debug(f"东财push2his资金流向获取失败({code}): {e}")

    # 第三优先: 新浪（已废弃，保留代码作最后兜底）
    try:
        raw = sina.fund_flow_daily(code=code, days=days)
        if raw:
            return raw
    except Exception as e:
        logger.debug(f"新浪资金流向获取失败({code}): {e}")

    logger.warning(f"A股资金流向所有数据源获取失败: {code}")
    return []


def _fund_flow_foreign(code: str, market: str, days: int) -> list[dict]:
    """美港股资金流向: 东财 push2his 接口。

    通过东财推送历史数据接口获取外资/主力资金流向。
    """
    from core.client import http_get
    import json

    try:
        secid = to_eastmoney_secid(code)
        url = (
            f"https://push2his.eastmoney.com/api/qt/stock/fflow/daykline/get"
            f"?secid={secid}&fields1=f1,f2,f3,f7"
            f"&fields2=f51,f52,f53,f54,f55,f56,f57"
            f"&lmt={days}"
        )
        resp = http_get(url)
        data = resp.json() if hasattr(resp, 'json') else json.loads(resp.text)

        klines = data.get("data", {}).get("klines", [])
        if not klines:
            return []

        results = []
        for line in klines:
            parts = line.split(",")
            if len(parts) < 7:
                continue
            results.append({
                "date": parts[0],
                "main_net_inflow": _safe_float(parts[1]),
                "big_net_inflow": _safe_float(parts[2]),
                "mid_net_inflow": _safe_float(parts[3]),
                "small_net_inflow": _safe_float(parts[4]),
                "main_net_pct": _safe_float(parts[5]),
                "close_price": _safe_float(parts[6]) if len(parts) > 6 else None,
                "change_pct": None,
            })

        return results

    except Exception as e:
        logger.debug(f"东财美港股资金流向获取失败({code}): {e}")
        return []


# ===========================================================================
# 数据标准化函数
# ===========================================================================


def _normalize_akshare_flow(raw: list, days: int) -> list[dict]:
    """标准化 akshare 资金流向数据。

    akshare stock_individual_fund_flow 返回 DataFrame → records 格式，
    字段名为中文，需要映射为英文标准字段。
    """
    # 字段映射（akshare 中文字段 → 标准英文字段）
    field_map = {
        "日期": "date",
        "主力净流入-净额": "main_net_inflow",
        "超大单净流入-净额": "super_big_net_inflow",
        "大单净流入-净额": "big_net_inflow",
        "中单净流入-净额": "mid_net_inflow",
        "小单净流入-净额": "small_net_inflow",
        "主力净流入-净占比": "main_net_pct",
        "收盘价": "close_price",
        "涨跌幅": "change_pct",
    }

    results = []
    for item in raw:
        record = {}
        for cn_key, en_key in field_map.items():
            if cn_key in item:
                val = item[cn_key]
                if en_key == "date":
                    record[en_key] = str(val)
                else:
                    record[en_key] = _safe_float(val)

        # 确保必要字段存在
        if "date" not in record:
            # 尝试其他日期字段
            for k in item:
                if "日期" in str(k) or "date" in str(k).lower():
                    record["date"] = str(item[k])
                    break

        if record.get("date"):
            # 补全缺失字段为 None
            record.setdefault("main_net_inflow", None)
            record.setdefault("super_big_net_inflow", None)
            record.setdefault("big_net_inflow", None)
            record.setdefault("mid_net_inflow", None)
            record.setdefault("small_net_inflow", None)
            record.setdefault("main_net_pct", None)
            record.setdefault("close_price", None)
            record.setdefault("change_pct", None)
            results.append(record)

    # 按日期倒序，取最近 days 条
    results.sort(key=lambda x: x.get("date", ""), reverse=True)
    return results[:days]


def _normalize_margin(raw: list) -> list[dict]:
    """标准化东财融资融券数据。

    东财 datacenter 返回大写字段名，映射为标准结构。
    """
    results = []
    for item in raw:
        record = {
            "date": item.get("DIM_DATE", item.get("TRADE_DATE", "")),
            "rzye": _safe_float(item.get("RZYE")),              # 融资余额
            "rzmre": _safe_float(item.get("RZMRE")),            # 融资买入额
            "rzche": _safe_float(item.get("RZCHE")),            # 融资偿还额
            "rqye": _safe_float(item.get("RQYE")),              # 融券余额
            "rqmcl": _safe_float(item.get("RQMCL")),            # 融券卖出量
            "rqchl": _safe_float(item.get("RQCHL")),            # 融券偿还量
            "rzrqye": _safe_float(item.get("RZRQYE")),          # 融资融券余额
        }
        results.append(record)

    return results


def _normalize_block_trade(raw: list) -> list[dict]:
    """标准化东财大宗交易数据。"""
    results = []
    for item in raw:
        trade_price = _safe_float(item.get("DEAL_PRICE"))
        close_price = _safe_float(item.get("CLOSE_PRICE"))

        # 计算溢价率
        premium_rate = None
        if trade_price and close_price and close_price != 0:
            premium_rate = round((trade_price - close_price) / close_price * 100, 2)

        record = {
            "date": item.get("TRADE_DATE", ""),
            "price": trade_price,
            "volume": _safe_float(item.get("DEAL_VOL")),         # 成交量
            "amount": _safe_float(item.get("DEAL_AMT")),         # 成交额
            "premium_rate": premium_rate or _safe_float(item.get("PREMIUM_RATIO")),
            "buyer": item.get("BUYER_NAME", item.get("BUY_DEPARTMENT", "")),
            "seller": item.get("SELLER_NAME", item.get("SELL_DEPARTMENT", "")),
        }
        results.append(record)

    return results


def _normalize_holder_count(raw: list) -> list[dict]:
    """标准化东财股东户数数据。"""
    results = []
    for item in raw:
        record = {
            "end_date": item.get("END_DATE", item.get("HOLDER_DATE", "")),
            "holder_num": _safe_float(item.get("HOLDER_NUM", item.get("HOLDER_TOTAL_NUM"))),
            "holder_num_change": _safe_float(item.get("HOLDER_NUM_CHANGE")),
            "holder_num_change_pct": _safe_float(item.get("HOLDER_NUM_RATIO")),
            "avg_hold_amount": _safe_float(item.get("AVG_MARKET_CAP")),
            "avg_hold_shares": _safe_float(item.get("AVG_HOLD_NUM")),
        }
        results.append(record)

    return results


def _normalize_dividend(raw: list) -> list[dict]:
    """标准化东财分红送转数据。"""
    results = []
    for item in raw:
        record = {
            "report_date": item.get("REPORT_DATE", item.get("ASSIGN_PROGRESS", "")),
            "ex_date": item.get("EX_DIVIDEND_DATE", ""),
            "record_date": item.get("EQUITY_RECORD_DATE", ""),
            "plan": item.get("ASSIGN_DETAIL", item.get("PLAN_EXPLAIN", "")),
            "cash_dividend": _safe_float(item.get("PRETAX_BONUS_RMB", item.get("BONUS_IT_RATIO"))),
            "bonus_shares": _safe_float(item.get("BONUS_RATIO")),         # 送股比例
            "convert_shares": _safe_float(item.get("CONVERT_RATIO")),     # 转增比例
            "progress": item.get("IMPL_PLAN_PROFILE", item.get("ASSIGN_PROGRESS", "")),
        }
        results.append(record)

    return results


# ===========================================================================
# 辅助函数
# ===========================================================================


def _safe_float(val) -> Optional[float]:
    """安全转换为浮点数，None/无效值/NaN 返回 None。"""
    if val is None:
        return None
    try:
        result = float(str(val).replace(",", "").replace("%", ""))
        return result if result == result else None  # 过滤 NaN
    except (ValueError, TypeError):
        return None
